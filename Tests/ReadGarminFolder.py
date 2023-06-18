# -*- coding: utf-8 -*-
"""
Script to test the import of a whole Garmin Data Folder. Helps to develop the associated class.
Created on Sun Jun 18 18:05:44 2023

@author: LeMoiAK
"""

import Utilities.Functions as Utils
import matplotlib.pyplot as plt
import pandas as pd
import glob
from Utilities.GarminDataImporter import GarminDataImporter

folderPath = Utils.getDataPath() + "\\2023_04_03_Complete"
print(folderPath)

#%% Try GarminDataImporter
gdi = GarminDataImporter(folderPath)

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
