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
# Standard libraries
import numpy as np
import datetime

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

# These HR zones are required for later use
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
# gdi = GarminDataImporter(folderPath, importActivities=True,
#                                      activityImporterOptions=dict(
#                                         importWeather=False,
#                                         customHRzones=StravaHRzones,
#                                         customPaceZones=StravaPaceZones
#                                         ) ) # To import from a Garmin data folder

# Evolution of best pace vs time of effort
actp.bestEffortPerTimeEvolutionPlot(gdi)

# Same graph but distance rather than time
actp.bestEffortPerDistanceEvolutionPlot(gdi)


# -------------------------------------------------------------------------------------------------------
#%% SHOW DISTRIBUTION OF TIME SPENT IN EACH HR ZONE EACH MONTH
# Obtain metrics from Data Importer
metricsDF = gdi.activityMetricsDF
# Then create the plot
actp.plotDistributionHRzones(metricsDF, StravaHRzones, "HR_Custom_Time_")

# Same but with Garmin zones already computed in the metrics.
# That means the bounds used to calculate the time spent in each zone as saved
# in the file may not correspond with the zones indicated below. The definition
# of the zones has evolved over time.
GarminHRzones = dict(
    Zone_0= [0, 99],
    Zone_1= [100, 118],
    Zone_2= [119, 138],
    Zone_3= [139, 158],
    Zone_4= [159, 178],
    Zone_5= [179, 198],
    Zone_6= [199, np.inf]
    )

actp.plotDistributionHRzones(metricsDF, GarminHRzones, "HR_Time_")

# -------------------------------------------------------------------------------------------------------
#%% SHOW DISTRIBUTION OF TIME SPENT IN EACH PACE ZONE EACH MONTH
# Then create the plot
actp.plotDistributionPaceZones(metricsDF, StravaPaceZones, "PaceZone_Time_")

# -------------------------------------------------------------------------------------------------------
#%% More graphs and analyses incoming
# For instance related to HR

