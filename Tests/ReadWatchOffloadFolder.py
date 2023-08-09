# -*- coding: utf-8 -*-
"""
Script to test the WatchOffloadDataImporter.
Rather than loading all files from the zip provided by Garmin, it loads them from
a folder where the user offloads the fit files from their watch directly.
That allows for more periodic updates.

Created on Thu Jul 27 23:44:06 2023

@author: LeMoiAK
"""

from Utilities.GarminDataImporter import GarminDataImporter,WatchOffloadDataImporter
from Utilities.ActivityImporter import ActivityImporter
from Utilities.ActivityPlotter import ActivityPlotter as actp
import Utilities.Functions as Utils
import numpy as np
import datetime

folderPath = Utils.getDataPath() + "\\WatchOffloadClean"
print(folderPath)

#%% Try GarminDataImporter
StravaHRzones = dict(
    Zone_1_Endurance= [0, 129],
    Zone_2_Moderate= [130, 161],
    Zone_3_Tempo= [162, 177],
    Zone_4_Threshold= [178, 193],
    Zone_5_Anaerobic= [194, np.inf]
    )
# Same for pace zones
StravaPaceZones = dict(
    Zone_1_Active_Recovery= [datetime.datetime(1970, 1, 1, 0, 6, 15), datetime.datetime(1970, 1, 1, 2, 0, 0)],
    Zone_2_Endurance= [datetime.datetime(1970, 1, 1, 0, 5, 23), datetime.datetime(1970, 1, 1, 0, 6, 15)],
    Zone_3_Tempo= [datetime.datetime(1970, 1, 1, 0, 4, 50), datetime.datetime(1970, 1, 1, 0, 5, 23)],
    Zone_4_Threshold= [datetime.datetime(1970, 1, 1, 0, 4, 31), datetime.datetime(1970, 1, 1, 0, 4, 50)],
    Zone_5_VO2max= [datetime.datetime(1970, 1, 1, 0, 4, 15), datetime.datetime(1970, 1, 1, 0, 4, 31)],
    Zone_6_Anaerobic= [datetime.datetime(1970, 1, 1, 0, 0, 0), datetime.datetime(1970, 1, 1, 0, 4, 15)]
    )

folderPath = Utils.getDataPath() + "\\WatchOffloadClean"
gdi = WatchOffloadDataImporter(folderPath, importActivities=True,
                                           activityImporterOptions=dict(
                                               importWeather=False,
                                               customHRzones=StravaHRzones,
                                               customPaceZones=StravaPaceZones
                                               ) ) # To import from a watch offload

#%% Create Heat Map of training pace and Heart Rate
# Get Total DataFrame
dfTotal = gdi.exportAllActivitiesData()
# Filter to normal paces under 8mins/km
dfTotal = dfTotal[dfTotal['pace'] < np.datetime64('1970-01-01 00:08:00')]

#%% Create a density plot
import plotly.express as px
import pandas as pd

#%% Plot distribution of times in all runs and compares it to races

# The Plotly express version has lots of issues with filled contours as soon
# as some options like marginal_x or trendline are used
fig = px.density_contour(
    data_frame= dfTotal,
    x= 'heart_rate',
    y= 'pace',
    histnorm='probability',
    range_y= (dfTotal['pace'].max(), dfTotal['pace'].min()),
    title= 'Heart Rate and Pace distribution during training'
    )
fig.update_traces(contours_coloring='fill', colorscale='jet')

# Get metrics to obtain best 5k, 10k, HM and M times and average HR
metricsDF = gdi.activityMetricsDF

# Get index of best 5k, 10k, HM and M
# Assigns better names for each distance
dictDistances = {
    "5km" : "5km",
    "10km" : "10km",
    "HalfMarathon" : "Half-Marathon",
    "FullMarathon" : "Marathon"
    }

for techName, readName in dictDistances.items():
    thisIndex = metricsDF['BestEffort_distance_' + techName + '_time'].idxmin()
    if not(np.isnan(thisIndex)):
        # If a best time is found
        fig.add_scatter(x= [int(metricsDF['BestEffort_distance_' + techName + '_avgHR'].iloc[thisIndex])],
                        y= [metricsDF['BestEffort_distance_' + techName + '_pace'].iloc[thisIndex]],
                        name= readName,
                        marker=dict(
                            color='Red',
                            size=20,
                            line=dict(
                                color='DarkSlateGrey',
                                width=2
                                )
                            )
                        )
        
fig.show()