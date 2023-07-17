# RunningDataAnalysis
Framework to import running data, primarily from the fit format from Garmin. Then produce insightful metrics and analyses.

## Install
This requires the Garmin fit SDK. Install using pip: ```pip install garmin-fit-sdk```  
More information can be found here: https://developer.garmin.com/fit/example-projects/python/

Once you cloned the project, you must add a text file containing the path to the folder containing your data. Add that file as ```Utilities/dataFolderPath.txt```

This also requires the meteostat python module. Install using pip: ```pip install meteostat```  