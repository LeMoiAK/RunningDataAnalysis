# Script to test the import of a .fit file using the Garmin sdk
import Utilities.Functions as Utils
from Utilities.ActivityImporter import ActivityImporter
import numpy as np
import pandas as pd
import seaborn as sns
import datetime
import matplotlib.pyplot as plt
from meteostat import Point, Hourly

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

#%% Test Weather data import
# Create start end and location from metrics
origTZinfo = metrics['Metric_StartTime'].tzname()
start = metrics['Metric_StartTime'].replace(tzinfo=None)  # Must add function to ensure there is at least one full hour between start and end
end = metrics['Metric_EndTime'].replace(tzinfo=None) # See if more elegant way to deal with timezones rather than removing it
location = Point(metrics['Metric_StartPosition_Lat'], metrics['Metric_StartPosition_Long'], actImp.data['altitude'].iloc[0])

# Get data
data = Hourly(location, start, end, origTZinfo)
data = data.fetch()