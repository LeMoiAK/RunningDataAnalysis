# -*- coding: utf-8 -*-
"""
ActivityImporter class
Class to import and process an activity .fit file
It also generates metrics and more avanced metrics.

This framework is only meant to deal with single sport sessions.

Created on Thu Jun 15 22:41:46 2023

@author: LeMoiAK
"""

#%% Import required modules
from garmin_fit_sdk import Decoder, Stream
import Utilities.Functions as Utils
import numpy as np
import pandas as pd
import datetime
from meteostat import Point, Hourly


#%% Define the ActivityImporter class
class ActivityImporter:
    """
    This class imports a single .fit activity given a file path.
    It also contains functions to create advanced metrics.
    """
    
    def __init__(self, filePath, estimateBestEfforts=True, importWeather=True):
        """
        Contructor. Give path to the .fit file as input
        """
        
        # Declare Main variables so we know they exist
        self.ObjInfo = dict()
        
        # Creates a stream and decoder object from the Garmin SDK to import data
        stream = Stream.from_file(filePath)
        decoder = Decoder(stream)
        # Then does the decoding
        messages, errors = decoder.read()
        
        # Checks for errors
        if len(errors) > 0:
            self.ObjInfo['DecodeSuccess'] = False
            print(f"Could not decode {filePath}: {errors}")
        else:
            self.ObjInfo['DecodeSuccess'] = True
        
        # Check if we indeed have an activity then get metrics if yes
        if 'activity_mesgs' in messages.keys() and 'record_mesgs' in messages.keys() \
            and 'event_mesgs' in messages.keys() and 'sport_mesgs' in messages.keys():
            self.ObjInfo['isSportActivity'] = True
            self.ObjInfo['sport'] = messages['sport_mesgs'][0]['sport']
            
            # Filter per sport - not designed to work with multisport
            if 'running' in self.ObjInfo['sport']:
                # Extracts User infos, file infos, and Metrics
                self.extractMetricsAndInfo(messages)
                    
                # Puts the records into the DataFrame format
                self.transformRecordsToDataFrame(messages['record_mesgs'])
                
                # Adds file path to the file info
                self.fileInfo['filePath'] = filePath
                
                # Get best efforts if requested
                if estimateBestEfforts:
                    self.getBestEfforts()
                    self.ObjInfo['hasBestEfforts'] = True
                else:
                    self.ObjInfo['hasBestEfforts'] = False
                    
                if importWeather:
                    self.importWeather()
                    self.ObjInfo['hasWeather'] = True
                else:
                    self.ObjInfo['hasWeather'] = False
                    
        else:
            self.ObjInfo['isSportActivity'] = False
       
            
    #%% Data formatting functions
    def transformRecordsToDataFrame(self, recordMessages):
        """
        Transforms the records messages into a pandas dataFrame and performs
        all operations on the data such as unit conversion
        """
        
        # Get into dataFrame
        df = pd.DataFrame(recordMessages)
        
        # Drop 136 and 135 columns
        # Drops 136 because it is exactly the heart rate
        # Drops 135 because no clue what it actually is
        df = Utils.removeNumberColumsFromDataFrame(df)
        
        # Get Cadence in Steps Per Minute
        # https://forums.garmin.com/developer/fit-sdk/f/discussion/288454/fractional-cadence-values
        if ('cadence' in df.columns) and ('fractional_cadence' in df.columns):
            # Raw cadence is the "RPM" of the legs, which must be multiplied by 2
            # to get the number of steps. Fractional_cadence allows odd numbers
            df['cadence_spm'] = Utils.convertRPMtoCadence(df['cadence'], df['fractional_cadence'])
        
        # Get position in degrees instead of semicircles
        # https://forums.garmin.com/developer/fit-sdk/f/discussion/280125/record-the-latitude-and-longitude-format-of-the-message
        if ('position_lat' in df.columns) and ('position_long' in df.columns):
            (df['position_lat_deg'], df['position_long_deg']) = Utils.SemiToDeg(df['position_lat'], df['position_long'])
                    
        # Drop enhanced fields because they are of no use for running
        # https://www.thisisant.com/forum/viewthread/4561
        if 'enhanced_speed' in df.columns:
            df.drop(columns='enhanced_speed', inplace=True)
        if 'enhanced_altitude' in df.columns:
            df.drop(columns='enhanced_altitude', inplace=True)
        
        # Get pace in min/km and speed in kph
        if 'speed' in df.columns:
            df['speed_kph']  = df['speed'] * 3.6
            df['pace'] = Utils.speedToPace(df['speed'])
        
        # Check the distance channel vs the integration of speed
        # Some activities have very bad distance estimations
        # No more than 30% error
        df['time'] = (df['timestamp'] - df['timestamp'].iloc[0]).apply(lambda x: x.total_seconds())
        estimatedDistance = np.trapz(x=df['time'], y=df['speed'].fillna(0.0))
        finalDistance = df['distance'].iloc[-1]
        if abs(estimatedDistance-finalDistance)/finalDistance*100 > 30:
            self.ObjInfo['isDistanceValid'] = False
        else:
            self.ObjInfo['isDistanceValid'] = True
        
        # Save df into object name
        self.data = df
        
    def extractBestEffortTimeSeries(self, effortName):
        """
        Creates a subset of the time series dataFrame that corresponds to the best effort for a Time or a distance.
        """
        
        # Check we have the best efforts available
        if not(self.ObjInfo['hasBestEfforts']):
            print("Best Efforts are not available.")
            return -1
        
        # Check the effort exists
        if not(effortName in self.bestEffortData['Distance_Names']) and not(effortName in self.bestEffortData['Time_Names']):
            print(f"{effortName} is not recognised as a Best Effort distance or Time")
            return -1
        
        # Find if distance or time, and which index
        if effortName in self.bestEffortData['Distance_Names']:
            isDistance = True
            idxEffort = self.bestEffortData['Distance_Names'].index(effortName)
            # Check the distance has a time record
            if np.isinf(self.bestEffortData['Distance_Times'][effortName]):
                print(f"{effortName} has no best effort for this activity")
                return -1
        elif effortName in self.bestEffortData['Time_Names']:
            isDistance = False
            idxEffort = self.bestEffortData['Time_Names'].index(effortName)
            # Check the time has a distance record
            if self.bestEffortData['Time_Distances'][effortName] == 0.0:
                print(f"{effortName} has no best effort for this activity")
                return -1
        
        # We now have a valid effort and can extract it from the dataFrame
        if isDistance:
            idxStart = int(self.bestEffortData['Distance_index'][idxEffort, 0])
            idxEnd   = int(self.bestEffortData['Distance_index'][idxEffort, 1])
        else:
            idxStart = int(self.bestEffortData['Time_index'][idxEffort, 0])
            idxEnd   = int(self.bestEffortData['Time_index'][idxEffort, 1])
            
        dfBestEffort = self.data.iloc[idxStart:(idxEnd+1)].copy()
        # Create a distance and time with 0 offset
        dfBestEffort['distanceEffort'] = dfBestEffort['distance'] - dfBestEffort['distance'].iloc[0]
        dfBestEffort['timeEffort'] = dfBestEffort['time'] - dfBestEffort['time'].iloc[0]
        return dfBestEffort
    
    def extractMetricsAndInfo(self, messages):
        """
        Extracts user information, file information, and metrics.
        Also converts them to the right unit as will be later required.
        """
        
        # Information on activity
        self.activityInfo = Utils.removeNumberKeysFromDict(messages['activity_mesgs'][0])
        # Information on device like what sensors are available
        self.deviceInfo = messages['device_info_mesgs']
        # Information on the file
        self.fileInfo = Utils.removeNumberKeysFromDict(messages['file_id_mesgs'][0])
        # List of events (start, stop, changes, etc)
        self.eventListDF = Utils.removeNumberColumsFromDataFrame(pd.DataFrame(messages['event_mesgs']))  # At least start and stop events so always a list
        # Laps and metrics per lap
        self.lapsMetricsDF = Utils.removeNumberColumsFromDataFrame(pd.DataFrame(messages['lap_mesgs']))
        if ('start_position_lat' in self.lapsMetricsDF.columns) and ('start_position_long' in self.lapsMetricsDF.columns):
            (self.lapsMetricsDF['start_position_lat_deg'], self.lapsMetricsDF['start_position_long_deg']) = \
                Utils.SemiToDeg(self.lapsMetricsDF['start_position_lat'], self.lapsMetricsDF['start_position_long'])
        if ('end_position_lat' in self.lapsMetricsDF.columns) and ('end_position_long' in self.lapsMetricsDF.columns):
            (self.lapsMetricsDF['end_position_lat_deg'], self.lapsMetricsDF['end_position_long_deg']) = \
                Utils.SemiToDeg(self.lapsMetricsDF['end_position_lat'], self.lapsMetricsDF['end_position_long'])
        self.lapsMetricsDF['avg_pace'] = Utils.speedToPace(self.lapsMetricsDF['avg_speed'])
        self.lapsMetricsDF['max_pace'] = Utils.speedToPace(self.lapsMetricsDF['max_speed'])
        self.lapsMetricsDF['avg_cadence_spm'] = Utils.convertRPMtoCadence(self.lapsMetricsDF['avg_cadence'], self.lapsMetricsDF['avg_fractional_cadence'])
        self.lapsMetricsDF['max_cadence_spm'] = Utils.convertRPMtoCadence(self.lapsMetricsDF['max_cadence'], self.lapsMetricsDF['max_fractional_cadence'])
        # Total Session Metrics
        self.sessionMetrics = Utils.removeNumberKeysFromDict(messages['session_mesgs'][0])
        if ('start_position_lat' in self.sessionMetrics.keys()) and ('start_position_long' in self.sessionMetrics.keys()):
            (self.sessionMetrics['start_position_lat_deg'], self.sessionMetrics['start_position_long_deg']) = \
                Utils.SemiToDeg(self.sessionMetrics['start_position_lat'], self.sessionMetrics['start_position_long'])
        self.sessionMetrics['avg_pace'] = Utils.speedToPace(self.sessionMetrics['avg_speed'])
        self.sessionMetrics['max_pace'] = Utils.speedToPace(self.sessionMetrics['max_speed'])
        self.sessionMetrics['avg_cadence_spm'] = Utils.convertRPMtoCadence(self.sessionMetrics['avg_cadence'], self.sessionMetrics['avg_fractional_cadence'])
        self.sessionMetrics['max_cadence_spm'] = Utils.convertRPMtoCadence(self.sessionMetrics['max_cadence'], self.sessionMetrics['max_fractional_cadence'])
        # Splits Information, run/walk/stand
        if 'split_mesgs' in messages.keys(): # This feature seems to have been added only after some time
            self.splitsInfo = Utils.removeNumberColumsFromDataFrame(pd.DataFrame(messages['split_mesgs']))
        # Information on Sport
        self.sportInfo = Utils.removeNumberKeysFromDict(messages['sport_mesgs'][0])
        # Heart-Rate zone per lap and for the whole session in last item (Nlaps+1)
        self.lapHRzonesDF = Utils.removeNumberColumsFromDataFrame(pd.DataFrame(messages['time_in_zone_mesgs']))
        # User Information like height, weight
        self.userProfile = Utils.removeNumberKeysFromDict(messages['user_profile_mesgs'][0])
        self.userProfile['sleep_time_TD'] = pd.Timestamp(self.userProfile['sleep_time'], unit='s') # Convert sleep and wake times in datetime
        self.userProfile['wake_time_TD'] = pd.Timestamp(self.userProfile['wake_time'], unit='s')

    def exportUsefulMetrics(self):
        """
        Function to export the most useful metrics to a dictionary.
        These metrics will then be put into a list that can be used for studying all sessions.
        """
        
        metricsExport = dict()
        
        # Create a dictionary containing all the metrics to obtain and which subfield
        # User Info
        metricsExport['User_Gender'] = self.userProfile['gender']
        metricsExport['User_Height'] = self.userProfile['height']
        metricsExport['User_RestingHeartRate'] = self.userProfile['resting_heart_rate']
        if 'max_heart_rate' in self.lapHRzonesDF.columns: # Not available for all activities
            metricsExport['User_MaxHeartRate'] = self.lapHRzonesDF['max_heart_rate'].iloc[-1]
        else:
            metricsExport['User_MaxHeartRate'] = np.nan
        metricsExport['User_Weight'] = self.userProfile['weight']
        metricsExport['User_SleepTime'] = self.userProfile['sleep_time_TD']
        metricsExport['User_WakeTime'] = self.userProfile['wake_time_TD']
        # Device and file info
        metricsExport['File_Device'] = self.fileInfo['manufacturer'] + ' ' + self.fileInfo['garmin_product'] + ' - ' + str(self.fileInfo['serial_number'])
        metricsExport['File_Path'] = self.fileInfo['filePath']
        metricsExport['File_CreationDate'] = self.fileInfo['time_created']
        metricsExport['File_isDistanceValid'] = self.ObjInfo['isDistanceValid']
        # Sport Info
        metricsExport['Sport_Name'] = self.sportInfo['name']
        metricsExport['Sport_Type'] = self.sportInfo['sport']
        metricsExport['Sport_SubType'] = self.sportInfo['sub_sport']
        # Session Metrics
        metricsExport['Metric_TotalTimerTime'] = self.sessionMetrics['total_timer_time'] # Timer of activity (pause excluded)
        metricsExport['Metric_TotalElapsedTime'] = self.sessionMetrics['total_elapsed_time'] # Timer (pause included)
        metricsExport['Metric_TotalDistance'] = self.sessionMetrics['total_distance']
        metricsExport['Metric_TotalCalories'] = self.sessionMetrics['total_calories']
        metricsExport['Metric_StartTime'] = self.sessionMetrics['start_time']
        metricsExport['Metric_EndTime'] = self.sessionMetrics['start_time'] + datetime.timedelta(seconds=self.sessionMetrics['total_elapsed_time'])
        metricsExport['Metric_AvgSpeed_ms'] = self.sessionMetrics['avg_speed']
        metricsExport['Metric_MaxSpeed_ms'] = self.sessionMetrics['max_speed']
        metricsExport['Metric_AvgPace'] = self.sessionMetrics['avg_pace']
        metricsExport['Metric_MaxPace'] = self.sessionMetrics['max_pace']
        metricsExport['Metric_TotalAscent'] = Utils.valuesOrDict(self.sessionMetrics, 'total_ascent', np.nan) # Not available for all activities, ex Treadmill
        metricsExport['Metric_TotalDescent'] = Utils.valuesOrDict(self.sessionMetrics, 'total_descent', np.nan)
        metricsExport['Metric_AvgCadence_spm'] = self.sessionMetrics['avg_cadence_spm']
        metricsExport['Metric_MaxCadence_spm'] = self.sessionMetrics['max_cadence_spm']
        metricsExport['Metric_NbLaps'] = self.sessionMetrics['num_laps']
        metricsExport['Metric_AvgHeartRate'] = self.sessionMetrics['avg_heart_rate']
        metricsExport['Metric_MaxHeartRate'] = self.sessionMetrics['max_heart_rate']
        metricsExport['Metric_StartPosition_Lat'] = Utils.valuesOrDict(self.sessionMetrics, 'start_position_lat_deg', np.nan) # Not available for all activities, ex Treadmill
        metricsExport['Metric_StartPosition_Long'] = Utils.valuesOrDict(self.sessionMetrics, 'start_position_long_deg', np.nan)
        # Heart Rate - Metrics only for whole session
        timeHRzones = self.lapHRzonesDF['time_in_hr_zone'].iloc[-1]
        totalTimeForHRzones = np.sum(timeHRzones) # Might be slightly different than session time
        if 'hr_zone_high_boundary' in self.lapHRzonesDF.columns: # Not available for all activities, ex First One
            HRzonesBounds = self.lapHRzonesDF['hr_zone_high_boundary'].iloc[-1]
        else:
            HRzonesBounds = [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]        
        metricsExport['HR_ZoneBoundaries'] = ','.join(str(bnd) for bnd in HRzonesBounds)
        metricsExport['HR_ZoneNames'] = "Warm Up,Easy,Aerobic,Threshold,Maximum"
        for iZone in np.arange(len(timeHRzones)):
            metricsExport['HR_Time_Zone_' + str(iZone)] = timeHRzones[iZone]
            metricsExport['HR_Ratio_Zone_' + str(iZone)] = timeHRzones[iZone] / totalTimeForHRzones * 100
        # Laps metrics
        metricsExport['Laps_Distance'] = ','.join(str(x) for x in self.lapsMetricsDF['total_distance'])
        metricsExport['Laps_Time'] = ','.join(str(x) for x in self.lapsMetricsDF['total_timer_time'])
        metricsExport['Laps_AvgPace'] = ','.join(x.strftime("%M:%S") for x in self.lapsMetricsDF['avg_pace'])
        metricsExport['Laps_MaxPace'] = ','.join(x.strftime("%M:%S") for x in self.lapsMetricsDF['max_pace'])
        metricsExport['Laps_AvgHR'] = ','.join(str(x) for x in self.lapsMetricsDF['avg_heart_rate'])
        metricsExport['Laps_MaxHR'] = ','.join(str(x) for x in self.lapsMetricsDF['max_heart_rate'])
        metricsExport['Laps_AvgCadence_spm'] = ','.join(str(x) for x in self.lapsMetricsDF['avg_cadence_spm'])
        metricsExport['Laps_MaxCadence_spm'] = ','.join(str(x) for x in self.lapsMetricsDF['max_cadence_spm'])
        
        # Get Best efforts if it exists
        if self.ObjInfo['hasBestEfforts']:
            for thisKey in self.bestEffortsMetrics.keys():
                metricsExport['BestEffort_' + thisKey] = self.bestEffortsMetrics[thisKey]
        
        # Get Weather; always there but can be NaNs
        for thisKey in self.weatherMetrics.keys():
            metricsExport['Weather_' + thisKey] = self.weatherMetrics[thisKey]
        
        # Finally return the metrics
        return metricsExport
    
    #%% Data Analysis functions
    def getBestEfforts(self):
        """
        Obtains the best efforts for each distance and time scale in the data.
        For distances, we look at 400m, 500m, 800m, 1km, 1mile, 5km, 10km, 15km, 10miles, Half and Full Marathon
        For time, we look at 12mins (Cooper test) and 60mins (Threshold)
        For each of these, we also produce the pace.
        
        This function can be relatively slow to run.
        """
        
        # Get data
        df = self.data
        Nrows = len(df)
        
        # Initialise the distance related best efforts
        distancesNamesList =  ['400m', '500m', '800m', '1km',            '1mile', '5km', '10km', '15km',             '10miles',             'HalfMarathon',             'FullMarathon']
        distancesValuesList = [ 400.0,  500.0,  800.0, 1.0e3, Utils.mileDistance, 5.0e3, 10.0e3, 15.0e3, 10*Utils.mileDistance, Utils.halfMarathonDistance, Utils.fullMarathonDistance]
        Ndistances = len(distancesNamesList)
        bestTimePerDistance = dict(zip(distancesNamesList, np.inf * np.ones(Ndistances))) # Initialised to np.inf because we want to minimise it
        bestEffortDistanceIndex = np.ones((Ndistances,2)) * np.nan # First column for start, second for finish index

        # Initialise the time related best efforts
        timesNamesList =  ['30s', '1mins', '2mins', '5mins', '10mins', '12mins', '20mins', '30mins', '45mins', '60mins', '75mins', '90mins', '105mins', '120mins']
        timesValuesList = [ 30.0,  1*60.0,  2*60.0,  5*60.0,  10*60.0,  12*60.0,  20*60.0,  30*60.0,  45*60.0,  60*60.0,  75*60.0,  90*60.0,  105*60.0,  120*60.0]
        Ntimes = len(timesNamesList)
        bestDistancePerTime = dict(zip(timesNamesList, np.zeros(Ntimes))) # Initialised to 0.0 because we want to maximise
        bestEffortTimeIndex = np.ones((Ntimes,2)) * np.nan # First column for start, second for finish index

        # Get nice names for the channels to look at
        distanceArray = df['distance'].values
        timeArray = df['time'].values

        # Go through the data point by point
        fullIdxArray = np.arange(Nrows) # Create the index array once to avoid calling np.arange many times
        distIdxArray = np.arange(Ndistances)
        timeIdxArray = np.arange(Ntimes)
        for idxStart in fullIdxArray:
            thisDistanceStart = distanceArray[idxStart]
            thisTimeStart = timeArray[idxStart]
            
            # These booleans are required to check we don't assign again once a valid value has been found for each effort
            hasFoundDistance = dict(zip(distancesNamesList, [False for i in distIdxArray] ))
            hasFoundTime = dict(zip(timesNamesList, [False for i in timeIdxArray] ))
            # Then go through the rest of the data
            for idxEnd in fullIdxArray[idxStart:]:
                thisDistanceEnd = distanceArray[idxEnd]
                thisTimeEnd = timeArray[idxEnd]
                
                distDelta = thisDistanceEnd - thisDistanceStart
                timeDelta = thisTimeEnd - thisTimeStart
                # Distances
                for iDist in distIdxArray:
                    thisDistName = distancesNamesList[iDist]
                    thisDistValue = distancesValuesList[iDist]
                    if not(hasFoundDistance[thisDistName]) and distDelta >= thisDistValue:
                        hasFoundDistance[thisDistName] = True
                        if bestTimePerDistance[thisDistName] >= timeDelta:
                            # Found a new best effort for that distance
                            # Update time and subset index
                            bestTimePerDistance[thisDistName] = timeDelta   
                            bestEffortDistanceIndex[iDist, 0] = idxStart
                            bestEffortDistanceIndex[iDist, 1] = idxEnd
                        
                # Times
                for iDist in timeIdxArray:
                    thisTimeName = timesNamesList[iDist]
                    thisTimeValue = timesValuesList[iDist]
                    if not(hasFoundTime[thisTimeName]) and timeDelta >= thisTimeValue:
                        hasFoundTime[thisTimeName] = True
                        if bestDistancePerTime[thisTimeName] <= distDelta:
                            # Found a new best effort for that time
                            # Update distance and subset index
                            bestDistancePerTime[thisTimeName] = distDelta   
                            bestEffortTimeIndex[iDist, 0] = idxStart
                            bestEffortTimeIndex[iDist, 1] = idxEnd

        # Then convert to paces and timestamps
        bestEffortsMetrics = dict()
        # Distances
        for iDist in distIdxArray:
            thisDistName = distancesNamesList[iDist]
            thisDistValue = distancesValuesList[iDist]
            if not(bestTimePerDistance[thisDistName] == np.inf):
                bestEffortsMetrics['distance_' + thisDistName + '_time'] = bestTimePerDistance[thisDistName]
                bestEffortsMetrics['distance_' + thisDistName + '_timeStamp'] = pd.Timestamp(bestTimePerDistance[thisDistName], unit='s')
                bestEffortsMetrics['distance_' + thisDistName + '_pace'] = Utils.speedToPace(thisDistValue / bestTimePerDistance[thisDistName])
            else:
                bestEffortsMetrics['distance_' + thisDistName + '_time'] = np.nan
                bestEffortsMetrics['distance_' + thisDistName + '_timeStamp'] = np.nan
                bestEffortsMetrics['distance_' + thisDistName + '_pace'] = np.nan
        # Times
        for iDist in timeIdxArray:
            thisTimeName = timesNamesList[iDist]
            thisTimeValue = timesValuesList[iDist]
            if not(bestDistancePerTime[thisTimeName] == 0.0):
                bestEffortsMetrics['time_' + thisTimeName + '_distance'] = bestDistancePerTime[thisTimeName]
                bestEffortsMetrics['time_' + thisTimeName + '_pace'] = Utils.speedToPace(bestDistancePerTime[thisTimeName] / thisTimeValue)
            else:
                bestEffortsMetrics['time_' + thisDistName + '_distance'] = np.nan
                bestEffortsMetrics['time_' + thisDistName + '_pace'] = np.nan

        # Finally save metrics to class
        self.bestEffortsMetrics = bestEffortsMetrics
        # And save indexes because they'll be useful in the extractBestEffort function
        self.bestEffortData = dict()
        self.bestEffortData['Distance_index'] = bestEffortDistanceIndex
        self.bestEffortData['Distance_Names'] = distancesNamesList
        self.bestEffortData['Distance_Distances'] = distancesValuesList
        self.bestEffortData['Distance_Times'] = bestTimePerDistance
        self.bestEffortData['Distance_Paces'] = [Utils.speedToPace(runDist/runTime) for (runDist, runTime) in zip(distancesValuesList, bestTimePerDistance.values())]
        self.bestEffortData['Time_index'] = bestEffortTimeIndex
        self.bestEffortData['Time_Names'] = timesNamesList
        self.bestEffortData['Time_Distances'] = bestDistancePerTime
        self.bestEffortData['Time_Times'] = timesValuesList
        self.bestEffortData['Time_Paces'] = [Utils.speedToPace(runDist/runTime) for (runDist, runTime) in zip(bestDistancePerTime.values(), timesValuesList)]
    
    #%% Data augmentation functions
    def importWeather(self):
        """
        This function imports the weather data corresponding to the imported run.
        It uses the Meteostat module https://dev.meteostat.net/guide.html
        The units and codes are explained here https://dev.meteostat.net/formats.html#time-format
        """
        
        # This function works only for running session and not Treadmill
        if 'start_position_lat_deg' in self.sessionMetrics.keys() and 'start_position_long_deg' in self.sessionMetrics.keys():
            try:
                # Create startTime endTime and location from metrics
                # Need to save then suppress the timezone information because of the Hourly function
                origTZinfo = self.sessionMetrics['start_time'].tzname()
                startTime = self.sessionMetrics['start_time'].replace(tzinfo=None)
                endTime = self.sessionMetrics['start_time'] + datetime.timedelta(seconds=self.sessionMetrics['total_elapsed_time'])
                endTime = endTime.replace(tzinfo=None)
                endTime = endTime.replace(second=0, microsecond=0, minute=0, hour=endTime.hour+1) # Ensure there's at least an hour (but loss of precision)
                
                startPosLat = Utils.valuesOrDict(self.sessionMetrics, 'start_position_lat_deg', np.nan)
                startPosLon = Utils.valuesOrDict(self.sessionMetrics, 'start_position_long_deg', np.nan)
                location = Point(startPosLat, startPosLon, self.data['altitude'].iloc[0])
        
                # Get data
                weatherData = Hourly(location, startTime, endTime, origTZinfo)
                weatherData = weatherData.fetch()
        
                weatherConditions = {1: "Clear", 2: "Fair", 3: "Cloudy", 4: "Overcast", 5: "Fog", 6: "Freezing Fog", 7: "Light Rain", 8: "Rain", 9: "Heavy Rain",
                                     10: "Freezing Rain", 11: "Heavy Freezing Rain", 12: "Sleet", 13: "Heavy Sleet", 14: "Light Snowfall", 15: "Snowfall",
                                     16: "Heavy Snowfall", 17: "Rain Shower", 18: "Heavy Rain Shower", 19: "Sleet Shower", 20: "Heavy Sleet Shower",
                                     21: "Snow Shower", 22: "Heavy Snow Shower", 23: "Lightning", 24: "Hail", 25: "Thunderstorm", 26: "Heavy Thunderstorm", 27: "Storm"}
        
                self.weatherMetrics = dict()
                self.weatherMetrics['Temperature_degC'] = weatherData['temp'].mean()
                self.weatherMetrics['Rain_mm'] = weatherData['prcp'].mean()
                self.weatherMetrics['WindSpeed_kph'] = weatherData['wspd'].mean()
                self.weatherMetrics['WindGustSpeed_kph'] = weatherData['wpgt'].mean()
                self.weatherMetrics['Condition'] = weatherData['coco'].map(weatherConditions).iloc[0]
            except:
                print('Can''t get Weather for: ' + self.fileInfo['filePath'])
                self.weatherMetrics = dict()
                self.weatherMetrics['Temperature_degC'] = np.nan
                self.weatherMetrics['Rain_mm'] = np.nan
                self.weatherMetrics['WindSpeed_kph'] = np.nan
                self.weatherMetrics['WindGustSpeed_kph'] = np.nan
                self.weatherMetrics['Condition'] = ""
        else:
            self.weatherMetrics = dict()
            self.weatherMetrics['Temperature_degC'] = np.nan
            self.weatherMetrics['Rain_mm'] = np.nan
            self.weatherMetrics['WindSpeed_kph'] = np.nan
            self.weatherMetrics['WindGustSpeed_kph'] = np.nan
            self.weatherMetrics['Condition'] = ""
            
    #%% Static methods
    @staticmethod
    def loadDataFromFitFile(filePath):
        """
        Function to load a single fit file and return the time series of the data
        without all the change to units, names, and other transformations.
        Should work with any kind of activity.
        Bare minimum code to read a FIT file.
        """
        
        # Creates a stream and decoder object from the Garmin SDK to import data
        stream = Stream.from_file(filePath)
        decoder = Decoder(stream)
        # Then does the decoding
        messages, errors = decoder.read()
        
        # Checks for errors
        if len(errors) > 0:
            print(f"Could not decode {filePath}: {errors}")
            return -1
        
        # Get into dataFrame
        if "record_mesgs" in messages:
            df = pd.DataFrame(messages['record_mesgs'])
            return df
        else:
            print(f"No record messages in {filePath}")
            return -1