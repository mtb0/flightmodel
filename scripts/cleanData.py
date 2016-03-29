#!/usr/bin/env python
"""Use equations involving DepTime, DepDelay, SchDep, ArrTime, ArrDelay, SchArr, ActualTime, and SchTime 
to enforce consistency and fill in NaNs.
We consider SchTime values which are over 1 interquartile range (or 30 minutes) from the 1st and 3rd 
quartile in order to detect outliers.  We adjust those outside that range by a multiple of 60 which will 
bring it closest to the median.  Finally, we overwrite current data with corrected data restricted to 
Date, Day, Carrier, Origin, Destination, SchDep, SchArr, and SchTime."""

import sys
import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None

def FixSchData(year, month):
	flights = pd.read_csv(str(year)+'_'+str(month)+'.csv', dtype={'Carrier': str})

	#Eliminate rows with same Origin and Destination.
	flights = flights[flights.OriginAirportId != flights.DestAirportId]

	#Convert between hhmm and minutes after midnight.
	MintoTime = (lambda minutes: 100*(minutes//60) + minutes%60)
	TimetoMin = (lambda t: 60*(t//100) + t%100)

	#The following equations must hold.  We check for each type of error.
	#D. DepTime = SchDep + DepDelay
	#A. ArrTime = SchArr + ArrDelay
	#ACT. ActualTime = SchTime + ArrDelay - DepDelay
	#TZ. ActualTime = ArrTime - DepTime, up to multiples of 60 minutes due to time zone.
	#SCH. SchTime = SchArr - SchDep, up to multiples of 60 minutes.
	df = pd.DataFrame({})

	#Indicator whether SchTime and ActualTime are invalid.  (If ActualTime is valid, so are DepTime, DepDelay, ArrTime, ArrDelay.)
	df['SValid'] = flights.SchTime.notnull() & (flights.SchTime > 0)
	df['AValid'] = flights.ActualTime.notnull() & (flights.ActualTime > 0)

	#Check that variables in the equations above are valid.
	DepValid = flights.DepTime.notnull() & flights.DepDelay.notnull() & flights.SchDep.notnull()
	ArrValid = flights.ArrTime.notnull() & flights.ArrDelay.notnull() & flights.SchArr.notnull()
	ActValid = df['SValid'] & df['AValid'] & flights.ArrDelay.notnull() & flights.DepDelay.notnull()
	TZValid = df['AValid'] & flights.DepTime.notnull() & flights.ArrTime.notnull()
	SCHValid = df['SValid'] & flights.SchArr.notnull() & flights.SchDep.notnull()

	#Check if the equations fail.
	df['D'] = ((TimetoMin(flights.DepTime) - flights.DepDelay - TimetoMin(flights.SchDep))%1440 != 0) & DepValid
	df['A'] = ((TimetoMin(flights.ArrTime) - flights.ArrDelay - TimetoMin(flights.SchArr))%1440 != 0) & ArrValid
	df['ACT'] = ((flights.ActualTime - flights.ArrDelay + flights.DepDelay)%1440 != flights.SchTime) & ActValid
	df['TZ'] = ((TimetoMin(flights.ArrTime) - TimetoMin(flights.DepTime) - flights.ActualTime)%60 != 0) & TZValid
	df['SCH'] = ((TimetoMin(flights.SchArr) - TimetoMin(flights.SchDep) - flights.SchTime)%60 != 0) & SCHValid
		
	#When SchDep is null, ACT and TZ hold, so we set SchDep = DepTime - DepDelay.
	SchDepNull = (flights.SchDep.isnull() & flights.DepTime.notnull() & flights.DepDelay.notnull())
	flights.SchDep[SchDepNull] = MintoTime((TimetoMin(flights.DepTime[SchDepNull]) - flights.DepDelay[SchDepNull])%1440)

	#When SchArr is null, ACT and TZ hold, so we set SchArr = ArrTime - ArrDelay.
	SchArrNull = (flights.SchArr.isnull() & flights.ArrTime.notnull() & flights.ArrDelay.notnull())
	flights.SchArr[SchArrNull] = MintoTime((TimetoMin(flights.DepTime[SchArrNull]) - flights.DepDelay[SchArrNull])%1440)

	#If SchTime is invalid and ActualTime is invalid, we need SchDep & SchArr valid & time zone info (which we may tackle later).

	#If SchTime is invalid and ActualTime is valid, then D, A, TZ hold. We set SchDep, SchArr, and SchTime to appropriate values.
	SNullA = (~df.SValid) & df.AValid
	flights.SchDep[SNullA] = MintoTime((TimetoMin(flights.DepTime[SNullA]) - flights.DepDelay[SNullA])%1440)
	flights.SchArr[SNullA] = MintoTime((TimetoMin(flights.ArrTime[SNullA]) - flights.ArrDelay[SNullA])%1440)
	flights.SchTime[SNullA] = (flights.ActualTime[SNullA] - flights.ArrDelay[SNullA] + flights.DepDelay[SNullA])%1440

	#If SchTime is valid, ActualTime is invalid, and SCH fails, then all other equations hold. We update SchTime.
	SANull = df.SValid & (~df.AValid) & df.SCH
	SchTimeError = (TimetoMin(flights.SchArr[SANull]) - TimetoMin(flights.SchDep[SANull]) - flights.SchTime[SANull])%60
	AddError = (SchTimeError < 30 | (flights.SchTime[SANull] + SchTimeError < 60))
	flights.SchTime[SANull] += SchTimeError - 60
	if(len(AddError) > 0):
		flights.SchTime[SANull & AddError] += 60

	#If SchTime and ActualTime are valid, then we update SchDep, SchArr, SchTime based on errors.
	SA = df.SValid & df.AValid & df.SCH
	flights.SchDep[(SA & df.D)] = MintoTime((TimetoMin(flights.DepTime[(SA & df.D)]) - flights.DepDelay[(SA & df.D)])%1440)
	flights.SchArr[(SA & df.A)] = MintoTime((TimetoMin(flights.ArrTime[(SA & df.A)]) - flights.ArrDelay[(SA & df.A)])%1440)
	flights.SchTime[(SA & df.ACT)] = (flights.ActualTime[(SA & df.ACT)] - flights.ArrDelay[(SA & df.ACT)] + flights.DepDelay[(SA & df.ACT)])%1440

	#When TZ and SCH fails, then D, A, ACT hold.  This suggests ActualTime and SchTime are incorrect.
	SchTimeError = (TimetoMin(flights.SchArr[(SA & df.TZ)]) - TimetoMin(flights.SchDep[(SA & df.TZ)]) - flights.SchTime[(SA & df.TZ)])%60
	AddError = (SchTimeError < 30 | (flights.SchTime[(SA & df.TZ)] + SchTimeError < 60))
	flights.SchTime[(SA & df.TZ)] += SchTimeError - 60
	if(AddError.sum() > 0):
		flights.SchTime[SA & AddError] += 60

	#Update SchDepMin and SchArrMin.
	df['SValid'] = flights.SchTime.notnull() & (flights.SchTime > 0)
	SCHValid = df['SValid'] & flights.SchArr.notnull() & flights.SchDep.notnull()
	df['SCH'] = ((TimetoMin(flights.SchArr) - TimetoMin(flights.SchDep) - flights.SchTime)%60 == 0) & SCHValid

	#Keep entries where SchArr, SchDep, SchTime are all valid, and equation SCH holds.
	flights = flights[df.SCH]
	newFlights = pd.DataFrame({'Carrier':flights.Carrier, 
							   'Day':flights.Day, 
							   'Date':flights.Date, 
							   'OriginAirportId':flights.OriginAirportId, 
							   'DestAirportId':flights.DestAirportId, 
							   'SchDep':flights.SchDep, 
							   'SchArr':flights.SchArr, 
							   'SchTime':flights.SchTime})

	newFlights.index = range(len(newFlights))
	return newFlights

#Output 1st and 3rd quartile. If there is < 20 flights that month, we output median.
#This indicates we adjust all SchTime.
def FirstQuartile(A):
	if(len(A) < 20):
		return np.median(A)
	else:
		A = sorted(list(A))
		return A[int(np.ceil(len(A)/4.))-1]

def ThirdQuartile(A):
	if(len(A) < 20):
		return np.median(A)
	else:
		A = sorted(list(A))
		return A[int(len(A) - 1 - np.ceil(len(A)/4))]


def AdjustSchTime(df):
	#Input: data frame with Origin, Dest, and SchTime columns.
	#We adjust SchTime outliers by multiples of 60 minutes.

	#Calculate median and quartiles of SchTime with given Origin/Dest.
	df['Median'] = df.groupby(['OriginAirportId', 'DestAirportId']).SchTime.transform(np.median)
	df['FirstQ'] = df.groupby(['OriginAirportId', 'DestAirportId']).SchTime.transform(FirstQuartile)
	df['ThirdQ'] = df.groupby(['OriginAirportId', 'DestAirportId']).SchTime.transform(ThirdQuartile)
	df['IQR'] = map(lambda x: min(x, 30), df.ThirdQ - df.FirstQ)

	Outlier = (df.SchTime <= df.FirstQ - df.IQR) | (df.SchTime >= df.ThirdQ + df.IQR)
	df.SchTime[Outlier] += 60 * np.round((df.Median[Outlier] - df.SchTime[Outlier])/60.)

	df.drop(['Median', 'FirstQ', 'ThirdQ', 'IQR'], axis=1, inplace=True)
	return df


#Clean Flight data.
def main():
	for year in range(1987, 2016):
		if(year == 1987):
			startmonth = 10
		else:
			startmonth = 1
		for month in range(startmonth, 13):
			print year, month
			newFlightdata = FixSchData(year, month)
			FinalFlightdata = AdjustSchTime(newFlightdata)
			FinalFlightdata.to_csv(str(year)+'_'+str(month)+'.csv', index=False)
	

if __name__ == '__main__':
	sys.exit(main())
