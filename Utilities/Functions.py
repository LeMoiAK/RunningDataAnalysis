# -*- coding: utf-8 -*-
"""
Useful and repeated utility functions to be used by any script.

Created on Sat Jun 17 16:11:42 2023

@author: LeMoiAK
"""

#%% Required modules
import pandas as pd
import numpy as np
import datetime

#%% Useful constants
halfMarathonDistance = 21.0975e3  # in meters
fullMarathonDistance = 42.195e3   # in meters
mileDistance = 1.60934e3 # in meters 

#%% File Functions
def getDataPath():
    """
    Gets the path to the data folder from the designated text file that will be ignored in GIT
    """
    txtFilePath = __file__.split("Functions.py")[0] + "dataFolderPath.txt"
    with open(txtFilePath, "r") as f:
        return f.readline() # Returns the file path

#%% User functions
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    From: https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

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

def getAge(birthDate):
    """
    Gets the age of a user based on their birth date. The calculation is slightly
    complex due to leap years. We cannot just take *.year from the time delta.
    Instead we get the year delta then substract 1 or not based on whether
    birthday has passed or not.
    """
    today = datetime.datetime.today()
    return today.year - birthDate.year - ((today.month, today.day) < (birthDate.month, birthDate.day))

def valuesOrDict(dataIN, key, defaultValue):
    """
    Tests if a value is available in a dictionnary and returns the default value if not
    """
    if key in dataIN.keys():
        return dataIN[key]
    else:
        return defaultValue

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
        return pd.to_datetime(1000/np.maximum(speedMS, 1/3.6), unit='s')

def convertRPMtoCadence(cadence_RPM, fractional_cadence):
    """
    Converts a cadence in RPM and fractional cadence to a cadence in steps per minute. See
    https://forums.garmin.com/developer/fit-sdk/f/discussion/288454/fractional-cadence-values
    
    Raw cadence is the "RPM" of the legs, which must be multiplied by 2
    to get the number of steps. Fractional_cadence allows odd numbers
    """
    cadence_spm = (cadence_RPM + fractional_cadence) * 2.0
    return cadence_spm

#%% Math function
def gaussianKernel(u):
    """
    Standard Gaussian Kernel (without bandwith)
    """
    return 1/np.sqrt(2*np.pi) * np.exp(-1/2*np.power(u, 2))

def kernelRegressionSmoothing(xData, yData, xSmooth, bandWidth):
    """ 
    Kernel Regression Smoothing based on the Gaussian kernel.    
    """
    ySmooth = np.nan * xSmooth
    for i in np.arange(len(xSmooth)):
        x = xSmooth[i]
        fracBottom = np.sum(gaussianKernel( (x - xData)/bandWidth ))
        fracTop = np.sum( np.multiply(gaussianKernel( (x - xData)/bandWidth ), yData) )
        ySmooth[i] = fracTop / fracBottom
    return ySmooth

#%% Formatting functions
def format_timedelta(td):
    """
    Formats Timedeltas nicely to deal with negatives rather than showing a full day minus the desired time
    """
    if td < datetime.timedelta(0):
        return '-' + format_timedelta(-td)
    else:
        # Change this to format positive timedeltas the way you want
        return str(td)