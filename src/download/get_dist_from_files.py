#!/usr/bin/env python
"""From flight data, gather info about distance between airports and check for consistency.  Then 
write to distance.csv"""

from sets import Set
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None #Suppress overwrite error.

def get_distancefreq():
    #Empty dataframe to accumulate frequency, based on Origin, Dest, and Distance.
    freqdf=pd.DataFrame({
        'OriginAirportId':[], 
        'DestAirportId':[], 
        'Distance':[], 
        'Freq':[]})
    freqdf.set_index(['OriginAirportId', 'DestAirportId', 'Distance'], inplace=True)

    for year in range(1987, 2016):
        if(year == 1987):
            startmonth = 10
        else:
            startmonth = 1
        for month in range(startmonth, 13):
            flightfile='../data/%d_%d.csv' %(year, month)
            df = pd.read_csv(flightfile)[['OriginAirportId', 'DestAirportId', 'Distance']]

            #Create a freq column and calculate frequency for a given month.
            df['Freq'] = np.nan
            df['Freq'] = df.groupby(['OriginAirportId', 'DestAirportId', 'Distance']).transform(len)
            df.drop_duplicates(inplace=True)
            df.set_index(['OriginAirportId', 'DestAirportId', 'Distance'], inplace=True)

            #Align rows by index, and sum frequencies.
            freqdf, df = freqdf.align(df, fill_value=0)
            freqdf += df

    return freqdf.reset_index(level=2)


def checkdistance(distdf):
    #Input dataframe has index=Origin, Dest; columns = Distance, Freq.
    #Freq = frequency of each distance given origin, dest.
    flights = list(distdf.index.unique())
    roundtrips = [x for x in flights if (x[1], x[0]) in flights and x[0] < x[1]]

    #Check, store, and print various errors.
    print "Same Origin and Dest Airports:"
    same_origindest = [x[0] for x in flights if x[0] == x[1]]
    print same_origindest

    print "Multiple Distance Errors:"
    multipledist = [(x[0], x[1]) for x in flights if distdf.Distance[x[0], x[1]].size > 1]
    for x in multipledist:
        print "Flight: ", x
        print "Distances: ", list(distdf.Distance[x])
        print "Frequency: ",  list(distdf.Freq[x])

    print "Round Trip Errors:"
    roundtriperrors = [x for x in roundtrips if 
        (True if distdf.Distance[x].size != distdf.Distance[x[1], x[0]].size
        else (distdf.Distance[x] != distdf.Distance[x[1], x[0]]) 
            if (distdf.Distance[x].size == 1)
        else (Set(distdf.Distance[x]) != Set(distdf.Distance[x[1], x[0]])))]

    for x in roundtriperrors:
        print "Flight: ", x
        print "Distance to: ", list(distdf.Distance[x])
        print "Distance back: ", list(distdf.Distance[x[1], x[0]])

    return [same_origindest, multipledist, roundtriperrors]


def getdistance():
    #Get distance info from flight data and check for errors.
    distfreq_df = get_distancefreq()
    errors = checkdistance(distfreq_df)

    #Remove same origin/dest flights.
    distfreq_df.drop([(x,x) for x in errors[0]], inplace=True)

    #Choose distance which occurs more than half the time.
    distfreq_df.reset_index(inplace=True)
    distfreq_df['TotalFreq'] = distfreq_df.groupby(['OriginAirportId', 'DestAirportId']).Freq.transform(sum)
    distfreq_df = distfreq_df[distfreq_df.Freq/distfreq_df.TotalFreq > 0.5]

    #Write to csv.
    distfreq_df.drop(['Freq', 'TotalFreq'], axis=1, inplace=True)
    distfreq_df.to_csv('../data/distance.csv', index=False)
