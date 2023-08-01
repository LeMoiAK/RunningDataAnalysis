# -*- coding: utf-8 -*-
"""
Script to filter the watch offload folder to runs only, rename them with a better
name with date, and copy them to another folder. This uses static methods from
the GarminDataImporter StandardImporter class.


Created on Tue Aug  1 17:44:01 2023

@author: LeMoiAK
"""

#%% Import required functions and modules
from Utilities.GarminDataImporter import StandardDataImporter
import Utilities.Functions as Utils

#%% Set folders then run the function
# - Activities offloaded manually from the watch
sourceFolder = Utils.getDataPath() + "\\WatchOffloadRaw"
destinationFolder = Utils.getDataPath() + "\\WatchOffloadClean"
# - To get activities that have not been offloaded from the watch in the past
# sourceFolder = Utils.getDataPath() + "\\2023_06_01_Complete\\DI_CONNECT\\DI-Connect-Uploaded-Files"
# destinationFolder = Utils.getDataPath() + "\\GarminFolderClean"

renamedAndFilteredFiles = StandardDataImporter.filterToRunOnlyAndRenameFitFiles(sourceFolder, destinationFolder)
print('\n' + str(len(renamedAndFilteredFiles)) + " files have been filtered and copied to the destination folder")