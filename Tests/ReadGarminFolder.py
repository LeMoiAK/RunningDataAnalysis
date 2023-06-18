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
import json
import datetime

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

#%% Plot paces for each record
plt.figure()
gdi.personalRecord['1km']['Pace'].plot(legend='1km')
gdi.personalRecord['5km']['Pace'].plot(legend='5km')
gdi.personalRecord['10km']['Pace'].plot(legend='10km')
gdi.personalRecord['HM']['Pace'].plot(legend='HM')
plt.grid(True, 'both')
plt.xlabel('Date')
plt.ylabel('Record Pace')
plt.legend(['1k', '5k', '10k', 'Half'])
plt.title('Record Pace Evolution Per Distance')

#%% Create a plot comparing race predictions and Personal records for each distance
plt.figure()
gdi.df_RacePred['raceTime5K_Pace'].plot()
plt.scatter(gdi.personalRecord['5km'].index, gdi.personalRecord['5km']['Pace'])
gdi.df_RacePred['raceTime10K_Pace'].plot()
plt.scatter(gdi.personalRecord['10km'].index, gdi.personalRecord['10km']['Pace'])
gdi.df_RacePred['raceTimeHalf_Pace'].plot()
plt.scatter(gdi.personalRecord['HM'].index, gdi.personalRecord['HM']['Pace'])
plt.xlabel('Date')
plt.ylabel('Pace Prediction')
plt.legend(['5k Prediction', '5k Real', '10k Prediction', '10k Real', 'Half Prediction', 'Half Real'])
plt.grid(True)
plt.title('Race Pace Prediction vs Personal Records')