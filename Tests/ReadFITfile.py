# Script to test the import of a .fit file using the Garmin sdk
from garmin_fit_sdk import Decoder, Stream, Profile
from Utilities.dataPath import getDataPath
import numpy as np
import pandas as pd
import seaborn as sns
import datetime

###############################################################################
# Define the Activity importer class
class ActivityImporter:
    """This class imports a single .fit activity given a file path.
    It also contains functions to create advanced metrics.
    """
    
    def __init__(self, filePath):
        """Contructor. Give path to the .fit file as input"""
        
        # Declare Main variables so we know they exist
        self.FileInfo = dict()
        self.ObjInfo = dict()
        
        self.FileInfo['filePath'] = filePath
        
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
        self.extractMetrics(messages)
            
        # Puts the records into the DataFrame format
        self.transformRecordsToDataFrame(messages['record_mesgs'])
            
        
    def transformRecordsToDataFrame(self, recordMessages):
        """Transforms the records messages into a pandas dataFrame and performs
        all operations on the data such as unit conversion"""
        
        # Get into dataFrame
        df = pd.DataFrame(recordMessages)
        
        # Get Cadence in Steps Per Minute
        # https://forums.garmin.com/developer/fit-sdk/f/discussion/288454/fractional-cadence-values
        if ('cadence' in df.columns) and ('fractional_cadence' in df.columns):
            # Raw cadence is the "RPM" of the legs, which must be multiplied by 2
            # to get the number of steps. Fractional_cadence allows odd numbers
            df['cadence_spm'] = (df['cadence'] + df['fractional_cadence'])*2 # Fractional cadence allows to get
        
        # Get position in degrees instead of semicircles
        # https://forums.garmin.com/developer/fit-sdk/f/discussion/280125/record-the-latitude-and-longitude-format-of-the-message
        if ('position_lat' in df.columns) and ('position_long' in df.columns):
            df['position_lat_deg']  = df['position_lat'] * ( 180.0 / 2**31 )
            df['position_long_deg'] = df['position_long'] * ( 180.0 / 2**31 )
        
        # Drop 136 and 135 columns
        if 136 in df.columns:
            df.drop(columns=136, inplace=True) # Drops 136 because it is exactly the heart rate
        if 135 in df.columns:
            df.drop(columns=135, inplace=True) # Drops 135 because no clue what it actually is
            
        # Drop enhanced fields because they are of no use for running
        # https://www.thisisant.com/forum/viewthread/4561
        if 'enhanced_speed' in df.columns:
            df.drop(columns='enhanced_speed', inplace=True)
        if 'enhanced_altitude' in df.columns:
            df.drop(columns='enhanced_altitude', inplace=True)
        
        # Get pace in min/km and speed in kph
        if 'speed' in df.columns:
            df['speed_kph']  = df['speed'] * 3.6
            df['pace'] = df['speed'].apply(lambda speed: pd.to_datetime(1000/max(speed, 1/3.6), unit='s'))
        
        # Save df into object name
        self.data = df
        
    def extractMetrics(self, messages):
        """
        Extracts user information, file information, and metrics
        """
        
        # Get User Information like age, height, weight
        self.UserProfile = messages['user_profile_mesgs'][0]
        # Convert sleep and wake times in datetime
        self.UserProfile['sleep_time_TD'] = pd.Timestamp(self.UserProfile['sleep_time'], unit='s')
        self.UserProfile['wake_time_TD'] = pd.Timestamp(self.UserProfile['wake_time'], unit='s')
        
        




###############################################################################
filePath = getDataPath() + "\\11329404102_ACTIVITY.fit"
print(filePath)

actImp = ActivityImporter(filePath)

# Plot the pace graph to check
actImp.data['pace'].plot(ylim=(datetime.datetime(1970, 1, 1, 00, 7), min(actImp.data['pace']) - datetime.timedelta(seconds=30)))

