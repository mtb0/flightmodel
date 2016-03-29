#!/usr/bin/env python

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from sklearn import linear_model
import sys
pd.options.mode.chained_assignment = None #Suppress overwrite error.


############## HELPER FUNCTIONS ##############
MonthDict = {1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 7:'July', 
    8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}

def DatetoDays(date):
    """Convert date to days after Jan 1, 1988."""
    ElapsedDays = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    ElapsedDaysLeap = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    [yr, month, day] = map(int, date.split('-'))
    adj = 1 if (yr > 2000) else 0   #Correction to calculation, since 2000 is not a leap year.
    if((yr%4 == 0) & (yr%400 != 0)):
        return np.ceil(365.25*(yr-1988)) + ElapsedDaysLeap[month-1] + (day-1) - adj
    else:
        return np.ceil(365.25*(yr-1988)) + ElapsedDays[month-1] + (day-1) - adj

def TimetoMin(time):
    """Turn hhmm into minutes after midnight."""
    return (60*np.floor(time/100) + time%100)

############## FILTERING ##############
def getJetstream(year, month):
    """Read flight data from a particular year and month, along with LatLong and distance tables.
    Combine and produce a dataframe containing Distance, Jetstream, and SchTime, along with identifying 
    flight information."""
    LL = pd.read_csv('LatLong.csv')
    flights = pd.read_csv('%d_%d.csv' %(year, month))
    dist = pd.read_csv('distance.csv')

    #Merge with LatLong and distance tables.
    flights = flights.merge(dist, on=['OriginAirportId', 'DestAirportId'])
    flights = flights.merge(LL, left_on='OriginAirportId', right_on='AirportId')
    flights.rename(columns={'Latitude':'OriginLat', 'Longitude':'OriginLong'}, inplace=True)
    flights = flights.merge(LL, left_on='DestAirportId', right_on='AirportId')
    flights.rename(columns={'Latitude':'DestLat', 'Longitude':'DestLong'}, inplace=True)

    #Calculate Jetstream and return data frame.
    df = flights[['OriginAirportId', 'OriginLat', 'OriginLong', 'DestLat', 'DestLong', 'DestAirportId', 
    'Distance', 'SchTime']]
    df['dLat'] = df.DestLat - df.OriginLat
    df['dLong'] = df.DestLong - df.OriginLong
    df.dLong[df.dLong <= -165] += 360
    df.dLong[df.dLong > 195] -= 360
    df['Jetstream'] = -df.dLong*df.Distance/np.sqrt(df.dLong**2 + df.dLat**2)
    return df

def getPacific(df):
    """Given a dataframe with information about Origin and Destination airport Latitude and Longitude, 
    it returns a dataframe with columns OriginOverseas and DestOverseas indicating whether the Destination 
    airport is in the Pacific."""

    df['DestOverseas'] = (df.DestLat < 50) & (np.abs(df.DestLong) > 130)
    return df


############## REGRESSION #############
def Regression(year, month, df=pd.DataFrame({})):
    """Calculate OLS regression coefficients modeling SchTime with Distance and Jetstream info."""
    #Obtain relevant dataframe and calculate Jetstream.
    if(len(df) == 0):
        df = getJetstream(year, month)
    
    #Run OLS regression.
    X = df[['Distance', 'Jetstream']]
    Y = df['SchTime']
    ols = linear_model.LinearRegression()
    ols.fit(X,Y)
    params = list(ols.coef_)
    params.append(ols.intercept_)
    score = ols.score(X,Y)
    
    #Calculate standard error.
    MSE = np.mean((Y - ols.predict(X).T)**2)    #Mean Square Error.
    X['ones'] = 1
    StdError = np.sqrt(MSE * np.diag(np.linalg.pinv(np.dot(X.T, X))))
    return (params, score, StdError)

