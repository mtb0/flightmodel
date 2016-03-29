
getFiles.py —> getDistfromFiles.py -> cleanData.py —> Analysis.py

getFiles.py downloads 13.6G of data from the Bureau of Transportation Statistics (http://tsdata.bts.gov/).  The location of the latitude/longitude and flight data has changed in the past and may change in the future.  Files are downloaded to the current directory and labeled 'LatLong.csv’ and 'year_month.csv’.

getDistfromFiles.py checks and isolates distance information from the downloaded files.  It produces 'distance.csv’ containing distance between origin and destination airports by 7-digit AirportId.

cleanData.py cleans all 'year_month.csv' using the procedure written in section 3 of the report.  It only attempts to verify/determine the scheduled departure, arrival, and flight times columns and no other column.  It then drops the disregarded columns of the existing file, and OVERWRITES it.  The size of the cleaned data is 7.85G. If you have the storage, you may wish to not overwrite the downloaded data.

Analysis.py performs the analysis and plots for the intro and section 2 of the report.  The data from section 1 was produced through executing the queries in BigQuery.txt, using the Google BigQuery web interface.  The tables were downloaded and plotted independently.  An automated script to produce these graphs may replace the text document in the future.