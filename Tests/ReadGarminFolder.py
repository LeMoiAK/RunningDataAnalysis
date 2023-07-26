# -*- coding: utf-8 -*-
"""
Script to test the import of a whole Garmin Data Folder. Helps to develop the associated class.
Created on Sun Jun 18 18:05:44 2023

@author: LeMoiAK
"""

import Utilities.Functions as Utils
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import glob
from Utilities.GarminDataImporter import GarminDataImporter
from Utilities.ActivityImporter import ActivityImporter
from Utilities.ActivityPlotter import ActivityPlotter as actp
import json
import datetime
from zipfile import ZipFile
import os

folderPath = Utils.getDataPath() + "\\2023_06_01_Complete"
print(folderPath)

#%% Try GarminDataImporter
gdi = GarminDataImporter(folderPath, importActivities=True)

#%% Plot Race Predictions
gdi.df_RacePred['raceTime5K_Pace'].plot()
gdi.df_RacePred['raceTime10K_Pace'].plot()
gdi.df_RacePred['raceTimeHalf_Pace'].plot()
gdi.df_RacePred['raceTimeMarathon_Pace'].plot()
plt.xlabel('Date')
plt.ylabel('Pace Prediction')
plt.legend(['5k', '10k', 'Half', 'Full'])
plt.grid(True)
plt.title('Race Pace Prediction')

#%% Plot VO2max and MET predictions
plt.figure()
plt.subplot(2, 2, 1)
gdi.df_MetVO2['vo2MaxValue'].plot()
plt.xlabel('Date')
plt.ylabel('VO2 Max')
plt.grid(True)
plt.title('VO2 Max Evolution')

plt.subplot(1, 2, 2)
plt.scatter(gdi.df_MetVO2['maxMet'], gdi.df_MetVO2['vo2MaxValue'])
plt.xlabel('Max MET (mL Oxygen/kg/min)')
plt.ylabel('VO2 Max')
plt.grid(True)
plt.title('VO2 Max vs MET')

plt.subplot(2, 2, 3)
gdi.df_MetVO2['maxMet'].plot()
plt.xlabel('Date')
plt.ylabel('Max MET (mL Oxygen/kg/min)')
plt.grid(True)
plt.title('Max MET Evolution')

#%% Plot paces for each record
plt.figure()
gdi.personalRecord['1km']['Pace'].plot(legend='1km')
gdi.personalRecord['5km']['Pace'].plot(legend='5km')
gdi.personalRecord['10km']['Pace'].plot(legend='10km')
gdi.personalRecord['HM']['Pace'].plot(legend='HM')
plt.grid(True, 'both')
plt.xlabel('Date')
plt.ylabel('Record Pace')
plt.legend(['1k', '5k', '10k', 'Half'])
plt.title('Record Pace Evolution Per Distance')

#%% Create a plot comparing race predictions and Personal records for each distance
plt.figure()
gdi.df_RacePred['raceTime5K_Pace'].plot()
plt.scatter(gdi.personalRecord['5km'].index, gdi.personalRecord['5km']['Pace'])
gdi.df_RacePred['raceTime10K_Pace'].plot()
plt.scatter(gdi.personalRecord['10km'].index, gdi.personalRecord['10km']['Pace'])
gdi.df_RacePred['raceTimeHalf_Pace'].plot()
plt.scatter(gdi.personalRecord['HM'].index, gdi.personalRecord['HM']['Pace'])
plt.xlabel('Date')
plt.ylabel('Pace Prediction')
plt.legend(['5k Prediction', '5k Real', '10k Prediction', '10k Real', 'Half Prediction', 'Half Real'])
plt.grid(True)
plt.title('Race Pace Prediction vs Personal Records')

#%% Look at metrics of activities
metricsDF = gdi.activityMetricsDF

plt.figure()
sns.scatterplot(x='Metric_StartTime',y='Metric_AvgPace',data=metricsDF,hue='Sport_Name')
plt.xlabel('Date')
plt.ylabel('Avg Pace (min/km)')
plt.grid(True)
plt.title('Avg Pace Evolution over Time')

#%% Look at best efforts evolution
plt.figure()
sns.scatterplot(x='Metric_StartTime', y='BestEffort_distance_5km_pace', data=metricsDF)
sns.scatterplot(x='Metric_StartTime', y='BestEffort_distance_10km_pace', data=metricsDF)
sns.scatterplot(x='Metric_StartTime', y='BestEffort_distance_HalfMarathon_pace', data=metricsDF)
plt.xlabel('Date')
plt.ylabel('Best Pace (min/km)')
plt.grid(True)
plt.title('Best Effort Pace Evolution over Time for each distance')
plt.legend(['5km', '10km', 'Half'])

#%% Look at VO2max estimation from the Cooper test
plt.figure()
metricsDF['CooperTest_VO2max_Estimation'] = (22.351 * metricsDF['BestEffort_time_12mins_distance']/1e3) - 11.288
sns.scatterplot(x='Metric_StartTime', y='CooperTest_VO2max_Estimation', data=metricsDF)
plt.xlabel('Date')
plt.ylabel('VO2max estimation (mL/kg/min)')
plt.grid(True)
plt.title('VO2max estimation Evolution over Time')

#%% Test best pace per period
dateRange = pd.date_range(start= metricsDF["Metric_StartTime"].min(), end= metricsDF["Metric_StartTime"].max(), freq = "90D")
dateRange = dateRange.union(pd.date_range(dateRange[-1] + dateRange.freq, periods=1, freq=dateRange.freq))

# Finally plot to give an idea
plt.Figure()
for i in np.arange(1,len(dateRange)):
    periodStart = dateRange[i-1]
    periodEnd   = dateRange[i]
    (timesNamesList, timesValuesArray, bestDistancePerTimeAllActivities, bestPacePerTimeAllActivities) = gdi.getBestPacePerTimeEffortForPeriod( periodStart, periodEnd)
    thisLabel = "From " + str(periodStart.date()) + " to " + str(periodEnd.date())
    plt.plot(timesValuesArray/60.0, bestPacePerTimeAllActivities, marker='.', label= thisLabel)
plt.xlabel('Effort Time (mins)')
plt.ylabel('Pace for that effort (min/km)')
plt.legend()
plt.gca().invert_yaxis()
plt.grid()
plt.show()

#%% Use Activity Plotter to make cleaner graph of best pace evolution
actp.bestEffortPerTimeEvolutionPlot(gdi)

#%% Same graph but distance rather than time
actp.bestEffortPerDistanceEvolutionPlot(gdi)
