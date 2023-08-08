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
        
    @staticmethod
    def bestEffortPerTimeEvolutionPlot(gdi):
        """
        Obtains then plots the evolution of the best effort pace per TIME for
        each period of 90 days. We can then see the evolution of best pace over time.
        Takes a GarminDataImporter with imported data as input.
        """
        
        # First obtain date range from the metrics
        dateRange = pd.date_range(start= gdi.activityMetricsDF["Metric_StartTime"].min(), end= gdi.activityMetricsDF["Metric_StartTime"].max(), freq = "90D")
        # Add one period to make sure we have the latest activities as well
        dateRange = dateRange.union(pd.date_range(dateRange[-1] + dateRange.freq, periods=1, freq=dateRange.freq))
        
        # Create the colors
        NdateRanges = len(dateRange)
        myColors = ["rgba({cr:.0f},{cg:.0f},{cb:.0f},{ca:.0f})".format(cr=c[0]*255,cg=c[1]*255,cb=c[2]*255,ca=c[3]*255) for c in pl.cm.coolwarm(np.linspace(0.0, 1.0, NdateRanges))]
        
        # Get data for each range then create a plot with the valid points
        tracesList = []
        for iPeriod in np.arange(1, NdateRanges):
            # Get data from GDI
            periodStart = dateRange[iPeriod-1]
            periodEnd   = dateRange[iPeriod]
            (timesNamesList, timesValuesArray, bestDistancePerTimeAllActivities, bestPacePerTimeAllActivities) = gdi.getBestPacePerTimeEffortForPeriod( periodStart, periodEnd)
            thisLabel = "From " + str(periodStart.date()) + " to " + str(periodEnd.date())
            
            # Filter data only to available points that have an effort (1h per km by default)
            xData = timesValuesArray
            yData = bestPacePerTimeAllActivities
            idxFilter = bestPacePerTimeAllActivities < datetime.datetime(1970, 1, 1, 1, 00, 00)
            xData = xData[idxFilter]
            yData = yData[idxFilter]
            
            tracesList.append(
                    go.Scatter(
                        x= xData/60,
                        y= yData,
                        name= thisLabel,
                        marker= dict(color= myColors[iPeriod], size=20),
                        legendgroup= thisLabel,
                        showlegend= True,
                        yaxis= "y",
                        line= dict(width=3)
                    )
                )
            
        # Then create Layout
        layout = go.Layout(
            legend=dict(
                orientation="h",
                yanchor= "bottom",
                y= 1.02,
                xanchor= "right",
                x= 1,
                font_size= 13
            ),
            yaxis=dict(
                domain=[0.00, 1.00],
                title= "Pace (min/km)",
                autorange="reversed",
                tickformat= "%M:%S"
            )
        )
        
        # Finally create figure
        fig = go.Figure(data= tracesList,
                        layout= layout
                        )
        fig.update_layout(title= "Evolution of Best Pace per Time for periods of 90 days", font_size=20)
        fig.update_xaxes(title_text= "Time (mins)")
        fig.show()
        
    @staticmethod
    def bestEffortPerDistanceEvolutionPlot(gdi):
        """
        Obtains then plots the evolution of the best effort pace per DISTANCE for
        each period of 90 days. We can then see the evolution of best pace over time.
        Takes a GarminDataImporter with imported data as input.
        """
        
        # First obtain date range from the metrics
        dateRange = pd.date_range(start= gdi.activityMetricsDF["Metric_StartTime"].min(), end= gdi.activityMetricsDF["Metric_StartTime"].max(), freq = "90D")
        # Add one period to make sure we have the latest activities as well
        dateRange = dateRange.union(pd.date_range(dateRange[-1] + dateRange.freq, periods=1, freq=dateRange.freq))
        
        # Create the colors
        NdateRanges = len(dateRange)
        myColors = ["rgba({cr:.0f},{cg:.0f},{cb:.0f},{ca:.0f})".format(cr=c[0]*255,cg=c[1]*255,cb=c[2]*255,ca=c[3]*255) for c in pl.cm.coolwarm(np.linspace(0.0, 1.0, NdateRanges))]
        
        # Get data for each range then create a plot with the valid points
        tracesList = []
        for iPeriod in np.arange(1, NdateRanges):
            # Get data from GDI
            periodStart = dateRange[iPeriod-1]
            periodEnd   = dateRange[iPeriod]
            (distancesNamesList, distancesValuesArray, bestTimePerDistanceAllActivities, bestPacePerDistanceAllActivities) = gdi.getBestPacePerDistanceEffortForPeriod( periodStart, periodEnd)
            thisLabel = "From " + str(periodStart.date()) + " to " + str(periodEnd.date())
            
            # Filter data only to available points that have an effort (1h per km by default)
            xData = distancesValuesArray
            yData = bestPacePerDistanceAllActivities
            idxFilter = bestPacePerDistanceAllActivities < datetime.datetime(1970, 1, 1, 1, 00, 00)
            xData = xData[idxFilter]
            yData = yData[idxFilter]
            
            tracesList.append(
                    go.Scatter(
                        x= xData/1.0e3,
                        y= yData,
                        name= thisLabel,
                        marker= dict(color= myColors[iPeriod], size=20),
                        legendgroup= thisLabel,
                        showlegend= True,
                        yaxis= "y",
                        line= dict(width=3)
                    )
                )
            
        # Then create Layout
        layout = go.Layout(
            legend=dict(
                orientation="h",
                yanchor= "bottom",
                y= 1.02,
                xanchor= "right",
                x= 1,
                font_size= 13
            ),
            yaxis=dict(
                domain=[0.00, 1.00],
                title= "Pace (min/km)",
                autorange="reversed",
                tickformat= "%M:%S"
            )
        )
        
        # Finally create figure
        fig = go.Figure(data= tracesList,
                        layout= layout
                        )
        fig.update_layout(title= "Evolution of Best Pace per Distance for periods of 90 days", font_size=20)
        fig.update_xaxes(title_text= "Distance (km)")
        fig.show()
        
    @staticmethod
    def plotDistributionHRzones(metricsDF, HRzonesDict, prefixInMetric):
        """
        Plots a distribution of the time spent in each HR zone for each month.
        It takes as argument the DataFrame of metrics, the dictionary defining
        the HR zones, as well as their prefix in the metrics column names.
        """
        
        # Create list of column names for HR zones
        HRzoneNames = list(HRzonesDict.keys())
        HRcolumnNames = [prefixInMetric + zoneName for zoneName in HRzoneNames]
        # Get total per zone for each year-month
        sumTimePerMonth = metricsDF.groupby(metricsDF['Metric_StartTime'].dt.strftime("%Y-%m"))[HRcolumnNames].sum()
        # Create Sum of time in each zone to get ratios
        sumTimePerMonth['Total'] = sumTimePerMonth[HRcolumnNames].sum(axis=1)
        
        # The create the trace for each zone
        tracesList = []
        for idx, thisCol in enumerate(HRcolumnNames):
            thisHRzoneName = HRzoneNames[idx]
            thisLegendName = thisHRzoneName.replace('_', ' ') + ": " + \
                                str(HRzonesDict[thisHRzoneName][0]) + "bpm to " + str(HRzonesDict[thisHRzoneName][1]) + "bpm"
            tracesList.append(
                    go.Bar(
                        x= sumTimePerMonth.index,
                        y= sumTimePerMonth[thisCol] / sumTimePerMonth['Total']*100.0,
                        name= thisLegendName,
                        legendgroup= HRcolumnNames[idx],
                        showlegend= True,
                        yaxis= "y"
                        )
                )
        # Create the Layout
        layout = go.Layout(
            legend=dict(
                orientation="h",
                yanchor= "bottom",
                y= 1.02,
                xanchor= "right",
                x= 1,
                font_size= 13
            ),
            yaxis=dict(
                domain=[0.00, 1.00],
                title= "Percent of Time Spent in each Zone (%)"
            )
        )
        # Finally create the figure
        fig = go.Figure(data= tracesList, layout= layout)
        fig.update_layout(title= "Distribution of time spent in each Heart Rate zone", font_size=20, barmode='stack', xaxis_tickangle=-45)
        fig.update_xaxes(title_text= "Month Year")
        fig.show()
        
    @staticmethod
    def plotDistributionPaceZones(metricsDF, PaceZonesDict, prefixInMetric):
        """
        Plots a distribution of the time spent in each Pace zone for each month.
        It takes as argument the DataFrame of metrics, the dictionary defining
        the Pace zones, as well as their prefix in the metrics column names.
        """
        
        # Create list of column names for HR zones
        PaceZoneNames = list(PaceZonesDict.keys())
        PaceColumnNames = [prefixInMetric + zoneName for zoneName in PaceZoneNames]
        # Get total per zone for each year-month
        sumTimePerMonth = metricsDF.groupby(metricsDF['Metric_StartTime'].dt.strftime("%Y-%m"))[PaceColumnNames].sum()
        # Create Sum of time in each zone to get ratios
        sumTimePerMonth['Total'] = sumTimePerMonth[PaceColumnNames].sum(axis=1)
        
        # The create the trace for each zone
        tracesList = []
        for idx, thisCol in enumerate(PaceColumnNames):
            thisPaceZoneName = PaceZoneNames[idx]
            thisLegendName = thisPaceZoneName.replace('_', ' ') + ": " + \
                                PaceZonesDict[thisPaceZoneName][0].strftime("%M:%S") + "/km to " + PaceZonesDict[thisPaceZoneName][1].strftime("%M:%S") + "/km"
            tracesList.append(
                    go.Bar(
                        x= sumTimePerMonth.index,
                        y= sumTimePerMonth[thisCol] / sumTimePerMonth['Total']*100.0,
                        name= thisLegendName,
                        legendgroup= PaceColumnNames[idx],
                        showlegend= True,
                        yaxis= "y"
                        )
                )
        # Create the Layout
        layout = go.Layout(
            legend=dict(
                orientation="h",
                yanchor= "bottom",
                y= 1.02,
                xanchor= "right",
                x= 1,
                font_size= 11
            ),
            yaxis=dict(
                domain=[0.00, 1.00],
                title= "Percent of Time Spent in each Zone (%)"
            )
        )
        # Finally create the figure
        fig = go.Figure(data= tracesList, layout= layout)
        fig.update_layout(title= "Distribution of time spent in each Pace zone", font_size=20, barmode='stack', xaxis_tickangle=-45)
        fig.update_xaxes(title_text= "Month Year")
        fig.show()