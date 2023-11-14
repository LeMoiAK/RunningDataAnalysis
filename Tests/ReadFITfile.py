# Script to test the import of a .fit file using the Garmin sdk
import Utilities.Functions as Utils
from Utilities.ActivityImporter import ActivityImporter
import numpy as np
import pandas as pd
import seaborn as sns
import datetime
import matplotlib.pyplot as plt
from Utilities.ActivityPlotter import ActivityPlotter as actp # To create standard plots

###############################################################################
#%% Test class
# filePath = Utils.getDataPath() + "\\11329404102_ACTIVITY.fit"
filePath = Utils.getDataPath() + "\\WatchOffloadClean\\2023_10_15-08_39_48_running.fit"
print(filePath)

StravaHRzones = dict(
    Zone_1_Endurance= [0, 129],
    Zone_2_Moderate= [130, 161],
    Zone_3_Tempo= [162, 177],
    Zone_4_Threshold= [178, 193],
    Zone_5_Anaerobic= [194, np.inf]
    )

StravaPaceZones = dict(
    Zone_1_Active_Recovery= [datetime.datetime(1970, 1, 1, 0, 6, 15), datetime.datetime(1970, 1, 1, 2, 0, 0)],
    Zone_2_Endurance= [datetime.datetime(1970, 1, 1, 0, 5, 23), datetime.datetime(1970, 1, 1, 0, 6, 15)],
    Zone_3_Tempo= [datetime.datetime(1970, 1, 1, 0, 4, 50), datetime.datetime(1970, 1, 1, 0, 5, 23)],
    Zone_4_Threshold= [datetime.datetime(1970, 1, 1, 0, 4, 31), datetime.datetime(1970, 1, 1, 0, 4, 50)],
    Zone_5_VO2max= [datetime.datetime(1970, 1, 1, 0, 4, 15), datetime.datetime(1970, 1, 1, 0, 4, 31)],
    Zone_6_Anaerobic= [datetime.datetime(1970, 1, 1, 0, 0, 0), datetime.datetime(1970, 1, 1, 0, 4, 15)]
    )

actImp = ActivityImporter(filePath, importWeather=False, customHRzones=StravaHRzones, customPaceZones=StravaPaceZones)
metrics = actImp.exportUsefulMetrics()

# Plot the pace graph to check
actImp.data['pace'].plot(ylim=(datetime.datetime(1970, 1, 1, 00, 7), min(actImp.data['pace']) - datetime.timedelta(seconds=30)))

#%% Check the altitude
yAlt = actImp.data['altitude'].values
yAltDiff = np.diff(yAlt)
yAscent = np.sum(yAltDiff[yAltDiff >= 0.0])
yDescent = np.sum(yAltDiff[yAltDiff < 0.0])
# Altitude is wrong, there is some level of correction happening when the run is processed by Garmin

#%% Check the Best Effort subset
df5km = actImp.extractBestEffortTimeSeries('5km')
df5kmPacing = ActivityImporter.createDFgivenPace(np.array([5.0e3]), np.array([np.datetime64('1970-01-01 00:04:30')]) )

# Now plots the comparison plot
actp.effortComparePlot([df5km, df5kmPacing], ['Random 5k', '04:30 pace 5k'], graphTitle="Comparison of 5km pacing")

#%% Create Graph of best pace vs time
x = np.array(actImp.bestEffortData['Time_Times'])
y = np.array(actImp.bestEffortData['Time_Paces'])
idxFilter = np.array(actImp.bestEffortData['Time_Paces']) < np.datetime64('1970-01-01 00:30:00')
x = x[idxFilter]
y = y[idxFilter]

plt.Figure()
plt.plot(x/60.0, y, marker='.')
plt.xlabel('Effort Time (mins)')
plt.ylabel('Pace for that effort (min/km)')
plt.gca().invert_yaxis()
plt.grid()
plt.show()

#%% Test zones with and without resampling
actImp_Resampled = ActivityImporter(filePath, importWeather=False, customHRzones=StravaHRzones, resampleDataTo1s=True, customPaceZones=StravaPaceZones)
actImp_Original  = ActivityImporter(filePath, importWeather=False, customHRzones=StravaHRzones, resampleDataTo1s=False, customPaceZones=StravaPaceZones)
timeInHRzones_Resampled = actImp_Resampled.timeInCustomHRzones
timeInHRzones_Original = actImp_Original.timeInCustomHRzones
timeInPaceZones_Resampled = actImp_Resampled.timeInPaceZones
timeInPaceZones_Original = actImp_Original.timeInPaceZones
