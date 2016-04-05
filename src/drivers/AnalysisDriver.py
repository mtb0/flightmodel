#!/usr/bin/env python
"""Plot scheduled flight times for AA flights between JFK and LAX.
For a given year and month, visualize dist vs sch time, run a regression, 
and look at error.  Filter based on whether the destination is in the Pacific, 
and study the regression and error for each group."""

import os
import sys

from analysis.filter import get_jetstream, get_pacific
from analysis.plot import plot_schtime, plot_regression, plot_error, plot_regression_coef
from analysis.regression import regression

def main():
    year = 2015
    month = 1

    os.system('mkdir -p graphs')  #Create directory to place graphs, if it doesn't exist.

    plot_schtime(12478, 12892, 'AA') #Plot sch flight time from JFK to LAX
    plot_schtime(12892, 12478, 'AA') #Plot sch flight time from LAX to JFK

    flights = get_jetstream(year, month)  #Get flight info.

    #Get info whether destination is in the Pacific and filter.
    df_pac = get_pacific(flights)
    overseas = df_pac[df_pac.DestOverseas]
    not_overseas = df_pac[~df_pac.DestOverseas]

    analysislist = [[flights, 'Regression Error'], 
        [overseas, 'Pacific Regression Error'], 
        [not_overseas, 'US Regression Error']]

    #Plot dist vs sch time, regression, and error for filtered flight data.
    for i, [df, title] in enumerate(analysislist):
        plot_regression(year, month, df)
        print regression(year, month, df)
        plot_error(year, month, df, title)

    plot_regression_coef()    #Plot monthly US and Pacific regression coefficients over time.


if __name__ == '__main__':
    sys.exit(main())