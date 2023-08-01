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

folderPath = Utils.getDataPath() + "\\WatchOffloadClean"
print(folderPath)

#%% Try GarminDataImporter
StravaHRzones = dict(
    Zone_1_Endurance= [0, 129],
    Zone_2_Moderate= [130, 161],
    Zone_3_Tempo= [162, 177],
    Zone_4_Threshold= [178, 195],
    Zone_5_Anaerobic= [194, np.inf]
    )

gdi = WatchOffloadDataImporter(folderPath, importActivities=True, activityImporterOptions=dict(importWeather=False, customHRzones=StravaHRzones) )

#%% Create Heat Map of training pace and Heart Rate
# Get Total DataFrame
dfTotal = gdi.exportAllActivitiesData()
# Filter to normal paces under 8mins/km
dfTotal = dfTotal[dfTotal['pace'] < np.datetime64('1970-01-01 00:08:00')]

#%% Create a density plot
import plotly.express as px
import pandas as pd

#%%
# Need to resolve the issue that some samples are longer times than others
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
fig.show()