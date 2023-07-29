# -*- coding: utf-8 -*-
"""
Try to understand the Relative Effort metric calculated by Strava.
After some research, it seems it is based solely on Heart Rate and time spent
in each HR zone.

Created on Fri Jul 28 21:21:59 2023

@author: LeMoiAK
"""

#%% import required libraries
import pandas as pd
import numpy as np

from Utilities.GarminDataImporter import GarminDataImporter,WatchOffloadDataImporter
from Utilities.ActivityImporter import ActivityImporter
from Utilities.ActivityPlotter import ActivityPlotter as actp
import Utilities.Functions as Utils

#%% Import the run data to get the HR metrics
folderPath = Utils.getDataPath() + "\\WatchOffloadRaw"
print(folderPath)
gdi = WatchOffloadDataImporter(folderPath, importActivities=True)
# Then get the metrics from these runs
metricsDF = gdi.activityMetricsDF

#%% Import the metrics from Strava
stravaActivitiesPath = Utils.getDataPath() + "\\2023_07_28_Strava\\activities.csv"
# Real only the potentially interesting columns
stravaDF = pd.read_csv(stravaActivitiesPath, usecols = ['Activity Date', 'Activity Name', 'Activity Type', 'Elapsed Time', 
                                                        'Max Heart Rate', 'Relative Effort', 'Moving Time', 'Distance', 
                                                        'Average Speed', 'Average Heart Rate', 'Calories'])

# Filter down to runs with Relative Effort available only
stravaDF.dropna(inplace=True) # Remove NaN, for instance activities without RE
stravaDF['Activity Date'] = pd.to_datetime(stravaDF['Activity Date'], utc=True)
stravaDF = stravaDF[ (stravaDF['Activity Type'] == 'Run') ]
stravaDF_light = stravaDF[['Activity Date', 'Relative Effort']].copy()
stravaDF_light['Metric_StartTime'] = stravaDF_light['Activity Date']

#%% Merge Metrics table together
metricsDF_light = metricsDF[['Metric_StartTime', 'Metric_TotalTimerTime', 'Metric_TotalDistance', 'HR_Time_Zone_0', 'HR_Time_Zone_1', 'HR_Time_Zone_2', 'HR_Time_Zone_3', 'HR_Time_Zone_4', 'HR_Time_Zone_5', 'HR_Time_Zone_6' ]]

fullDF = pd.merge(metricsDF_light, stravaDF_light, on='Metric_StartTime', how='inner')

#%% Create linear model of RE as a function of time in each zone