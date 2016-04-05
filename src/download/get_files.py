#!/usr/bin/env python
"""Download Latitude/Longitude information and Flight time information from 
the Bureau of Transportation Statistics website, using wget."""

import os
import pandas as pd
import tempfile

URL='http://tsdata.bts.gov/'
LATLONG='187806114_T_MASTER_CORD'
FLIGHT='On_Time_On_Time_Performance'

def get_latlong():
    newlatlongfile='../data/LatLong.csv'

    #Download LatLong.csv
    os.system('wget ' + URL + LATLONG + '.zip')
    os.system('unzip ' + LATLONG + '.zip')
    os.system('rm ' + LATLONG + '.zip')
    os.system('mv ' + LATLONG + '.csv ' + newlatlongfile)

    #Read LatLong.csv, select and write columns.
    df = pd.read_csv(newlatlongfile)
    latlong = pd.DataFrame({
        'AirportId':df.AIRPORT_SEQ_ID, 
        'AirportName':df.DISPLAY_AIRPORT_NAME, 
        'Latitude':df.LATITUDE, 
        'Longitude':df.LONGITUDE})

    latlong.dropna(inplace=True)
    latlong.to_csv(newlatlongfile, index=False)


def get_flights(year, month):
    flightfile=FLIGHT + '_%d_%d' %(year, month)
    flighturl=URL + 'PREZIP/' + flightfile + '.zip'
    newflightfile='../data/%d_%d.csv' %(year, month)

    #Download flight data as year_month.csv
    os.system('wget ' + flighturl)
    tempdir = tempfile.mkdtemp()  #Create temporary directory to place unzipped file.
    os.system('unzip ' + flightfile + ' -d ' + tempdir)
    os.system('rm ' + flightfile + '.zip')
    os.system('mv ' + tempdir + '/' + flightfile + '.csv ' + newflightfile)
    os.system('rm ' + tempdir + '/*')
    os.removedirs(tempdir)

    #Read LatLong.csv, select and write columns.
    df=pd.read_csv(newflightfile, dtype={'UniqueCarrier':str})
    flightdf=pd.DataFrame({
        'Day':df.DayOfWeek, 
        'Date':df.FlightDate, 
        'Carrier':df.UniqueCarrier, 
        'OriginAirportId':df.OriginAirportSeqID, 
        'DestAirportId':df.DestAirportSeqID, 
        'SchDep':df.CRSDepTime, 
        'DepTime':df.DepTime, 
        'DepDelay':df.DepDelay, 
        'SchArr':df.CRSArrTime, 
        'ArrTime':df.ArrTime, 
        'ArrDelay':df.ArrDelay, 
        'SchTime':df.CRSElapsedTime, 
        'ActualTime':df.ActualElapsedTime, 
        'Distance':df.Distance})
    flightdf.to_csv(newflightfile, index=False)
