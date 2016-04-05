#!/usr/bin/env python
"""Estimate parameters of models that predict SchTime using available info: SchDep, SchArr, Carrier, 
    Date, Distance, Origin and Dest coordinates."""

import numpy as np
import pandas as pd
from sklearn import linear_model
from analysis.filter import get_jetstream

def regression(year, month, df):
    """OLS regression modeling SchTime with Distance and Jetstream info."""
    #Obtain relevant dataframe and calculate Jetstream.
    if(len(df) == 0):
        df = get_jetstream(year, month)

    #Run OLS regression.
    x = df[['Distance', 'Jetstream']]
    y = df['SchTime']
    ols = linear_model.LinearRegression()
    ols.fit(x,y)
    params = list(ols.coef_)
    params.append(ols.intercept_)
    score = ols.score(x,y)

    #Calculate standard error.
    mean_sqerr = np.mean((y - ols.predict(x).T)**2)    #Mean Square Error.
    x['ones'] = 1
    stderror = np.sqrt(mean_sqerr * np.diag(np.linalg.pinv(np.dot(x.T, x))))
    return (params, score, stderror)
