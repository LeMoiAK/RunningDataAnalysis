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

folderPath = Utils.getDataPath() + "\\WatchOffloadRaw"
print(folderPath)

#%% Try GarminDataImporter
gdi = WatchOffloadDataImporter(folderPath, importActivities=True)