#!/usr/bin/env python
"""From flight data, gather info about distance between airports and check for consistency.  We then 
write to distance.csv"""

import sys
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None #Suppress overwrite error.

def getDistanceFreq():
	#Empty dataframe to accumulate frequency, based on Origin, Dest, and Distance.
	freqDF=pd.DataFrame({'OriginAirportId':[] , 
						 'DestAirportId':[], 
						 'Distance':[], 
						 'Freq':[]}).set_index(['OriginAirportId', 'DestAirportId', 'Distance'])

	for year in range(1987, 2016):
		if(year == 1987):
			startmonth = 10
		else:
			startmonth = 1
		for month in range(startmonth, 13):
			print year, month
			flightFile=str(year)+'_'+str(month)+'.csv'
			df = pd.read_csv(flightFile)[['OriginAirportId', 'DestAirportId', 'Distance']]

			#Create a freq column and calculate frequency for a given month.
			df['Freq'] = np.nan
			df['Freq'] = df.groupby(['OriginAirportId', 'DestAirportId', 'Distance']).transform(len)
			df.drop_duplicates(inplace=True)
			df.set_index(['OriginAirportId', 'DestAirportId', 'Distance'], inplace=True)

			#Align rows by index, and sum frequencies.
			freqDF, df = freqDF.align(df, fill_value=0)
			freqDF += df

	return freqDF.reset_index(level=2)

def checkDistance(distDF):
	#Input dataframe has index=Origin, Dest; columns = Distance, Freq.  Given index, then distances are distinct.
	Flights = list(distDF.index.unique())
	RoundTrips = [x for x in Flights if (x[1], x[0]) in Flights and x[0] < x[1]]

	#Check, store, and print various errors.
	print "Same Origin and Dest Airports:"
	SameOriginDest = [x[0] for x in Flights if x[0] == x[1]]
	print SameOriginDest

	print "Multiple Distance Errors:"
	MultipleDist = [(x[0], x[1]) for x in Flights if distDF.Distance[x[0], x[1]].size > 1]
	for x in MultipleDist:
		print "Flight: ", x
		print "Distances: ", list(distDF.Distance[x])
		print "Frequency: ",  list(distDF.Freq[x])

	print "Round Trip Errors:"
	RoundTripErrors = []
	for x in RoundTrips:
		if(distDF.Distance[x].size != distDF.Distance[x[1], x[0]].size):
			RoundTripErrors.append(x)
		elif(distDF.Distance[x].size == 1):
			if(distDF.Distance[x] != distDF.Distance[x[1], x[0]]):
				RoundTripErrors.append(x)
		else:
			if(Set(list(distDF.Distance[x])) != Set(list(distDF.Distance[x[1], x[0]]))):
				RoundTripErrors.append(x)

	for x in RoundTripErrors:
		print "Flight: ", x
		print "Distance to: ", list(distDF.Distance[x])
		print "Distance back: ", list(distDF.Distance[x[1], x[0]])

	return [SameOriginDest, MultipleDist, RoundTripErrors]

def main():
	#Get distance info from flight data and check for errors.
	DistFreqDF = getDistanceFreq()
	Errors = checkDistance(DistFreqDF)

	#Remove same origin/dest flights.
	DistFreqDF.drop([(x,x) for x in Errors[0]], inplace=True)

	#Choose distance which occurs more than half the time.
	DistFreqDF.reset_index(inplace=True)
	DistFreqDF['totalFreq'] = DistFreqDF.groupby(['OriginAirportId', 'DestAirportId']).Freq.transform(sum)
	DistFreqDF = DistFreqDF[DistFreqDF.Freq/DistFreqDF.totalFreq > 0.5]

	#Write to csv.
	DistFreqDF.drop(['Freq', 'totalFreq'], axis=1, inplace=True)
	DistFreqDF.to_csv('distance.csv', index=False)

if __name__ == '__main__':
	sys.exit(main())
