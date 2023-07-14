# -*- coding: utf-8 -*-
"""
ActivityPlotter class
Class to plot data from dataFrames obtained from activities and best efforts.

Created on Fri Jul 14 22:32:35 2023

@author: LeMoiAK
"""

#%% Import necessary libraries
import Utilities.Functions as Utils
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.io as pio
#pio.renderers.default = 'svg'
pio.renderers.default= 'browser' # Set to render plots in a browser
import pandas as pd
import numpy as np

#%% Define the ActivityPlotter class
class ActivityPlotter:
    """
    This class contains static methods meant to plot data in a nice and standard way.
    """
    
    @staticmethod
    def effortComparePlot(dfList, namesList, title="", baselineIdx=0):
        """
        Standard plot to compare two best efforts on a single standard plot.
        Shows pace, time difference, heart rate and elevation.
        
        dfList contains all dataFrames of activities to compare.
        namesList contains their respective names for legends.
        title is an optional title for the graph.
        baselineIdx is the index of the baseline activity for time delta.
        """
        
        # Interpolates all dataFrames into the distance of the first one
        # For the first one, it is just a copy. But others need to be recreated
        # because they potentially have a different size
        Nact = len(dfList)
        dfInterp = []
        endDistArray = [thisDF['distanceEffort'].iloc[-1] for thisDF in dfList] # Get list of distances
        endDist = min(endDistArray)
        xDistanceArray = np.arange(0, endDist, 1.0)
        if xDistanceArray[-1] < endDist:
            xDistanceArray = np.append(xDistanceArray, endDist)
        for idx in np.arange(Nact):
            interp_Time = np.interp(xDistanceArray, dfList[idx]["distanceEffort"], dfList[idx]["timeEffort"])
            interp_Speed = np.interp(xDistanceArray, dfList[idx]["distanceEffort"], dfList[idx]["speed"])
            interp_HeartRate = np.interp(xDistanceArray, dfList[idx]["distanceEffort"], dfList[idx]["heart_rate"])
            dfInterp.append( pd.DataFrame(data = {'distance': xDistanceArray, \
                                                  'time': interp_Time,
                                                  'speed': interp_Speed,
                                                  'speed_kph': interp_Speed*3.6,
                                                  'pace': Utils.speedToPace(interp_Speed),
                                                  'heart_rate': interp_HeartRate
                                                } ))
        
        # Calculate Tdiff
        for idx in np.arange(Nact):
            dfInterp[idx]['timeDelta'] = dfInterp[idx]['time'] - dfInterp[baselineIdx]['time']
        
        # Plot the graphs
        fig = make_subplots(rows=3, cols=1)
        # Time delta
        for idx in np.arange(Nact):
            fig.add_scatter(x=dfInterp[idx]['distance'], y=dfInterp[idx]['timeDelta'], mode='lines', name=namesList[idx], row=1, col=1)
        fig.update_layout(
           title = title,
           xaxis_title = "Distance",
           yaxis_title = "Time Delta (s)",
           legend_title = "Activity Name"
        )
        # Pace
        for idx in np.arange(Nact):
            fig.add_scatter(x=dfInterp[idx]['distance'], y=dfInterp[idx]['pace'], mode='lines', row=2, col=1)
        fig.update_layout(
           title = title,
           xaxis_title = "Distance",
           yaxis_title = "Pace (min/km)",
           legend_title = "Activity Name"
        )
        # Heart Rate
        for idx in np.arange(Nact):
            fig.add_scatter(x=dfInterp[idx]['distance'], y=dfInterp[idx]['heart_rate'], mode='lines', row=3, col=1)
        fig.update_layout(
           title = title,
           xaxis_title = "Distance",
           yaxis_title = "Heart Rate (bpm)",
           legend_title = "Activity Name"
        )
        fig.show()
        
        # Manual test
        trace1 = go.Scatter(
            x=[0, 1, 2],
            y=[10, 11, 12]
        )
        trace2 = go.Scatter(
            x=[2, 3, 4],
            y=[100, 110, 120],
            yaxis="y2"
        )
        trace3 = go.Scatter(
            x=[3, 4, 5],
            y=[1000, 1100, 1200],
            yaxis="y3"
        )
        data = [trace1, trace2, trace3]
        layout = go.Layout(
            yaxis=dict(
                domain=[0, 0.33],
            ),
            legend=dict(
                traceorder="reversed"
            ),
            yaxis2=dict(
                domain=[0.33, 0.66]
            ),
            yaxis3=dict(
                domain=[0.66, 1]
            )
        )
        fig = go.Figure(data=data, layout=layout)
        fig.show()