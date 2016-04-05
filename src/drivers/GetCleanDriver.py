#!/usr/bin/env python
"""Download and clean data from Bureau of Transportation Statistics.  Place files 
in the data folder."""

import sys

from download.get_files import get_latlong, get_flights
from download.get_dist_from_files import getdistance
from clean.cleandata import fix_schdata, adjust_schtime

def main():
    get_latlong()  #Get LatLong.csv

    for year in range(1987,2016):
        if(year == 1987):
            startmonth=10
        else:
            startmonth=1
        for month in range(startmonth, 13):
            get_flights(year, month)  #Get flight data as year_month.csv

    getdistance()  #Get distance.csv

    for year in range(1987, 2016):
        if(year == 1987):
            startmonth = 10
        else:
            startmonth = 1
        for month in range(startmonth, 13):
            #Fix SchDep, SchArr, SchTime so that data is consistent.
            newflightdata = fix_schdata(year, month)

            finalflightdata = adjust_schtime(newflightdata)  #Adjust SchTime that are outliers.
            finalflightdata.to_csv('../data/%d_%d.csv' %(year, month), index=False)

if __name__ == '__main__':
    sys.exit(main())