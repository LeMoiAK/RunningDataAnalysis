# -*- coding: utf-8 -*-
"""
ActivityPlotter class
Class to plot data from dataFrames obtained from activities and best efforts.

Created on Fri Jul 14 22:32:35 2023

@author: LeMoiAK
"""

#%% Import necessary libraries
# Own libraries
import Utilities.Functions as Utils
# Graphing libraries
import plotly.graph_objects as go
import plotly.io as pio
#pio.renderers.default = 'svg'
pio.renderers.default= 'browser' # Set to render plots in a browser
import matplotlib.pylab as pl
# Data libraries
import pandas as pd
import numpy as np
import datetime

#%% Define the ActivityPlotter class
class ActivityPlotter:
    """
    This class contains static methods meant to plot data in a nice and standard way.
    """
    
    @staticmethod
    def effortComparePlot(dfList, namesList, graphTitle="", baselineIdx=0):
        """
        Standard plot to compare two best efforts on a single standard plot.
        Shows pace, time difference, heart rate and elevation.
        
        dfList contains all dataFrames of activities to compare.
        namesList contains their respective names for legends.
        graphTitle is an optional title for the graph.
        baselineIdx is the index of the baseline activity for time delta.
        """
        
        # Make sure distanceEffort is available
        for thisDF in dfList:
            if not('distanceEffort' in thisDF.columns):
                thisDF['distanceEffort'] = thisDF['distance'] - thisDF['distance'].iloc[0]
            if not('timeEffort' in thisDF.columns):
                thisDF['timeEffort'] = thisDF['time'] - thisDF['time'].iloc[0]
        
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
        # Add column with name before merging into single dataFrame        
        for idx in np.arange(Nact):
            dfInterp[idx]['activityName'] = namesList[idx]
        
        # Get list of times then add them to names of activities
        endTimeList = [Utils.format_timedelta(datetime.timedelta(seconds= round(df['time'].iloc[-1]))) for df in dfInterp]
        endTimeDeltaList = [" (" + Utils.format_timedelta(datetime.timedelta(seconds= round(df['timeDelta'].iloc[-1]))) + ")" for df in dfInterp]
        endTimeDeltaList[baselineIdx] = " (baseline)"
        namesListWithTime = [thisName + " - " + thisTimeStr + thisTimeDeltaStr for thisName, thisTimeStr, thisTimeDeltaStr in zip(namesList, endTimeList, endTimeDeltaList)]
                        
        # Manual test
        tracesList = []
        myColors = ["rgba({cr:.0f},{cg:.0f},{cb:.0f},{ca:.0f})".format(cr=c[0]*255,cg=c[1]*255,cb=c[2]*255,ca=c[3]*255) for c in pl.cm.jet(np.linspace(0.0, 1.0, Nact))]
        # Time delta
        for idx in np.arange(Nact):
            tracesList.append(
                    go.Scatter(
                        x= dfInterp[idx]['distance'],
                        y= dfInterp[idx]['timeDelta'],
                        name= namesListWithTime[idx],
                        marker= dict(color= myColors[idx]),
                        legendgroup= namesList[idx],
                        yaxis="y3"
                    )
                )
        # Pace
        for idx in np.arange(Nact):
            tracesList.append(
                    go.Scatter(
                        x= dfInterp[idx]['distance'],
                        y= dfInterp[idx]['pace'],
                        name= namesListWithTime[idx],
                        marker= dict(color= myColors[idx]),
                        legendgroup= namesList[idx],
                        showlegend= False,
                        yaxis="y2"
                    )
                )
        # Pace
        for idx in np.arange(Nact):
            tracesList.append(
                    go.Scatter(
                        x= dfInterp[idx]['distance'],
                        y= dfInterp[idx]['heart_rate'],
                        name= namesListWithTime[idx],
                        marker= dict(color= myColors[idx]),
                        legendgroup= namesList[idx],
                        showlegend= False,
                        yaxis="y"
                    )
                )
        
        # Then create Layout
        layout = go.Layout(
            yaxis=dict(
                domain=[0.00, 0.32],
                title= "Heart Rate (bpm)",
                tickformat= ".0f"
            ),
            legend=dict(
                orientation="h",
                yanchor= "bottom",
                y= 1.02,
                xanchor= "right",
                x= 1
            ),
            yaxis2=dict(
                domain=[0.34, 0.65],
                title= "Pace (min/km)",
                autorange="reversed",
                tickformat= "%M:%S"
            ),
            yaxis3=dict(
                domain=[0.67, 1.00],
                title= "Time delta (s)",
                tickformat= ".0f"
            )
        )
        
        # Finally create figure
        fig = go.Figure(data= tracesList,
                        layout= layout
                        )
        fig.update_layout(title= graphTitle)
        fig.update_xaxes(title_text= "Distance (m)")
        fig.show()