############### PLOTTING ##############
def PlotSchTime(origin, destination, carrier):
    """Input: 5 digit AirportID code for origin and destination.  Plot scheduled flight times from 
    origin to destination from Oct 1, 1987 to Dec 31, 2015."""
    dataFrames = []
    for year in range(1987, 2016):
        if(year == 1987):
            startmonth = 10
        else:
            startmonth = 1
        for mon in range(startmonth, 13):
            data = str(year)+'_'+str(mon)+'.csv'
            flights = pd.read_csv(data)

            #Filter by origin, destination, and carrier.
            isFlight = (np.floor(flights.OriginAirportId/100) == origin) & (np.floor(flights.DestAirportId/100) == destination) & (flights.Carrier == carrier)
            df = flights[isFlight][['Date', 'SchDep', 'SchTime']]

            #Determine \# days after Jan. 1, 1988.
            df['Time'] = df.Date.apply(DatetoDays)
            df['Time'] += TimetoMin(df.SchDep)/1440.
            df.drop(['Date', 'SchDep'],axis=1, inplace=True)
            dataFrames.append(df)

    flightdist = pd.concat(dataFrames, ignore_index=True)
    
    #Determine start and end date in days.
    daystart = DatetoDays('1987-10-01')
    dayend = DatetoDays('2016-01-01')
    
    #Format, plot, and save graph.
    fig, ax = plt.subplots(figsize=(20,10))
    ax.plot(flightdist.Time, flightdist.SchTime, 'b.')
    ax.set_xlim(daystart, dayend)
    ax.set_xticks(np.arange(0, dayend, 365.25))
    labels = range(1988, 2017)
    ax.set_xticklabels(labels, rotation='vertical', fontsize=20)
    ax.set_title('%d to %d' %(origin, destination), fontsize=20)
    ax.set_xlabel('Date', fontsize=20)
    ax.set_ylabel('Scheduled Flight Time', fontsize=20)
    plt.subplots_adjust(bottom = 0.15)
    fig.savefig('%s%d_%d.jpg' %(carrier, origin, destination))


def PlotDistSchTime(year, month, df=pd.DataFrame({})):
    """Plot Dist vs SchTime for flights in a given year and month."""
    if(len(df) == 0):
        df = getJetstream(year, month)  #Get Longitude info to see if west or eastbound.
    Westbound = (df.dLong < 0)
    Eastbound = (df.dLong > 0)

    #Plot Dist vs SchTime. Color Eastbound flights red and Westbound flights blue.
    fig, ax = plt.subplots()
    ax.plot(df.Distance[Eastbound], df.SchTime[Eastbound], 'r.', ms = 2)
    ax.plot(df.Distance[Westbound], df.SchTime[Westbound], 'b.', ms = 2)
    ax.set_title('Flights in %s %d' %(MonthDict[month], year))
    ax.set_xlabel('Distance (miles)')
    ax.set_ylabel('Scheduled Flight Time')
    
    #Make legend.
    red_patch = mpatches.Patch(color='red', label='Eastbound')
    blue_patch = mpatches.Patch(color='blue', label='Westbound')
    lines = [red_patch, blue_patch]
    labels = [line.get_label() for line in lines]
    plt.legend(lines, labels, loc='upper left')
    fig.savefig('%d_%d.jpg' %(year, month))


