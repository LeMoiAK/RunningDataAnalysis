# -*- coding: utf-8 -*-
"""
Shows the process of reading a FIT file into a pandas DataFrame when we are 
not interested in all the right units, names, etc. We just want the data.

Created on Mon Jul 17 21:52:24 2023

@author: LeMoiAK
"""

# Imports the ActivityImporter class
import Utilities.Functions as Utils
from Utilities.ActivityImporter import ActivityImporter

# Necessqry just for plotting
import plotly.express as px
import plotly.io as pio
pio.renderers.default= 'browser' # Set to render plots in a browser

# Sets the file path relative to the data folder
filePath = Utils.getDataPath() + "\\11566503738_ACTIVITY.fit"
print(filePath)

# Read the FIT file into a DataFrame
df = ActivityImporter.loadDataFromFitFile(filePath)

# Do some conversions that might be useful
df['speed_kph'] = df['speed'] * 3.6
df['time'] = (df['timestamp'] - df['timestamp'].iloc[0]).apply(lambda x: x.total_seconds())
(df['position_lat_deg'], df['position_long_deg']) = Utils.SemiToDeg(df['position_lat'], df['position_long'])

# Plots the position on a map with speed as color
fig = px.scatter_geo(df, lat='position_lat_deg', lon='position_long_deg', color="speed_kph", hover_name="speed_kph", scope="europe")
fig.update_layout(title = 'Position', title_x= 0.5)
fig.show()