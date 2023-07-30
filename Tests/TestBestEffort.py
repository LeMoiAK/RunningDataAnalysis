# -*- coding: utf-8 -*-
"""
Script to investigate better algorithms to find the best efforts in the runs.

Created on Sat Jul 29 06:26:00 2023

@author: LeMoiAK
"""

#%% Import useful modules
# Imports the ActivityImporter class
import Utilities.Functions as Utils
from Utilities.ActivityImporter import ActivityImporter
import pandas as pd
import numpy as np
import time

#%% Imports a fit file to just get the datafamre
filePath = Utils.getDataPath() + "\\11566503738_ACTIVITY.fit"
print(filePath)

# Read the FIT file into a DataFrame
df = ActivityImporter.loadDataFromFitFile(filePath)

# Do some conversions that might be useful
df['speed_kph'] = df['speed'] * 3.6
df['time'] = (df['timestamp'] - df['timestamp'].iloc[0]).apply(lambda x: x.total_seconds())
(df['position_lat_deg'], df['position_long_deg']) = Utils.SemiToDeg(df['position_lat'], df['position_long'])

#%% Script settings
distanceToGet = 5.0e3; # Search only for the 5k in a first time

#%% Define original algorithm
def originalSearch(df, distanceToGet):
    Nrows = len(df)
    
    bestTimePerDistance = np.inf
    bestEffortDistanceIndex = np.ones((1,2)) * np.nan
    
    # Get nice names for the channels to look at
    distanceArray = df['distance'].values
    timeArray = df['time'].values
    
    # Go through the data point by point
    fullIdxArray = np.arange(Nrows) # Create the index array once to avoid calling np.arange many times
    
    for idxStart in fullIdxArray:
        thisDistanceStart = distanceArray[idxStart]
        thisTimeStart = timeArray[idxStart]
        
        # These booleans are required to check we don't assign again once a valid value has been found for each effort
        hasFoundDistance = False
        # Then go through the rest of the data
        for idxEnd in fullIdxArray[idxStart:]:
            thisDistanceEnd = distanceArray[idxEnd]
            thisTimeEnd = timeArray[idxEnd]
            
            distDelta = thisDistanceEnd - thisDistanceStart
            timeDelta = thisTimeEnd - thisTimeStart
            # Distances
            if not(hasFoundDistance) and distDelta >= distanceToGet:
                hasFoundDistance = True
                if bestTimePerDistance > timeDelta:
                    # Found a new best effort for that distance
                    # Update time and subset index
                    bestTimePerDistance = timeDelta
                    bestEffortDistanceIndex[0, 0] = idxStart
                    bestEffortDistanceIndex[0, 1] = idxEnd
    
    # Then return best time and indices
    return (bestTimePerDistance, bestEffortDistanceIndex)

#%% Sliding search algorithm
# First we search from the start the first segment having the right distance
# Then we slide along the data by removing points at the start and adding points at the end if they allow to remain over the distance
def slidingSearch(df, distanceToGet):
    # Initialise the indices
    idxStart = 0
    idxEnd = 1
    
    # Initialise the variables
    bestTimePerDistance = np.inf
    bestEffortDistanceIndex = np.ones((1,2)) * np.nan
    
    # Get nice names for the channels to look at
    distanceArray = df['distance'].values
    timeArray = df['time'].values
    
    # Find the first end index that matches the distance
    thisDistanceStart = distanceArray[idxStart]
    thisTimeStart = timeArray[idxStart]
    thisDistanceEnd = distanceArray[idxEnd]
    thisTimeEnd = timeArray[idxEnd]
    
    distDelta = thisDistanceEnd - thisDistanceStart
    timeDelta = thisTimeEnd - thisTimeStart
    
    Nrows = len(df)
    while idxEnd <= (Nrows-2) and distDelta < distanceToGet:
        idxEnd += 1
        thisDistanceEnd = distanceArray[idxEnd]
        thisTimeEnd = timeArray[idxEnd]
        
        distDelta = thisDistanceEnd - thisDistanceStart
        timeDelta = thisTimeEnd - thisTimeStart
        
    # This is the initial best guess
    bestTimePerDistance = timeDelta
    bestEffortDistanceIndex[0, 0] = idxStart
    bestEffortDistanceIndex[0, 1] = idxEnd

    # Then slide the indices progressively
    while idxEnd <= (Nrows-2):
        idxEnd += 1
        # Check the new array with a new point at the end
        distDelta = distanceArray[idxEnd] - distanceArray[idxStart]
        timeDelta = timeArray[idxEnd] - timeArray[idxStart]        
        # Check if we can remove the start index
        distDeltaStartRemoved = distDelta
        while distDeltaStartRemoved > distanceToGet:
            idxStart += 1
            distDeltaStartRemoved = distanceArray[idxEnd] - distanceArray[idxStart]
        # When we come out of this loop; that means we went one point too far
        idxStart -= 1
        # Check if the new array has a better time than the current best
        distDelta = distanceArray[idxEnd] - distanceArray[idxStart]
        timeDelta = timeArray[idxEnd] - timeArray[idxStart]
        if timeDelta < bestTimePerDistance:
            bestTimePerDistance = timeDelta
            bestEffortDistanceIndex[0, 0] = idxStart
            bestEffortDistanceIndex[0, 1] = idxEnd
    
    # Then return best time and indices
    return (bestTimePerDistance, bestEffortDistanceIndex)

    
#%% Test and time both functions
Ntest = 50;

# Original function
time_Original = np.ones_like(np.nan, shape=(Ntest,1))
for i in np.arange(Ntest):
    tStart = time.time()
    (bestTimePerDistance_Original, bestEffortDistanceIndex_Original) = originalSearch(df, distanceToGet)
    time_Original[i] = time.time() - tStart
print("ORIGINAL Execution time " + str(time_Original.mean()*1e6) + "us")

# Sliding function
time_Sliding = np.ones_like(np.nan, shape=(Ntest,1))
for i in np.arange(Ntest):
    tStart = time.time()
    (bestTimePerDistance_Sliding, bestEffortDistanceIndex_Sliding) = slidingSearch(df, distanceToGet)
    time_Sliding[i] = time.time() - tStart
print("SLIDING Execution time " + str(time_Sliding.mean()*1e6) + "us")
print("Time difference between best found " + str( (bestTimePerDistance_Original-bestTimePerDistance_Sliding)*1e6 ) + "us")
print("Improvement: " + str( time_Original.mean()/time_Sliding.mean() ) + " times better"  )