def PlotRegression(year, month, df=pd.DataFrame({})):
    """Plot distance vs SchTime for flights in a given year and month, along with the 
    regression lines capturing flights due east and due west."""
    #Get regression coefficients for flights landing in Pacific and other flights.
    if(len(df) == 0):
        df = getJetstream(year, month)
    df = getPacific(df)
    PacificDest = df[df.DestOverseas]
    Pacparams = Regression(year, month, PacificDest)[0]
    Pacdist = Pacparams[0]
    Pacjet = Pacparams[1]
    Pacground = Pacparams[2]

    USDest = df[~df.DestOverseas]
    USparams = Regression(year, month, USDest)[0]
    USdist = USparams[0]
    USjet = USparams[1]
    USground = USparams[2]

    #Get regression line points.
    x = np.linspace(0, 5000, 2)
    Pacy_east = Pacground + (Pacdist - Pacjet)*x
    Pacy_west = Pacground + (Pacdist + Pacjet)*x
    USy_east = USground + (USdist - USjet)*x
    USy_west = USground + (USdist + USjet)*x

    Westbound = (df.dLong < 0) & (~df.DestOverseas)
    Eastbound = (df.dLong > 0) & (~df.DestOverseas)
    Pacific = df.DestOverseas

    #Plot Dist vs SchTime. Color Eastbound flights red and Westbound flights blue.
    fig, ax = plt.subplots()
    ax.plot(df.Distance[Eastbound], df.SchTime[Eastbound], 'r.', ms = 2)
    ax.plot(df.Distance[Westbound], df.SchTime[Westbound], 'b.', ms = 2)
    ax.plot(df.Distance[Pacific], df.SchTime[Pacific], 'g.', ms = 2)
    ax.plot(x, Pacy_west, 'k--')
    ax.plot(x, USy_east, 'k')
    ax.plot(x, USy_west, 'k')
    ax.set_title('Flights in %s %d' %(MonthDict[month], year))
    ax.set_xlabel('Distance (miles)')
    ax.set_ylabel('Scheduled Flight Time')
    
    #Make legend.
    red_patch = mpatches.Patch(color='red', label='Eastbound')
    blue_patch = mpatches.Patch(color='blue', label='Westbound')
    green_patch = mpatches.Patch(color='green', label='Pacific Dest.')
    black_dash = mlines.Line2D([], [], color='black', label='Pacific Regression', ls='--')
    black_line = mlines.Line2D([], [], color='black', label='US Regression')
    lines = [red_patch, blue_patch, green_patch, black_dash, black_line]
    labels = [line.get_label() for line in lines]
    plt.legend(lines, labels, loc='upper left')
    fig.savefig('%d_%d.jpg' %(year, month))


def PlotError(year, month, df=pd.DataFrame({}), title='Regression Error'):
    """Plot the error from the linear regression in a histogram."""
    if(len(df) == 0):
        df = getJetstream(year, month)
    
    params = Regression(year, month, df)[0]

    #Determine Error.
    df['Error'] = df.SchTime - (params[0]*df.Distance + params[1]*df.Jetstream + params[2])

    #Plot the histograms.
    fig, ax = plt.subplots()
    ax.hist(df.Error, 50)
    ax.set_xlabel('Error (min)', fontsize=20)
    ax.set_ylabel('Freq', fontsize=20)
    ax.set_title(('%s %d ' + title) %(MonthDict[month], year), fontsize=20)
    fig.savefig('%s.jpg' %title)

    #Output flights that have Error < -25.
    LL = pd.read_csv('LatLong.csv')
    df = df[df.Error < -25]
    Errors = pd.DataFrame({'OriginAirportId':df.OriginAirportId, 'DestAirportId':df.DestAirportId})
    Errors.drop_duplicates(inplace=True)
    Errors.index = range(len(Errors))

    Errors = Errors.merge(LL, left_on = 'OriginAirportId', right_on='AirportId')
    Errors.rename(columns={'AirportName':'OriginAirport'}, inplace=True)
    Errors = Errors.merge(LL, left_on = 'DestAirportId', right_on='AirportId')
    Errors.rename(columns={'AirportName':'DestAirport'}, inplace=True)
    for x in Errors.index:
        print "%s --> %s" %(Errors.OriginAirport[x], Errors.DestAirport[x])


