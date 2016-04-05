#!/usr/bin/env python
"""Plotting functions: Scheduled flight times given an airline and origin/dest, over time.
Distance vs Scheduled flight time, indicating eastbound and westbound, regression lines, and error.
Monthly regression coefficients over time."""

import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import pandas as pd
pd.options.mode.chained_assignment = None #Suppress overwrite error.

from analysis.filter import get_jetstream, get_pacific
from analysis.regression import regression


monthdict = {1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 7:'July', 
    8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}


def timetomin(time):
    """Turn hhmm into minutes after midnight."""
    return (60*np.floor(time/100) + time%100)


def date_to_days(df):
    """From a dataframe of strings 'year-mon-day', return days since epoch."""
    epoch = datetime.datetime.utcfromtimestamp(0)
    return map(lambda A: A.days, pd.to_datetime(df) - epoch)


def plot_schtime(origin, destination, carrier):
    """Input: 5 digit AirportID code for origin and destination.  Plot scheduled flight times from 
    origin to destination from Oct 1, 1987 to Dec 31, 2015."""
    dataframes = []
    for year in range(1987, 2016):
        if(year == 1987):
            startmonth = 10
        else:
            startmonth = 1
        for mon in range(startmonth, 13):
            flights = pd.read_csv('../data/%d_%d.csv' %(year, mon))

            #Filter by origin, destination, and carrier.
            isflight = ((np.floor(flights.OriginAirportId/100) == origin) & 
                (np.floor(flights.DestAirportId/100) == destination) & (flights.Carrier == carrier))
            df = flights[isflight][['Date', 'SchDep', 'SchTime']]

            #Determine \# days after Jan. 1, 1988.
            df['Time'] = date_to_days(df.Date)
            df['Time'] += timetomin(df.SchDep)/1440.
            df.drop(['Date', 'SchDep'],axis=1, inplace=True)
            dataframes.append(df)

    flightdist = pd.concat(dataframes, ignore_index=True)
    
    #Determine start and end date in days.
    daystart = date_to_days(['1987-10-01'])[0]
    dayend = date_to_days(['2016-01-01'])[0]
    ticks = date_to_days(['%d-01-01' %year for year in range(1988, 2017)])
    
    #Format, plot, and save graph.
    fig, ax = plt.subplots(figsize=(20,10))
    ax.plot(flightdist.Time, flightdist.SchTime, 'b.')
    ax.set_xlim(daystart, dayend)
    ax.set_xticks(ticks)
    labels = range(1988, 2017)
    ax.set_xticklabels(labels, rotation='vertical', fontsize=20)
    ax.set_title('%d to %d' %(origin, destination), fontsize=20)
    ax.set_xlabel('Date', fontsize=20)
    ax.set_ylabel('Scheduled Flight Time', fontsize=20)
    plt.subplots_adjust(bottom = 0.15)
    fig.savefig('../graphs/%s%d_%d.jpg' %(carrier, origin, destination))


def plot_distschtime(year, month, df):
    """Plot Dist vs SchTime for flights in a given year and month."""
    if(len(df) == 0):
        df = get_jetstream(year, month)  #Get Longitude info to see if west or eastbound.
    westbound = (df.dLong < 0)
    eastbound = (df.dLong > 0)

    #Plot Dist vs SchTime. Color Eastbound flights red and Westbound flights blue.
    fig, ax = plt.subplots()
    ax.plot(df.Distance[eastbound], df.SchTime[eastbound], 'r.', ms = 2)
    ax.plot(df.Distance[westbound], df.SchTime[westbound], 'b.', ms = 2)
    ax.set_title('Flights in %s %d' %(monthdict[month], year))
    ax.set_xlabel('Distance (miles)')
    ax.set_ylabel('Scheduled Flight Time')
    
    #Make legend.
    red_patch = mpatches.Patch(color='red', label='Eastbound')
    blue_patch = mpatches.Patch(color='blue', label='Westbound')
    lines = [red_patch, blue_patch]
    labels = [line.get_label() for line in lines]
    plt.legend(lines, labels, loc='upper left')
    fig.savefig('../graphs/DistvsSchTime_%d_%d.jpg' %(year, month))


def plot_regression(year, month, df):
    """Plot distance vs SchTime for flights in a given year and month, along with the 
    regression lines capturing flights due east and due west."""
    #Get regression coefficients for flights landing in Pacific and other flights.
    if(len(df) == 0):
        df = get_jetstream(year, month)

    params = regression(year, month, df)[0]
    dist = params[0]
    jet = params[1]
    ground = params[2]

    #Get regression line points.
    x = np.linspace(0, 5000, 2)
    y_east = ground + (dist - jet)*x
    y_west = ground + (dist + jet)*x
    
    westbound = (df.dLong < 0)
    eastbound = (df.dLong > 0)

    #Plot Dist vs SchTime. Color Eastbound flights red and Westbound flights blue.
    fig, ax = plt.subplots()
    ax.plot(df.Distance[eastbound], df.SchTime[eastbound], 'r.', ms = 2)
    ax.plot(df.Distance[westbound], df.SchTime[westbound], 'b.', ms = 2)
    ax.plot(x, y_east, 'k')
    ax.plot(x, y_west, 'k')
    ax.set_title('Flights in %s %d' %(monthdict[month], year))
    ax.set_xlabel('Distance (miles)')
    ax.set_ylabel('Scheduled Flight Time')
    
    #Make legend.
    red_patch = mpatches.Patch(color='red', label='Eastbound')
    blue_patch = mpatches.Patch(color='blue', label='Westbound')
    black_line = mlines.Line2D([], [], color='black', label='Regression')
    lines = [red_patch, blue_patch, black_line]
    labels = [line.get_label() for line in lines]
    plt.legend(lines, labels, loc='upper left')
    fig.savefig('../graphs/Regression_%d_%d.jpg' %(year, month))


