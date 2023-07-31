# Script to test the import of a .fit file using the Garmin sdk
import Utilities.Functions as Utils
from Utilities.ActivityImporter import ActivityImporter
import numpy as np
import pandas as pd
import seaborn as sns
import datetime
import matplotlib.pyplot as plt

###############################################################################
#%% Test class
filePath = Utils.getDataPath() + "\\11329404102_ACTIVITY.fit"
print(filePath)

actImp = ActivityImporter(filePath)
metrics = actImp.exportUsefulMetrics()

# Plot the pace graph to check
actImp.data['pace'].plot(ylim=(datetime.datetime(1970, 1, 1, 00, 7), min(actImp.data['pace']) - datetime.timedelta(seconds=30)))

#%% Check the altitude
yAlt = actImp.data['altitude'].values
yAltDiff = np.diff(yAlt)
yAscent = np.sum(yAltDiff[yAltDiff >= 0.0])
yDescent = np.sum(yAltDiff[yAltDiff < 0.0])
# Altitude is wrong, there is some level of correction happening when the run is processed by Garmin

#%% Check the Best Effort subset
df5km = actImp.extractBestEffortTimeSeries('12mins')

#%% Create Graph of best pace vs time
x = np.array(actImp.bestEffortData['Time_Times'])
y = np.array(actImp.bestEffortData['Time_Paces'])
idxFilter = np.array(actImp.bestEffortData['Time_Paces']) < np.datetime64('1970-01-01 00:30:00')
x = x[idxFilter]
y = y[idxFilter]

plt.Figure()
plt.plot(x/60.0, y, marker='.')
plt.xlabel('Effort Time (mins)')
plt.ylabel('Pace for that effort (min/km)')
plt.gca().invert_yaxis()
plt.grid()
plt.show()
