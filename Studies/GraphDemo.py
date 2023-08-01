# -*- coding: utf-8 -*-
"""
Contains demonstrations of all graphs that can be created. Kind of a showcase
of all functionalities.

Created on Tue Aug  1 18:04:25 2023

@author: LeMoiAK
"""

#%% Import modules
# Custom Modules to load data
import Utilities.Functions as Utils
from Utilities.GarminDataImporter import GarminDataImporter,WatchOffloadDataImporter # To read entire folders
from Utilities.ActivityImporter import ActivityImporter # To read a single activity
from Utilities.ActivityPlotter import ActivityPlotter as actp # To create standard plots

# -------------------------------------------------------------------------------------------------------
#%% COMPARE MULTIPLE SIMILAR ACTIVITIES
# Import the data from several activities
filePathList = [Utils.getDataPath() + "\\WatchOffloadClean\\2023_04_01-10_08_23_running.fit", 
                Utils.getDataPath() + "\\WatchOffloadClean\\2023_06_10-08_01_34_running.fit"
                ]

namesList = ["Training 01/04/2023",
             "Parkrun 10/06/2023"
             ]
# Import the data
activityList = [ActivityImporter(thisPath) for thisPath in filePathList] # Get Activities
metrics = [thisAct.exportUsefulMetrics() for thisAct in activityList] # Get Metrics
df5kmList = [thisAct.extractBestEffortTimeSeries('5km') for thisAct in activityList] # Get 5k dataFrames

# Now plots the comparison plot
actp.effortComparePlot(df5kmList, namesList, graphTitle="Comparison of two best 5km PB")

# -------------------------------------------------------------------------------------------------------
#%% SHOW EVOLUTION OF BEST PACE VS TIME AND DISTANCE
# Import the data from the Watch Offload folder
# Could be done with the Garmin folder as well

folderPath = Utils.getDataPath() + "\\WatchOffloadClean"
gdi = WatchOffloadDataImporter(folderPath, importActivities=True, activityImporterOptions=dict(importWeather=False) ) # To import from a watch offload
# gdi = GarminDataImporter(folderPath, importActivities=True, activityImporterOptions=dict(importWeather=False) ) # To import from a Garmin data folder

# Evolution of best pace vs time of effort
actp.bestEffortPerTimeEvolutionPlot(gdi)

# Same graph but distance rather than time
actp.bestEffortPerDistanceEvolutionPlot(gdi)

# -------------------------------------------------------------------------------------------------------
#%% More graphs and analyses incoming
# For instance related to HR
