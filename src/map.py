#!/usr/bin/env python3

import gmplot

def plot_map(lat_list,lon_list,a_lat_list,a_lon_list):
    gmap3 = gmplot.GoogleMapPlotter(lat_list[0], lon_list[0], 50)
    gmap3.scatter(lat_list, lon_list, '#FF0000', size = 0.1, marker = False)
    gmap3.scatter(a_lat_list, a_lon_list, '#008000', size = 0.1, marker = False)
    gmap3.plot(a_lat_list, a_lon_list, 'yellow', edge_width = 2.5)
    gmap3.plot(lat_list, lon_list, 'cornflowerblue', edge_width = 2.5)
    gmap3.draw("map.html")