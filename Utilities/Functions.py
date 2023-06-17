# -*- coding: utf-8 -*-
"""
Useful and repeated utility functions to be used by any script.

Created on Sat Jun 17 16:11:42 2023

@author: koppa
"""

#%% Required modules
import pandas as pd


#%% File Functions
def getDataPath():
    """
    Gets the path to the data folder from the designated text file that will be ignored in GIT
    """
    txtFilePath = __file__.split("Functions.py")[0] + "dataFolderPath.txt"
    with open(txtFilePath, "r") as f:
        return f.readline() # Returns the file path

#%% Data management functions
def removeNumberColumsFromDataFrame(df):
    """
    Removes all columns with a number (int) as name from a DataFrame.
    """
    columnNames = df.columns
    # Get list of ints
    toRemove = []
    for name in columnNames:
        if isinstance(name, int):
            toRemove.append(name)
    # Remove these columns
    for name in toRemove:
        df = df.drop(columns=name, inplace=False)
    return df
    
def removeNumberKeysFromDict(thisDict):
    """
    Removes all columns with a number (int) as name from a Dictionary.
    """
    keyNames = thisDict.keys()
    # Get list of ints
    toRemove = []
    for name in keyNames:
        if isinstance(name, int):
            toRemove.append(name)
    # Remove these keys
    for name in toRemove:
        thisDict.pop(name, None)
    return thisDict

#%% Conversion functions
def SemiToDeg(posLat, posLong):
    """
    Transforms a lat/long position given in semicircle into a lat/long position
    given in degrees. See:
    https://forums.garmin.com/developer/fit-sdk/f/discussion/280125/record-the-latitude-and-longitude-format-of-the-message
    """
    
    posLat_deg  = posLat * ( 180.0 / 2**31 )
    posLong_deg = posLong * ( 180.0 / 2**31 )
    
    return (posLat_deg, posLong_deg)

def speedToPace(speedMS):
    """
    Transforms a speed in m/s to a pace in min/km
    Speed input must be a Pandas Series so we can use apply
    """
    # The max ensures we don't divide by 0 and don't go slower than 60min/km
    # Check for Type because we need different formulas for series and single numbers
    if isinstance(speedMS, pd.Series):
        return speedMS.apply(lambda speed: pd.to_datetime(1000/max(speed, 1/3.6), unit='s'))
    else:
        return pd.to_datetime(1000/max(speedMS, 1/3.6), unit='s')

def convertRPMtoCadence(cadence_RPM, fractional_cadence):
    """
    Converts a cadence in RPM and fractional cadence to a cadence in steps per minute. See
    https://forums.garmin.com/developer/fit-sdk/f/discussion/288454/fractional-cadence-values
    
    Raw cadence is the "RPM" of the legs, which must be multiplied by 2
    to get the number of steps. Fractional_cadence allows odd numbers
    """
    cadence_spm = (cadence_RPM + fractional_cadence) * 2.0
    return cadence_spm