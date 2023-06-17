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


#%% Define the ActivityImporter class
class ActivityImporter:
    """
    This class imports a single .fit activity given a file path.
    It also contains functions to create advanced metrics.
    """
    
    def __init__(self, filePath):
        """Contructor. Give path to the .fit file as input"""
        
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
            
        # Extracts User infos, file infos, and Metrics
        self.extractMetricsAndInfo(messages)
            
        # Puts the records into the DataFrame format
        self.transformRecordsToDataFrame(messages['record_mesgs'])
        
        # Adds file path to the file info
        self.fileInfo['filePath'] = filePath
    
    #%% Data formatting functions
    def transformRecordsToDataFrame(self, recordMessages):
        """Transforms the records messages into a pandas dataFrame and performs
        all operations on the data such as unit conversion"""
        
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
        
        # Save df into object name
        self.data = df
    
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
        (self.lapsMetricsDF['start_position_lat_deg'], self.lapsMetricsDF['start_position_long_deg']) = \
            Utils.SemiToDeg(self.lapsMetricsDF['start_position_lat'], self.lapsMetricsDF['start_position_long'])
        (self.lapsMetricsDF['end_position_lat_deg'], self.lapsMetricsDF['end_position_long_deg']) = \
            Utils.SemiToDeg(self.lapsMetricsDF['end_position_lat'], self.lapsMetricsDF['end_position_long'])
        self.lapsMetricsDF['avg_pace'] = Utils.speedToPace(self.lapsMetricsDF['avg_speed'])
        self.lapsMetricsDF['max_pace'] = Utils.speedToPace(self.lapsMetricsDF['max_speed'])
        self.lapsMetricsDF['avg_cadence_spm'] = Utils.convertRPMtoCadence(self.lapsMetricsDF['avg_cadence'], self.lapsMetricsDF['avg_fractional_cadence'])
        self.lapsMetricsDF['max_cadence_spm'] = Utils.convertRPMtoCadence(self.lapsMetricsDF['max_cadence'], self.lapsMetricsDF['max_fractional_cadence'])
        # Total Session Metrics
        self.sessionMetrics = Utils.removeNumberKeysFromDict(messages['session_mesgs'][0])
        (self.sessionMetrics['start_position_lat_deg'], self.sessionMetrics['start_position_long_deg']) = \
            Utils.SemiToDeg(self.sessionMetrics['start_position_lat'], self.sessionMetrics['start_position_long'])
        self.sessionMetrics['avg_pace'] = Utils.speedToPace(self.sessionMetrics['avg_speed'])
        self.sessionMetrics['max_pace'] = Utils.speedToPace(self.sessionMetrics['max_speed'])
        self.sessionMetrics['avg_cadence_spm'] = Utils.convertRPMtoCadence(self.sessionMetrics['avg_cadence'], self.sessionMetrics['avg_fractional_cadence'])
        self.sessionMetrics['max_cadence_spm'] = Utils.convertRPMtoCadence(self.sessionMetrics['max_cadence'], self.sessionMetrics['max_fractional_cadence'])
        # Splits Information, run/walk/stand
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
        metricsExport['User_MaxHeartRate'] = self.lapHRzonesDF['max_heart_rate'].iloc[-1]
        metricsExport['User_Weight'] = self.userProfile['weight']
        metricsExport['User_SleepTime'] = self.userProfile['sleep_time_TD']
        metricsExport['User_WakeTime'] = self.userProfile['wake_time_TD']
        # Device and file info
        metricsExport['File_Device'] = self.fileInfo['manufacturer'] + ' ' + self.fileInfo['garmin_product'] + ' - ' + str(self.fileInfo['serial_number'])
        metricsExport['File_Path'] = self.fileInfo['filePath']
        metricsExport['File_CreationDate'] = self.fileInfo['time_created']
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
        metricsExport['Metric_TotalAscent'] = self.sessionMetrics['total_ascent']
        metricsExport['Metric_TotalDescent'] = self.sessionMetrics['total_descent']
        metricsExport['Metric_AvgCadence_spm'] = self.sessionMetrics['avg_cadence_spm']
        metricsExport['Metric_MaxCadence_spm'] = self.sessionMetrics['max_cadence_spm']
        metricsExport['Metric_NbLaps'] = self.sessionMetrics['num_laps']
        metricsExport['Metric_AvgHeartRate'] = self.sessionMetrics['avg_heart_rate']
        metricsExport['Metric_MaxHeartRate'] = self.sessionMetrics['max_heart_rate']
        metricsExport['Metric_StartPosition_Lat'] = self.sessionMetrics['start_position_lat_deg']
        metricsExport['Metric_StartPosition_Long'] = self.sessionMetrics['start_position_long_deg']
        # Heart Rate - Metrics only for whole session
        timeHRzones = self.lapHRzonesDF['time_in_hr_zone'].iloc[-1]
        totalTimeForHRzones = np.sum(timeHRzones) # Might be slightly different than session time
        HRzonesBounds = self.lapHRzonesDF['hr_zone_high_boundary'].iloc[-1]
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
        
        # Finally return the metrics
        return metricsExport
    
    #%% Data Analysis functions
    