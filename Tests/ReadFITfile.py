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
start = metrics['Metric_StartTime'].replace(tzinfo=None)
end = metrics['Metric_EndTime'].replace(tzinfo=None)
end = end.replace(second=0, microsecond=0, minute=0, hour=end.hour+1) # Ensure there's at least an hour (but loss of precision)
location = Point(metrics['Metric_StartPosition_Lat'], metrics['Metric_StartPosition_Long'], actImp.data['altitude'].iloc[0])

# Get data
weatherData = Hourly(location, start, end, origTZinfo)
weatherData = weatherData.fetch()

weatherConditions = {1: "Clear", 2: "Fair", 3: "Cloudy", 4: "Overcast", 5: "Fog", 6: "Freezing Fog", 7: "Light Rain", 8: "Rain", 9: "Heavy Rain",
                     10: "Freezing Rain", 11: "Heavy Freezing Rain", 12: "Sleet", 13: "Heavy Sleet", 14: "Light Snowfall", 15: "Snowfall",
                     16: "Heavy Snowfall", 17: "Rain Shower", 18: "Heavy Rain Shower", 19: "Sleet Shower", 20: "Heavy Sleet Shower",
                     21: "Snow Shower", 22: "Heavy Snow Shower", 23: "Lightning", 24: "Hail", 25: "Thunderstorm", 26: "Heavy Thunderstorm", 27: "Storm"}

weatherMetrics = dict()
weatherMetrics['Temperature_degC'] = weatherData['temp'].mean()
weatherMetrics['Rain_mm'] = weatherData['prcp'].mean()
weatherMetrics['WindSpeed_kph'] = weatherData['wspd'].mean()
weatherMetrics['WindGustSpeed_kph'] = weatherData['wpgt'].mean()
weatherMetrics['Condition'] = weatherData['coco'].map(weatherConditions).iloc[0]