def plot_error(year, month, df, title):
    """Plot the error from the linear regression in a histogram.  Output flights with error < -25."""
    if(len(df) == 0):
        df = get_jetstream(year, month)
    
    params = regression(year, month, df)[0]

    #Determine Error.
    df['Error'] = df.SchTime - (params[0]*df.Distance + params[1]*df.Jetstream + params[2])

    #Plot the histograms.
    fig, ax = plt.subplots()
    ax.hist(df.Error, 50)
    ax.set_xlabel('Error (min)', fontsize=20)
    ax.set_ylabel('Freq', fontsize=20)
    ax.set_title(('%s %d ' + title) %(monthdict[month], year), fontsize=20)
    fig.savefig('../graphs/%s.jpg' %title)

    #Output flights that have Error < -25.
    latlong = pd.read_csv('LatLong.csv')
    df = df[df.Error < -25]
    errors = pd.DataFrame({'OriginAirportId':df.OriginAirportId, 'DestAirportId':df.DestAirportId})
    errors.drop_duplicates(inplace=True)
    errors.reset_index(drop=True)

    errors = errors.merge(LL, left_on = 'OriginAirportId', right_on='AirportId')
    errors.rename(columns={'AirportName':'OriginAirport'}, inplace=True)
    errors = errors.merge(LL, left_on = 'DestAirportId', right_on='AirportId')
    errors.rename(columns={'AirportName':'DestAirport'}, inplace=True)
    for x in errors.index:
        print "%s --> %s" %(errors.OriginAirport[x], errors.DestAirport[x])


def plot_regression_coef():
    """Plot regression coefficients for Pacific and non-Pacific flights from Oct 1987 to Dec 2015.
    Also, count number of errors > 20 min."""
    [pacplane, pacjet, pacground, pacfit, usplane, usjet, usground, usfit, time] = [[] for i in range(9)]
    [pacflights, usflights, pac_error, us_error] = [0]*4

    for year in range(2011, 2016):
        if(year == 1987):
            startmonth = 10
        else:
            startmonth = 1
        for month in range(startmonth, 13):
            print year, month
            #Get Pacific and non-Pacific flights, and calculate Regression coefficients and fit.
            df = get_jetstream(year, month)
            df = get_pacific(df)
            df_pac = df[df.DestOverseas]
            df_us = df[~df.DestOverseas]
            (pacparams, pacscore, pac_stderr) = regression(year, month, df_pac)
            (usparams, us_score, us_stderr) = regression(year, month, df_us)

            #Put this data into lists.
            pacplane.append(60/pacparams[0])
            pacjet.append(60/pacparams[0] - 60/(pacparams[0] + pacparams[1]))
            pacground.append(pacparams[2])
            pacfit.append(pacscore)

            usplane.append(60/usparams[0])
            usjet.append(60/usparams[0] - 60/(usparams[0] + usparams[1]))
            usground.append(usparams[2])
            usfit.append(us_score)
            time.append(date_to_days(['%d-%d-01'] %(year, month))[0])

            #Calculate and enumerate error.
            df_pac['Error'] = df_pac.SchTime - (pacparams[0]*df_pac.Distance + pacparams[1]*df_pac.Jetstream + pacparams[2])
            df_us['Error'] = df_us.SchTime - (usparams[0]*df_us.Distance + usparams[1]*df_us.Jetstream + usparams[2])
            pacflights += len(df_pac)
            pac_error += len(df_pac[np.abs(df_pac.Error) > 20])
            usflights += len(df_us)
            us_error += len(df_us[np.abs(df_us.Error) > 20])

    print "Pacific Errors: %d out of %d" %(pac_error, pacflights)
    print "Non-Pacific Errors: %d out of %d" %(us_error, usflights)

    coeffs = {'Pacific':[pacplane, pacjet, pacground, pacfit], 'US':[usplane, usjet, usground, usfit]}
    plotdict = {0:('Scheduled Plane Speed', 'mph', 'Plane.jpg'), 
    1:('Jetstream Effect', 'mph', 'Jetstream.jpg'), 
    2:('Ground Time', 'min', 'Ground.jpg'), 
    3:('Correlation Coefficient', 'R^2', 'Fit.jpg')}

    daystart = date_to_days(['1987-10-01'])[0]
    dayend = date_to_days(['2016-01-01'])[0]
    ticks = date_to_days(['%d-01-01' %year for year in range(1988, 2017)])

    #Plot Regression Coefficients
    for region_prefix, region_coeffs in coeffs.viewitems():
        for j, region_coef in enumerate(region_coeffs):
            fig, ax = plt.subplots()
            ax.plot(time, region_coef)
            labels = range(1988, 2017)
            ax.set_xlim(daystart, dayend)
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, rotation='vertical')
            ax.set_xlabel('Year')
            ax.set_title(region_prefix + ' ' + plotdict[j][0])
            ax.set_ylabel(plotdict[j][1])
            plt.subplots_adjust(bottom = 0.15)
            fig.savefig(../graphs/region_prefix+plotdict[j][2])
