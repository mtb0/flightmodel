#!/usr/bin/env python
"""Download Latitude/Longitude information and Flight time information from 
the Bureau of Transportation Statistics website, using wget."""

import os
import sys

import pandas as pd

URL='http://tsdata.bts.gov/'
LATLONG='873930595_T_MASTER_CORD'
FLIGHT='On_Time_On_Time_Performance'

def getLatLong():
	os.system('wget ' + URL + LATLONG + '.zip')
	os.system('unzip ' + LATLONG + '.zip')
	os.system('rm ' + LATLONG + '.zip')
	os.system('mv ' + LATLONG + '.csv LatLong.csv')

	df = pd.read_csv('LatLong.csv')
	LatLong = pd.DataFrame({'AirportId':df[df.columns[0]], 
							'AirportName':df[df.columns[3]], 
							'Latitude':df['LATITUDE'], 
							'Longitude':df['LONGITUDE']})
	LatLong.dropna(inplace=True)
	LatLong.to_csv('LatLong.csv', index=False)

def getFlights(year, month):
	flightFile=FLIGHT + '_%d_%d' %(year, month)
	newflightFile='%d_%d.csv' %(year, month)
	flighturl=URL + 'PREZIP/' + flightFile + '.zip'
	
	os.system('wget ' + flighturl)
	os.system('unzip ' + flightFile + ' -d temp')
	os.system('rm ' + flightFile + '.zip')
	os.system('mv temp/' + flightFile + '.csv ' + newflightFile)
	os.system('rm -rf temp')

	df=pd.read_csv(newflightFile, dtype={'UniqueCarrier': str})
	FlightDF=pd.DataFrame({'Day':df[df.columns[4]], 
						 'Date':df[df.columns[5]], 
						 'Carrier':df[df.columns[6]], 
						 'OriginAirportId':df[df.columns[12]], 
						 'DestAirportId':df[df.columns[21]], 
						 'SchDep':df[df.columns[29]], 
						 'DepTime':df[df.columns[30]], 
						 'DepDelay':df[df.columns[31]], 
						 'SchArr':df[df.columns[40]], 
						 'ArrTime':df[df.columns[41]], 
						 'ArrDelay':df[df.columns[42]], 
						 'SchTime':df[df.columns[50]], 
						 'ActualTime':df[df.columns[51]], 
						 'Distance':df[df.columns[54]]})
	FlightDF.to_csv(newflightFile, index=False)

def main():
	getLatLong()
	for year in range(1987,2016):
		if(year == 1987):
			startmonth=10
		else:
			startmonth=1
		for month in range(startmonth, 13):
			getFlights(year, month)


if __name__ == '__main__':
	sys.exit(main())