def PlotRegressionCoef():
    """Plot regression coefficients for Pacific and non-Pacific flights from Oct 1987 to Dec 2015.
    Also, count number of errors > 20 min."""
    [PacPlane, PacJet, PacGround, PacFit, USPlane, USJet, USGround, USFit, Time] = [[] for i in range(9)]
    [Pacflights, USflights, PacError, USError] = [0]*4

    for year in range(2011, 2016):
        if(year == 1987):
            startmonth = 10
        else:
            startmonth = 1
        for month in range(startmonth, 13):
            print year, month
            #Get Pacific and non-Pacific flights, and calculate Regression coefficients and fit.
            df = getJetstream(year, month)
            df = getPacific(df)
            dfPac = df[df.DestOverseas]
            dfUS = df[~df.DestOverseas]
            (Pacparams, Pacscore, PacSE) = Regression(year, month, dfPac)
            (USparams, USscore, US_SE) = Regression(year, month, dfUS)

            #Put this data into lists.
            PacPlane.append(60/Pacparams[0])
            PacJet.append(60/Pacparams[0] - 60/(Pacparams[0] + Pacparams[1]))
            PacGround.append(Pacparams[2])
            PacFit.append(Pacscore)

            USPlane.append(60/USparams[0])
            USJet.append(60/USparams[0] - 60/(USparams[0] + USparams[1]))
            USGround.append(USparams[2])
            USFit.append(USscore)
            Time.append(DatetoDays('%d-%d-01' %(year, month)))

            #Calculate and enumerate error.
            dfPac['Error'] = dfPac.SchTime - (Pacparams[0]*dfPac.Distance + Pacparams[1]*dfPac.Jetstream + Pacparams[2])
            dfUS['Error'] = dfUS.SchTime - (USparams[0]*dfUS.Distance + USparams[1]*dfUS.Jetstream + USparams[2])
            Pacflights += len(dfPac)
            PacError += len(dfPac[np.abs(dfPac.Error) > 20])
            USflights += len(dfUS)
            USError += len(dfUS[np.abs(dfUS.Error) > 20])

    print "Pacific Errors: %d out of %d" %(PacError, Pacflights)
    print "Non-Pacific Errors: %d out of %d" %(USError, USflights)

    Coeff = [[PacPlane, PacJet, PacGround, PacFit], [USPlane, USJet, USGround, USFit]]
    PlotDict = {0:('Scheduled Plane Speed', 'mph', 'Plane.jpg'), 
    1:('Jetstream Effect', 'mph', 'Jetstream.jpg'), 
    2:('Ground Time', 'min', 'Ground.jpg'), 
    3:('Correlation Coefficient', 'R^2', 'Fit.jpg')}

    #Plot Regression Coefficients
    for i in range(2):
        for j in range(4):
            if(i == 0):
                prefix = 'Pacific'
            else:
                prefix = 'US'
            fig, ax = plt.subplots()
            ax.plot(Time, Coeff[i][j])
            labels = range(1988, 2017)
            ax.set_xlim(-100, 10228)
            ax.set_xticks(np.arange(0, 10228, 365.25))
            ax.set_xticklabels(labels, rotation='vertical')
            ax.set_xlabel('Year')
            ax.set_title(prefix + ' ' + PlotDict[j][0])
            ax.set_ylabel(PlotDict[j][1])
            fig.savefig(prefix+PlotDict[j][2])


def main():
    year = 2015
    month = 1
    PlotSchTime(12478, 12892, 'AA') #Plot sch flight time from JFK to LAX
    PlotSchTime(12892, 12478, 'AA') #Plot sch flight time from LAX to JFK
    
    df = getJetstream(year, month)  #Get flight info.
    PlotDistSchTime(year, month, df)    #Plot distance vs sch flight time for Jan. 2015.
    print Regression(year, month, df)   #Print regression coeff, r^2, standard error.
    PlotError(year, month, df, 'Regression Error')   #Plot error from Regression.
    
    dfPac = getPacific(df)      #Get info whether destination is in the Pacific.
    PlotRegression(year, month, df)     #Separate flights by Pacific Destination, regress, plot.
    print Regression(year, month, dfPac[dfPac.DestOverseas])    #Regression for Pacific dest flights.
    PlotError(year, month, dfPac[dfPac.DestOverseas], 'Pacific Regression Error')
    print Regression(year, month, dfPac[~dfPac.DestOverseas])   #Regression for non-Pacific dest flights.
    PlotError(year, month, dfPac[~dfPac.DestOverseas], 'US Regression Error')

    PlotRegressionCoef()    #Plot monthly US and Pacific regression coefficients from Oct 1987 - Dec. 2015.
    

if __name__ == '__main__':
    sys.exit(main())
