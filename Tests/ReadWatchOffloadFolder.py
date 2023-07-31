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

folderPath = Utils.getDataPath() + "\\WatchOffloadRaw"
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