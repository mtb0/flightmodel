#!/usr/bin/env python
"""Use equations involving DepTime, DepDelay, SchDep, ArrTime, ArrDelay, SchArr, ActualTime, and SchTime 
to enforce consistency and fill in NaNs.
We consider SchTime values which are over 1 interquartile range (or 30 minutes) from the 1st and 3rd 
quartile in order to detect outliers.  We adjust those outside that range by a multiple of 60 which will 
bring it closest to the median.  Finally, we overwrite current data with corrected data restricted to 
Date, Day, Carrier, Origin, Destination, SchDep, SchArr, and SchTime."""

import pandas as pd
import numpy as np
pd.options.mode.chained_assignment = None

def fix_schdata(year, month):
    flights = pd.read_csv('../data/%d_%d.csv' %(year, month), dtype={'Carrier':str})

    #Eliminate rows with same Origin and Destination.
    flights = flights[flights.OriginAirportId != flights.DestAirportId]

    #Convert between hhmm and minutes after midnight.
    mintotime = (lambda minutes: 100*(minutes//60) + minutes%60)
    timetomin = (lambda t: 60*(t//100) + t%100)

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
    dep_valid = flights.DepTime.notnull() & flights.DepDelay.notnull() & flights.SchDep.notnull()
    arr_valid = flights.ArrTime.notnull() & flights.ArrDelay.notnull() & flights.SchArr.notnull()
    act_valid = df['SValid'] & df['AValid'] & flights.ArrDelay.notnull() & flights.DepDelay.notnull()
    tz_valid = df['AValid'] & flights.DepTime.notnull() & flights.ArrTime.notnull()
    sch_valid = df['SValid'] & flights.SchArr.notnull() & flights.SchDep.notnull()

    #Check if the equations fail.
    df['D'] = ((timetomin(flights.DepTime) - flights.DepDelay - timetomin(flights.SchDep))%1440 != 0) & dep_valid
    df['A'] = ((timetomin(flights.ArrTime) - flights.ArrDelay - timetomin(flights.SchArr))%1440 != 0) & arr_valid
    df['ACT'] = ((flights.ActualTime - flights.ArrDelay + flights.DepDelay)%1440 != flights.SchTime) & act_valid
    df['TZ'] = ((timetomin(flights.ArrTime) - timetomin(flights.DepTime) - flights.ActualTime)%60 != 0) & tz_valid
    df['SCH'] = ((timetomin(flights.SchArr) - timetomin(flights.SchDep) - flights.SchTime)%60 != 0) & sch_valid
		
    #When SchDep is null, ACT and TZ hold, so we set SchDep = DepTime - DepDelay.
    schdepnull = (flights.SchDep.isnull() & flights.DepTime.notnull() & flights.DepDelay.notnull())
    flights.SchDep[schdepnull] = mintotime((timetomin(flights.DepTime[schdepnull]) - flights.DepDelay[schdepnull])%1440)

    #When SchArr is null, ACT and TZ hold, so we set SchArr = ArrTime - ArrDelay.
    scharrnull = (flights.SchArr.isnull() & flights.ArrTime.notnull() & flights.ArrDelay.notnull())
    flights.SchArr[scharrnull] = mintotime((timetomin(flights.DepTime[scharrnull]) - flights.DepDelay[scharrnull])%1440)

    #If SchTime is invalid and ActualTime is invalid, we need SchDep & SchArr valid & time zone info (which we may tackle later).

    #If SchTime is invalid and ActualTime is valid, then D, A, TZ hold. We set SchDep, SchArr, and SchTime to appropriate values.
    snulla = (~df.SValid) & df.AValid
    flights.SchDep[snulla] = mintotime((timetomin(flights.DepTime[snulla]) - flights.DepDelay[snulla])%1440)
    flights.SchArr[snulla] = mintotime((timetomin(flights.ArrTime[snulla]) - flights.ArrDelay[snulla])%1440)
    flights.SchTime[snulla] = (flights.ActualTime[snulla] - flights.ArrDelay[snulla] + flights.DepDelay[snulla])%1440

    #If SchTime is valid, ActualTime is invalid, and SCH fails, then all other equations hold. We update SchTime.
    sanull = df.SValid & (~df.AValid) & df.SCH
    schtimeerror = (timetomin(flights.SchArr[sanull]) - timetomin(flights.SchDep[sanull]) - flights.SchTime[sanull])%60
    adderror = (schtimeerror < 30 | (flights.SchTime[sanull] + schtimeerror < 60))
    flights.SchTime[sanull] += schtimeerror - 60
    if(len(adderror) > 0):
        flights.SchTime[sanull & adderror] += 60

    #If SchTime and ActualTime are valid, then we update SchDep, SchArr, SchTime based on errors.
    sa = df.SValid & df.AValid & df.SCH
    flights.SchDep[(sa & df.D)] = mintotime((timetomin(flights.DepTime[(sa & df.D)]) - flights.DepDelay[(sa & df.D)])%1440)
    flights.SchArr[(sa & df.A)] = mintotime((timetomin(flights.ArrTime[(sa & df.A)]) - flights.ArrDelay[(sa & df.A)])%1440)
    flights.SchTime[(sa & df.ACT)] = (flights.ActualTime[(sa & df.ACT)] - flights.ArrDelay[(sa & df.ACT)] + flights.DepDelay[(sa & df.ACT)])%1440

    #When TZ and SCH fails, then D, A, ACT hold.  This suggests ActualTime and SchTime are incorrect.
    schtimeerror = (timetomin(flights.SchArr[(sa & df.TZ)]) - timetomin(flights.SchDep[(sa & df.TZ)]) - flights.SchTime[(sa & df.TZ)])%60
    adderror = (schtimeerror < 30 | (flights.SchTime[(sa & df.TZ)] + schtimeerror < 60))
    flights.SchTime[(sa & df.TZ)] += schtimeerror - 60
    if(adderror.sum() > 0):
        flights.SchTime[sa & adderror] += 60

    #Update SchDepMin and SchArrMin.
    df['SValid'] = flights.SchTime.notnull() & (flights.SchTime > 0)
    sch_valid = df['SValid'] & flights.SchArr.notnull() & flights.SchDep.notnull()
    df['SCH'] = ((timetomin(flights.SchArr) - timetomin(flights.SchDep) - flights.SchTime)%60 == 0) & sch_valid

    #Keep entries where SchArr, SchDep, SchTime are all valid, and equation SCH holds.
    flights = flights[df.SCH]
    newflights = pd.DataFrame({
        'Carrier':flights.Carrier, 
        'Day':flights.Day, 
        'Date':flights.Date, 
        'OriginAirportId':flights.OriginAirportId, 
        'DestAirportId':flights.DestAirportId, 
        'SchDep':flights.SchDep, 
        'SchArr':flights.SchArr, 
        'SchTime':flights.SchTime})

    newflights.reset_index(drop=True)
    return newflights


def adjust_schtime(df):
    #Input: data frame with Origin, Dest, and SchTime columns.
    #We adjust SchTime outliers by multiples of 60 minutes.

    #Output 1st and 3rd quartile. If there is < 20 flights that month, we output median.
    #This indicates we adjust all SchTime.
    firstquartile = lambda A: np.median(A) if len(A) < 20 else A.quantile(0.25)
    thirdquartile = lambda A: np.median(A) if len(A) < 20 else A.quantile(0.75)

    #Calculate median and quartiles of SchTime with given Origin/Dest.
    df['Median'] = df.groupby(['OriginAirportId', 'DestAirportId']).SchTime.transform(np.median)
    df['Q1'] = df.groupby(['OriginAirportId', 'DestAirportId']).SchTime.transform(firstquartile)
    df['Q3'] = df.groupby(['OriginAirportId', 'DestAirportId']).SchTime.transform(thirdquartile)
    df['IQR'] = map(lambda x: min(x, 30), df.Q3 - df.Q1)

    #Detect and adjust outliers.
    outlier = (df.SchTime <= df.Q1 - df.IQR) | (df.SchTime >= df.Q3 + df.IQR)
    df.SchTime[outlier] += 60 * np.round((df.Median[outlier] - df.SchTime[outlier])/60.)

    df.drop(['Median', 'Q1', 'Q3', 'IQR'], axis=1, inplace=True)
    return df
