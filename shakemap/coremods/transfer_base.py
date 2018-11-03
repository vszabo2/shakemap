# stdlib imports
import argparse
import inspect
import os.path
from datetime import datetime
import sys
import logging

# third party imports
from impactutils.io.smcontainers import ShakeMapOutputContainer
from configobj import ConfigObj
from validate import Validator

# local imports
from .base import CoreModule
from shakemap.utils.config import (get_config_paths,
                                   get_data_path,
                                   config_error)
from shakelib.rupture import constants

NO_TRANSFER = 'NO_TRANSFER'


class TransferBaseModule(CoreModule):
    def __init__(self, eventid, cancel=False):
        """
        Instantiate a CoreModule class with an event ID.
        """
        self._eventid = eventid

    def execute(self):
        install_path, data_path = get_config_paths()
        self.datadir = os.path.join(data_path, self._eventid, 'current')
        if not os.path.isdir(self.datadir):
            raise NotADirectoryError(
                '%s is not a valid directory.' % self.datadir)

        # look for the presence of a NO_TRANSFER file in the datadir.
        notransfer = os.path.join(self.datadir, NO_TRANSFER)
        if os.path.isfile(notransfer):
            self.logger.info(
                'Event has a %s file blocking transfer.' % NO_TRANSFER)
            return

        # get the path to the transfer.conf spec file
        configspec = os.path.join(get_data_path(), 'transferspec.conf')

        # look for an event specific transfer.conf file
        transfer_conf = os.path.join(self.datadir, 'transfer.conf')
        if not os.path.isfile(transfer_conf):
            # if not there, use the system one
            transfer_conf = os.path.join(
                install_path, 'config', 'transfer.conf')
            if not os.path.isfile(transfer_conf):
                raise FileNotFoundError('%s does not exist.' % transfer_conf)

        # get the config information for transfer
        self.config = ConfigObj(transfer_conf, configspec=configspec)
        results = self.config.validate(Validator())
        if not isinstance(results, bool) or not results:
            config_error(self.config, results)

        # get the output container with all the things in it
        products_dir = os.path.join(self.datadir, 'products')
        datafile = os.path.join(products_dir, 'shake_result.hdf')
        if not os.path.isfile(datafile):
            raise FileNotFoundError('%s does not exist.' % datafile)

        # Open the ShakeMapOutputContainer and extract the data
        container = ShakeMapOutputContainer.load(datafile)
        # extract the info.json object from the container
        self.info = container.getMetadata()
        container.close()

    def getProperties(self, info):
        properties = {}
        product_properties = {}
        # origin info
        origin = info['input']['event_information']
        properties['eventsource'] = origin['netid']
        # The netid could be a valid part of the eventsourcecode, so we have to
        # check here if it ***starts with*** the netid
        # This fix should already be done by the time we get here, but this
        # is just an insurance check
        if origin['eventsourcecode'].startswith(origin['netid']):
            eventsourcecode = origin['eventsourcecode'].replace(origin['netid'],
                                                                '', 1)
        else:
            eventsourcecode = origin['eventsourcecode']
        properties['eventsourcecode'] = eventsourcecode
        properties['code'] = origin['productcode']
        properties['source'] = origin['productsource']
        properties['type'] = origin['producttype']

        properties['magnitude'] = float(origin['magnitude'])
        properties['latitude'] = float(origin['latitude'])
        properties['longitude'] = float(origin['longitude'])
        properties['depth'] = float(origin['depth'])
        try:
            properties['eventtime'] = datetime.strptime(origin['origin_time'],
                                                        constants.TIMEFMT)
        except ValueError:
            properties['eventtime'] = datetime.strptime(origin['origin_time'],
                                                        constants.ALT_TIMEFMT)

        product_properties['event-type'] = origin['event_type']
        product_properties['event-description'] = origin['event_description']

        # other metadata
        if 'MMI' in info['output']['ground_motions']:
            mmi_info = info['output']['ground_motions']['MMI']
            product_properties['maxmmi'] = mmi_info['max']
            product_properties['maxmmi-grid'] = mmi_info['max_grid']

        if 'PGV' in info['output']['ground_motions']:
            pgv_info = info['output']['ground_motions']['PGV']
            product_properties['maxpgv'] = pgv_info['max']
            product_properties['maxpgv-grid'] = pgv_info['max_grid']

        if 'PGA' in info['output']['ground_motions']:
            pga_info = info['output']['ground_motions']['PGA']
            product_properties['maxpga'] = pga_info['max']
            product_properties['maxpga-grid'] = pga_info['max_grid']

        if 'SA(0.3)' in info['output']['ground_motions']:
            psa03_info = info['output']['ground_motions']['SA(0.3)']
            product_properties['maxpsa03'] = psa03_info['max']
            product_properties['maxpsa03-grid'] = psa03_info['max_grid']

        if 'SA(1.0)' in info['output']['ground_motions']:
            psa10_info = info['output']['ground_motions']['SA(1.0)']
            product_properties['maxpsa10'] = psa10_info['max']
            product_properties['maxpsa10-grid'] = psa10_info['max_grid']

        if 'SA(3.0)' in info['output']['ground_motions']:
            psa30_info = info['output']['ground_motions']['SA(3.0)']
            product_properties['maxpsa30'] = psa30_info['max']
            product_properties['maxpsa30-grid'] = psa30_info['max_grid']

        product_properties['minimum-longitude'] = \
            info['output']['map_information']['min']['longitude']
        product_properties['minimum-latitude'] = \
            info['output']['map_information']['min']['latitude']
        product_properties['maximum-longitude'] = \
            info['output']['map_information']['max']['longitude']
        product_properties['maximum-latitude'] = \
            info['output']['map_information']['max']['latitude']

        product_properties['process-timestamp'] = \
            info['processing']['shakemap_versions']['process_time']
        product_properties['version'] = \
            info['processing']['shakemap_versions']['map_version']
        product_properties['map-status'] = \
            info['processing']['shakemap_versions']['map_status']

        # if this process is being run manually, set the review-status property
        # to "reviewed". If automatic, then set to "automatic".
        product_properties['review-status'] = 'automatic'
        if sys.stdout is not None and sys.stdout.isatty():
            product_properties['review-status'] = 'reviewed'

        # what gmice was used for the model calculations
        gmice = info['processing']['ground_motion_modules']['gmice']['module']
        product_properties['gmice'] = gmice

        return (properties, product_properties)

    def parseArgs(self, arglist):
        """
        Set up the object to accept the --comment flag.
        """
        parser = argparse.ArgumentParser(
            prog=self.__class__.command_name,
            description=inspect.getdoc(self.__class__))
        helpstr = 'Cancel this event.'
        parser.add_argument('-c', '--cancel', help=helpstr,
                            action='store_true', default=False)
        #
        # This line should be in any modules that overrides this
        # one. It will collect up everything after the current
        # modules options in args.rem, which should be returned
        # by this function. Note: doing parser.parse_known_args()
        # will not work as it will suck up any later modules'
        # options that are the same as this one's.
        #
        parser.add_argument('rem', nargs=argparse.REMAINDER,
                            help=argparse.SUPPRESS)
        args = parser.parse_args(arglist)
        self.cancel = args.cancel
        return args.rem
