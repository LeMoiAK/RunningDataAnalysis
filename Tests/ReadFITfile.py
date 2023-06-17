# Script to test the import of a .fit file using the Garmin sdk
import Utilities.Functions as Utils
from Utilities.ActivityImporter import ActivityImporter
import numpy as np
import pandas as pd
import seaborn as sns

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