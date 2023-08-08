# RunningDataAnalysis

Framework to import running data, primarily from the fit format from Garmin. Then produce insightful metrics and analyses.

## Install

This requires the Garmin fit SDK. Install using pip: ```pip install garmin-fit-sdk```  
More information can be found here: <https://developer.garmin.com/fit/example-projects/python/>

Once you cloned the project, you must add a text file containing the path to the folder containing your data. Add that file as ```Utilities/dataFolderPath.txt```

This also requires:

- The meteostat python module. Install using pip: ```pip install meteostat```
- The tqdm module for progress bar. Install using pip: ```pip install tqdm```

## Getting Started

A demo of all importing, analysis, and graphing functionalities can be found in [GraphDemo.py](Studies/GraphDemo.py).  
Change the folder and activity files paths to point to your files; then launch the script. A first graph will quickly appear to compare two 5k runs. It will then take a few minutes to import all activities from the folder with the GarminDataImporter, before all other graphs are displayed.

If you are only interested in obtaining the time series from a FIT file, you can run [SimpleFITread.py](Tests/SimpleFITread.py). It will read the file and export the time series data into a pandas DataFrame without all the overheads and treatments of the running dedicated framework.

## Getting Data

This framework is meant to read FIT files generated by Garmin hardware. These files can be obtained in three ways:

1. For a single activity, go to [Garmin Connect](https://connect.garmin.com/modern/); select an activity; click the settings/cog icon; then "Export Original".
2. For all activities, connect your watch to your computer as a USB storage, then copy all FIT files contained in the Activity folder on your computer. Then launch [CleanWatchOffloadFolder.py](Scripts/CleanWatchOffloadFolder.py) with your own paths to filter and rename the fit files. The FIT files must regularly be offloaded from your watch because older activities get progressively deleted.
3. Request all your data from Garmin. You will receive a zip folder containing your activities, but also your user data and predictions like the "Race Predictor" that you can compare to your actual performance.