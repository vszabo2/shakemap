#!/usr/bin/env python

import os.path
import sys
import time
import pytest

from openquake.hazardlib.geo.geodetic import azimuth
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d

from impactutils.rupture.quad_rupture import QuadRupture
from impactutils.rupture.origin import Origin
from impactutils.time.ancient_time import HistoricTime

from shakelib.plotting.plotrupture import plot_rupture_wire3d, map_rupture

homedir = os.path.dirname(os.path.abspath(__file__))  # where is this script?
shakedir = os.path.abspath(os.path.join(homedir, "..", ".."))
sys.path.insert(0, shakedir)

MAX_DEPTH = 70
DIP = 17


def test_plot_rupture(interactive=False):
    xp0 = np.array([-90.898000])
    xp1 = np.array([-91.308000])
    yp0 = np.array([12.584000])
    yp1 = np.array([12.832000])
    zp = [0.0]
    strike = azimuth(yp0[0], xp0[0], yp1[0], xp1[0])
    origin = Origin(
        {
            "lat": 0.0,
            "lon": 0.0,
            "depth": 0.0,
            "mag": 5.5,
            "id": "",
            "netid": "abcd",
            "network": "",
            "locstring": "",
            "time": HistoricTime.utcfromtimestamp(time.time()),
        }
    )
    interface_width = MAX_DEPTH / np.sin(np.radians(DIP))
    widths = np.ones(xp0.shape) * interface_width
    dips = np.ones(xp0.shape) * DIP
    strike = [strike]
    rupture = QuadRupture.fromTrace(
        xp0, yp0, xp1, yp1, zp, widths, dips, origin, strike=strike
    )
    plot_rupture_wire3d(rupture)
    if interactive:
        fname = os.path.join(os.path.expanduser("~"), "rupture_wire_plot.png")
        plt.savefig(fname)
        print(f"Wire 3D plot saved to {fname}.  Delete this file if you wish.")

    # Need to get tests to check exception for if an axis is handed off
    fig = plt.figure()
    # ax = fig.add_subplot(111, projection="3d")
    ax = axes3d.Axes3D(fig)
    plot_rupture_wire3d(rupture, ax)

    # And raise the exception if it is not a 3d axis
    with pytest.raises(TypeError):
        ax = fig.add_subplot(111)
        plot_rupture_wire3d(rupture, ax)


def test_map_rupture(interactive=False):
    xp0 = np.array([-90.898000])
    xp1 = np.array([-91.308000])
    yp0 = np.array([12.584000])
    yp1 = np.array([12.832000])
    zp = [0.0]
    strike = azimuth(yp0[0], xp0[0], yp1[0], xp1[0])
    origin = Origin(
        {
            "lat": 0.0,
            "lon": 0.0,
            "depth": 0.0,
            "mag": 5.5,
            "id": "",
            "netid": "abcd",
            "network": "",
            "locstring": "",
            "time": HistoricTime.utcfromtimestamp(time.time()),
        }
    )
    interface_width = MAX_DEPTH / np.sin(np.radians(DIP))
    widths = np.ones(xp0.shape) * interface_width
    dips = np.ones(xp0.shape) * DIP
    strike = [strike]
    rupture = QuadRupture.fromTrace(
        xp0, yp0, xp1, yp1, zp, widths, dips, origin, strike=strike
    )
    map_rupture(rupture)
    if interactive:
        fname = os.path.join(os.path.expanduser("~"), "rupture_map.png")
        plt.savefig(fname)
        print(f"Rupture map plot saved to {fname}.  Delete this file if you wish.")


if __name__ == "__main__":
    test_plot_rupture(interactive=True)
    test_map_rupture(interactive=True)
