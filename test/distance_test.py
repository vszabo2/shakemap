#!/usr/bin/env python

#stdlib imports
import os.path
import sys
from collections import OrderedDict

#third party
import numpy as np

#hack the path so that I can debug these functions if I need to
homedir = os.path.dirname(os.path.abspath(__file__)) #where is this script?
shakedir = os.path.abspath(os.path.join(homedir,'..'))
sys.path.insert(0,shakedir) #put this at the front of the system path, ignoring any installed mapio stuff

from shakemap.grind.distance import *
from shakemap.grind.vector import Vector
from shakemap.grind.fault import Fault

from openquake.hazardlib.geo.geodetic import npoints_towards
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.utils import get_orthographic_projection

def test_rx():
    print('Testing low level calc_rx() method...')
    #this is the coordinate of a station used in Northridge
    slat = 34.0700
    slon = -118.1500
    sdep = 0.0

    #this is the starting point of the top edge of rupture for the Northridge fault
    p0lon = -118.598000
    p0lat = 34.387000

    #this is the ending point of the top edge of rupture for the Northridge fault
    p1lon = -118.431819
    p1lat = 34.301105

    west = min(p0lon,p1lon)
    east = max(p0lon,p1lon)
    south = min(p0lat,p1lat)
    north = max(p0lat,p1lat)
    proj = get_orthographic_projection(west,east,north,south) #projected coordinates are in km
    p0x,p0y = proj(p0lon,p0lat)
    p1x,p1y = proj(p1lon,p1lat)
    P0 = Vector(p0x*1000,p0y*1000,0.0)
    P1 = Vector(p1x*1000,p1y*1000,0.0)

    sx,sy = proj(slon,slat)
    station = np.array([sx*1000,sy*1000,0.0]).reshape(1,3)
    rx = calc_rx_distance(P0,P1,station)[0][0]

    output = 7.98
    np.testing.assert_almost_equal(rx,output,decimal=1)
    print('Passed low level calc_rx() method...')

    print('Testing high level get_distance() method with Rx...')
    mesh = Mesh(np.array([slon]),np.array([slat]),np.array([0.0]))
    quadlist = []
    P0 = Point(p0lon,p0lat,0.0)
    P1 = Point(p1lon,p1lat,0.0)
    P2 = Point(0,0,0) #it doesn't matter for Rx, as it only uses the top edge
    P3 = Point(0,0,0) #it doesn't matter for Rx, as it only uses the top edge
    quad = (P0,P1,P2,P3)
    quadlist.append(quad)
    rxd = get_distance('rx',mesh,quadlist=quadlist)[0]
    np.testing.assert_almost_equal(rxd,output,decimal=1)
    print('Passed high level get_distance() method with Rx...')

def test_dist():
    #TODO - revisit the way we're constructing the fault object - 
    #it appears there may be something wrong with that...
    L = 24.0 # length, km
    W = 18.0 # width, km
    strike = 122.0
    dip = 40.0
    lat_ulc = 34.387    # latitude of upper left corner
    lon_ulc = -118.598
    depth_ulc = 5.0
    P0 = Vector.fromPoint(Point(lon_ulc,lat_ulc,depth_ulc))
    p1lon,p1lat,p1dep = npoints_towards(lon_ulc,lat_ulc,depth_ulc,strike,L,0,2)
    P1 = Vector.fromPoint(Point(p1lon[1],p1lat[1],p1dep[1]))

    station_lat = 34.0160
    station_lon = -119.3620
    station_depth = 0

    hypolat = 34.2057
    hypolon = -118.5539
    hypodep = 17.5

    mypoint = Point(hypolon,hypolat,hypodep)

    outputs = OrderedDict([('repi',77.39),
                           ('rhypo',79.34),
                           ('rrup',36.77),
                           ('rjb',65.84),
                           ('rx',72.11),
                           ('ry0',-47.055479)])

    xp0 = np.array([lon_ulc])
    yp0 = np.array([lat_ulc])
    zp = np.array([depth_ulc])
    xp1 = np.array([p1lon[1]])
    yp1 = np.array([p1lat[1]])
    fault = Fault.fromTrace(xp0,yp0,xp1,yp1,zp,np.array([W]),np.array([dip]))
    
    quads = fault.getQuadrilaterals()
    mesh = Mesh(np.array([station_lon]),np.array([station_lat]),np.array([station_depth]))

    for method in outputs.keys():
        d = get_distance(method,mesh,quadlist=quads,mypoint=mypoint)
        print('Method %s: %.2f output, %.2f groundtruth' % (method,d,outputs[method]))
    

