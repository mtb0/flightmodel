#!/usr/bin/env python
"""Take a dataframe with flight info, and extend it by calculating new variables which will 
be used in our regression models."""

import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None #Suppress overwrite error.

def get_jetstream(year, month):
    """Read flight data from a particular year and month, along with LatLong and distance tables.
    Combine and produce a dataframe containing Distance, Jetstream, and SchTime, along with identifying 
    flight information."""
    latlong = pd.read_csv('../data/LatLong.csv')
    flights = pd.read_csv('../data/%d_%d.csv' %(year, month))
    dist = pd.read_csv('../data/distance.csv')

    #Merge with LatLong and distance tables.
    flights = flights.merge(dist, on=['OriginAirportId', 'DestAirportId'])
    flights = flights.merge(latlong, left_on='OriginAirportId', right_on='AirportId')
    flights.rename(columns={'Latitude':'OriginLat', 'Longitude':'OriginLong'}, inplace=True)
    flights = flights.merge(latlong, left_on='DestAirportId', right_on='AirportId')
    flights.rename(columns={'Latitude':'DestLat', 'Longitude':'DestLong'}, inplace=True)

    #Calculate degrees Latitude North and degrees Longitude East travelled.
    df = flights[['OriginAirportId', 'OriginLat', 'OriginLong', 'DestLat', 'DestLong', 'DestAirportId', 
    'Distance', 'SchTime']]
    df['dLat'] = df.DestLat - df.OriginLat
    df['dLong'] = df.DestLong - df.OriginLong
    df.dLong[df.dLong < -180] += 360
    df.dLong[df.dLong > 180] -= 360

    #Estimate Jetstream effect and return dataframe.
    df['Jetstream'] = -df.dLong*df.Distance/np.sqrt(df.dLong**2 + df.dLat**2)
    return df

def get_pacific(df):
    """Given a dataframe with information about Destination airport Latitude and Longitude, it returns 
    a dataframe with column DestOverseas roughly indicating whether the Destination airport is in 
    the Pacific."""

    df['DestOverseas'] = (df.DestLat < 50) & (np.abs(df.DestLong) > 130)
    return df
