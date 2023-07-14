# -*- coding: utf-8 -*-
"""
Script to test the ActivityPlotter to compare activities.

Created on Fri Jul 14 22:34:13 2023

@author: LeMoiAK
"""

import Utilities.Functions as Utils
from Utilities.ActivityImporter import ActivityImporter
from Utilities.ActivityPlotter import ActivityPlotter as actp

#%% Import the data from several activities
filePathList = [Utils.getDataPath() + "\\10765570476_ACTIVITY.fit", 
                Utils.getDataPath() + "\\11259017918_ACTIVITY.fit", 
                Utils.getDataPath() + "\\11329404102_ACTIVITY.fit"
                ]

namesList = ["Activity 1 10765570476",
             "Activity 2 11259017918",
             "Activity 3 11329404102"
             ]

activityList = [ActivityImporter(thisPath) for thisPath in filePathList] # Get Activities
metrics = [thisAct.exportUsefulMetrics() for thisAct in activityList] # Get Metrics
df5kmList = [thisAct.extractBestEffortTimeSeries('5km') for thisAct in activityList] # Get 5k dataFrames

#%% Now plots the data
actp.effortComparePlot(df5kmList, namesList, title="Comparison of 5km races")