if __name__ == '__main__':
    test_rx()
    sys.exit(0)
    test_dist()
    sys.exit(0)
    
    flat = [28.427,27.986,27.469,27.956]
    flon = [84.614,86.179,85.880,84.461]
    fdep = [20.0,20.0,13.0,13.0]
    lat0,lat1,lat2,lat3 = flat
    lon0,lon1,lon2,lon3 = flon
    dep0,dep1,dep2,dep3 = fdep
    
    P0 = Vector.fromPoint(point.Point(lon0,lat0,dep0))
    P1 = Vector.fromPoint(point.Point(lon1,lat1,dep1))
    P2 = Vector.fromPoint(point.Point(lon2,lat2,dep2))
    P3 = Vector.fromPoint(point.Point(lon3,lat3,dep3))

    lons = np.arange(81.5,87.5,0.0083)
    lats = np.arange(25.5,31.0,0.0083)
    lonmat,latmat = np.meshgrid(lons,lats)
    depmat = np.zeros_like(lonmat)

    x,y,z = latlon2ecef(lonmat,latmat,depmat)
    nr,nc = x.shape
    x.shape = (nr*nc,1)
    y.shape = (nr*nc,1)
    z.shape = (nr*nc,1)
    points = np.hstack((x,y,z))
    t1 = datetime.now()
    dist = calcRuptureDistance(P0,P1,P2,P3,points)
    t2 = datetime.now()
    dt = t2-t1
    sec = dt.seconds + float(dt.microseconds)/1e6
    npoints = nr*nc
    print('RRupt: %.4f seconds for %i point grid' % (sec,npoints))
    dist.shape = (nr,nc)
    if nr > 1 and nc > 1:
        plt.imshow(dist,interpolation='nearest')
        plt.colorbar()
        plt.savefig('dist.png')
    else:
        print(dist)

    #test this against Bruce's C program
    nr2,nc2 = points.shape
    f = open('points.bin','wb')
    for i in range(0,nr2):
        xt,yt,zt = points[i,:]
        xb = struct.pack('d',xt)
        yb = struct.pack('d',yt)
        zb = struct.pack('d',zt)
        f.write(xb)
        f.write(yb)
        f.write(zb)
    f.close()

    #now write out the quads
    f = open('fault.txt','wt')
    f.write('5\n')
    f.write('%.11f %.11f %.11f\n' % tuple(P0.getArray()))
    f.write('%.11f %.11f %.11f\n' % tuple(P1.getArray()))
    f.write('%.11f %.11f %.11f\n' % tuple(P2.getArray()))
    f.write('%.11f %.11f %.11f\n' % tuple(P3.getArray()))
    f.write('%.11f %.11f %.11f\n' % tuple(P0.getArray()))
    f.close()

    cmd = '/Users/mhearne/src/python/ShakeMap/src/contour/dist_rrupt fault.txt < points.bin > outpoints.bin'
    res,stdout,stderr = getCommandOutput(cmd)
    f = open('outpoints.bin','rb')
    dlist = []
    buf = f.read(8)
    while buf:
        d = struct.unpack('d',buf)
        dlist.append(d[0])
        buf = f.read(8)
    f.close()
    d2 = np.array(dlist)
    d2.shape = (nr,nc)
    if nr > 1 and nc > 1:
        plt.close()
        plt.imshow(d2,interpolation='nearest')
        plt.colorbar()
        plt.savefig('dist_c.png')
    else:
        print(dist)
    
    P0,P1 = getTopEdge(flat,flon,fdep)
    rxdist = calcRxDistance(P0,P1,points)
    rxdist.shape = (nr,nc)
    if nr > 1 and nc > 1:
        plt.close()
        plt.imshow(rxdist,interpolation='nearest')
        plt.colorbar()
        plt.savefig('distrx.png')
    else:
        print(rxdist)

    #test against Bruce's C implementation
    f = open('points.txt','wt')
    for i in range(0,nr2):
        xt,yt = (points[i,0],points[i,1])
        f.write('%.11f %.11f\n' %(xt,yt))
    f.close()
    cmd = '/Users/mhearne/src/python/ShakeMap/src/contour/dist_rx %.11f %.11f %.11f %.11f < points.txt > outpoints.txt' % (P0.x,P0.y,P1.x,P1.y)
    res,stdout,stderr = getCommandOutput(cmd)
    rxdist2 = []
    for line in open('outpoints.txt','rt').readlines():
        rxdist2.append(float(line.strip()))
    rxdist2 = np.array(rxdist2)
    rxdist2.shape = (nr,nc)
    if nr > 1 and nc > 1:
        plt.close()
        plt.imshow(rxdist2,interpolation='nearest')
        plt.colorbar()
        plt.savefig('distrx_c.png')
    else:
        print(rxdist2)
