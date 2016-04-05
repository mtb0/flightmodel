##About

Flightmodel is a collection of scripts to download, clean, and analyze flight data from the Bureau of Transportation Statistics. Currently, it models scheduled flight times using flight distance, bearing of the plane, and coordinates of the destination airport, and quantifies the effect of various factors on scheduled flight times.  Estimated parameters of the model reflect physical observations, such as seasonal variation in the jet stream.  The results of the analysis and methodology is written in `AirlineData.pdf`.

###Directory structure
    src/  
    ├── analysis  
    ├── clean  
    ├── download  
    └── drivers  

To run a script from the source directories:

    export PYTHONPATH=<flightmodel>/src:$PYTHONPATH


###Structure

`GetCleanDriver.py` --> `AnalysisDriver.py`

`GetCleanDriver.py` downloads and cleans flight data, and places it within the data directory.  It executes functions contained in the clean and download directories.

  *  `get_files.py` contains functions that download 13.6G of data from the [Bureau of Transportation Statistics](http://tsdata.bts.gov/).  The location of the latitude/longitude and flight data has changed in the past and may change in the future.  Files are downloaded to the data directory and labeled 'LatLong.csv' and 'year_month.csv'.

  *  `get_dist_from_files.py` contains functions that check and isolate distance information from the downloaded files.  It produces 'distance.csv' containing distance between origin and destination airports by 7-digit AirportId.

  *  `cleandata.py` contains functions that cleans all 'year_month.csv' using the procedure written in section 3 of the report.  It only attempts to verify/determine the scheduled departure, arrival, and flight times columns and no other column.  It then drops the disregarded columns of the existing file, and OVERWRITES it.  The size of the cleaned data is 7.85G. If you have the storage, you may wish to not overwrite the downloaded data.


`AnalysisDriver.py` performs the analysis and plots for the intro and section 2 of the report using functions contained in the analysis directory.  It plots scheduled flight times for a specific flight over time, runs and plots regressions and errors, and plots regression coefficients over time.  It places these plots in the graphs directory.

  *  `filter.py` contains functions that calculate new variables from flight data, which can be used in a regression or to filter the data.

  *  `plot.py` contains functions that plots scheduled flight time vs distance and time, regressions and errors, as well as regression coefficients over time.

  *  `regression.py` contains a regresssion function which models scheduled flight times using distance and calculated jetstream information.

The data from section 1 was produced through executing the queries in 'BigQuery.txt', using the Google BigQuery web interface.  The tables were downloaded and plotted independently.  An automated script to produce these graphs may replace the text document in the future.