# -*- coding: utf-8 -*-
"""
Script to study the relationship between heart rate and pace.
Created on Sun Jun 25 18:51:35 2023

@author: LeMoiAK
"""

# Required libraries
import Utilities.Functions as Utils
from Utilities.ActivityImporter import ActivityImporter
import numpy as np
import pandas as pd
import seaborn as sns
import datetime
import matplotlib.pyplot as plt

###############################################################################
#%% Import data
filePath = Utils.getDataPath() + "\\11259017918_ACTIVITY.fit"
print(filePath)

thisAct = ActivityImporter(filePath)

#%% investigate HR vs pace
df = thisAct.data
paceLim=(max(df['pace']), min(df['pace']) - datetime.timedelta(seconds=30))

plt.figure()
sns.scatterplot(data=df, x='heart_rate', y='speed')
# plt.ylim(paceLim)
plt.grid(visible=True)

plt.figure()
plt.plot(df['time'], df['heart_rate'])
plt.grid(visible=True)

#%% Kernel regression smoothing    
xData = df['heart_rate']
yData = df['speed']
xSmooth = np.linspace(140.0, max(xData)+5, 1000)
ySmooth = Utils.kernelRegressionSmoothing(xData, yData, xSmooth, 5)

plt.figure()
plt.scatter(xData, Utils.speedToPace(yData))
plt.plot(xSmooth, Utils.speedToPace(ySmooth))
plt.grid(True)
plt.ylim(paceLim)