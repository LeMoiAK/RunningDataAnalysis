# -*- coding: utf-8 -*-
"""
GarminDataImporter class
Class containing all functions and properties to import all the data from a Garmin
personal data request. This contains activities, heart and sleep data, Race Predictor, etc.

Created on Sat Jun 17 23:18:42 2023

@author: LeMoiAK
"""

#%% Required modules
from Utilities.ActivityImporter import ActivityImporter
import Utilities.Functions as Utils
import pandas as pd
import glob
import json
import datetime
from zipfile import ZipFile
import os

#%% GarminDataImporter class
class GarminDataImporter:
    """
    This class imports data from all files contained within the folder of data provided by Garmin.
    """
    
    def __init__(self, folderPath, importActivities=True):
        """
        Constructor of the GarminDataImporter class

        Parameters
        ----------
        folderPath : String
            Path to the root folder of the Garmin Data.
        importActivities : String, optional
            Bool on whether to import the activity files. WARNING IS SLOW. The default is True.

        Returns
        -------
        None.

        """        
        
        # Save folder for us in other methods
        self.rootFolder = folderPath
        
        # Loads the user profile like name and age
        self.importUserProfile()
        
        # Load Performance Metrics
        self.importPerformanceMetrics()
        
        # Load the personal records
        self.importPersonalRecords()
        
        # Imports the activities if requested
        if importActivities:
            self.importActivityFiles()
        
    
    
    #%% Data Import method
    def importUserProfile(self):
        """
        Imports the user profile and makes somes calculations like age and unit conversions
        """
        userFolder = self.rootFolder + "\\DI_CONNECT\\DI-Connect-User"
        with open(userFolder + '\\user_profile.json', 'r') as f:
            self.userProfile = json.load(f)
        self.userProfile['weight'] = self.userProfile['weight'] / 1e3 # Weight saved in g
        self.userProfile['height'] = self.userProfile['height'] / 1e2 # Height saved in cm
        self.userProfile['birthDate'] = datetime.datetime.strptime(self.userProfile['birthDate'], '%Y-%m-%d')
        self.userProfile['age'] = Utils.getAge(self.userProfile['birthDate'])
        
        # Add the Heart Rate Zones and handedness
        with open(userFolder + '\\user_settings.json', 'r') as f:
            userSettings = json.load(f)
        self.userProfile['handedness'] = userSettings['handedness']
        self.userProfile['heartRateZones'] = userSettings['heartRateZones'][0]
    
    def importPerformanceMetrics(self):
        """
        Function to import the performance metrics generated by Garmin.
        This is mainly the race pace prediction and the VO2 max estimation.
        """
        
        # Create folder name and find files in it corresponding to each category
        performanceMetricsFolder = self.rootFolder + "\\DI_CONNECT\\DI-Connect-Metrics"
        listRacePredictorFiles = glob.glob(performanceMetricsFolder + "\\RunRacePredictions_*.json")
        listMetricsFiles = glob.glob(performanceMetricsFolder + "\\MetricsMaxMetData_*.json")
        
        # Load Race Predictions
        dfs = [] # an empty list to store the data frames
        for file in listRacePredictorFiles:
            data = pd.read_json(file, lines=False) # read data frame from json file
            dfs.append(data) # append the data frame to the list

        self.df_RacePred = pd.concat(dfs, ignore_index=True) # concatenate all the data frames in the list.
        self.df_RacePred.set_index('timestamp', inplace=True)
        self.df_RacePred.sort_values('timestamp', inplace=True)
        
        self.df_RacePred['raceTime5K_DT'] = pd.to_datetime(self.df_RacePred['raceTime5K'], unit='s')
        self.df_RacePred['raceTime10K_DT'] = pd.to_datetime(self.df_RacePred['raceTime10K'], unit='s')
        self.df_RacePred['raceTimeHalf_DT'] = pd.to_datetime(self.df_RacePred['raceTimeHalf'], unit='s')
        self.df_RacePred['raceTimeMarathon_DT'] = pd.to_datetime(self.df_RacePred['raceTimeMarathon'], unit='s')

        self.df_RacePred['raceTime5K_Pace'] = Utils.speedToPace(5.0e3 / self.df_RacePred['raceTime5K'])
        self.df_RacePred['raceTime10K_Pace'] = Utils.speedToPace(10.0e3 / self.df_RacePred['raceTime10K'])
        self.df_RacePred['raceTimeHalf_Pace'] = Utils.speedToPace(Utils.halfMarathonDistance / self.df_RacePred['raceTimeHalf'])
        self.df_RacePred['raceTimeMarathon_Pace'] = Utils.speedToPace(Utils.fullMarathonDistance / self.df_RacePred['raceTimeMarathon'])
        
        # Load VO2 max estimation and max MET (less discrete)
        dfs = [] # an empty list to store the data frames
        for file in listMetricsFiles:
            data = pd.read_json(file, lines=False) # read data frame from json file
            dfs.append(data) # append the data frame to the list

        self.df_MetVO2 = pd.concat(dfs, ignore_index=True) # concatenate all the data frames in the list.
        self.df_MetVO2.set_index('updateTimestamp', inplace=True)
        self.df_MetVO2.sort_values('updateTimestamp', inplace=True)

    def importPersonalRecords(self):
        """
        Imports the User's personal records, filters to running only then
        puts them in their respective categories.
        """
        
        fitnessFolder = self.rootFolder + "\\DI_CONNECT\\DI-Connect-Fitness"
        with open(fitnessFolder + '\\' + self.userProfile['userName'] + '_personalRecord.json', 'r') as f:
            tmp = json.load(f)
        df_PR = pd.DataFrame(tmp[0]['personalRecords'])
        # Filter it to Running only
        df_PR = df_PR.loc[df_PR['personalRecordType'].apply(lambda rType: isinstance(rType , str) and ('Run' in rType or 'Marathon' in rType) )]
        # Make dates and sets as index
        df_PR['activityStartTime'] = pd.to_datetime(df_PR['prStartTimeGMT'])
        df_PR.set_index('activityStartTime', inplace=True)
        # Put PR into categories for easier access and understanding + create metrics
        self.personalRecord = dict()
        # Farthest Run
        df_PR_FarthestRun = df_PR.loc[df_PR['personalRecordType'] == 'Farthest Run'].copy()
        df_PR_FarthestRun['Distance_km'] = df_PR_FarthestRun['value'] / 1.0e3
        self.personalRecord['FarthestRun'] = df_PR_FarthestRun
        # 1km time
        df_PR_1km = df_PR.loc[df_PR['personalRecordType'] == 'Best 1km Run'].copy()
        df_PR_1km['Time'] = df_PR_1km['value']
        df_PR_1km['Time_DT'] = pd.to_datetime(df_PR_1km['Time'], unit='s')
        df_PR_1km['Pace'] = Utils.speedToPace(1.0e3 / df_PR_1km['value'])
        self.personalRecord['1km'] = df_PR_1km
        # 5km time
        df_PR_5km = df_PR.loc[df_PR['personalRecordType'] == 'Best 5km Run'].copy()
        df_PR_5km['Time'] = df_PR_5km['value']
        df_PR_5km['Time_DT'] = pd.to_datetime(df_PR_5km['Time'], unit='s')
        df_PR_5km['Pace'] = Utils.speedToPace(5.0e3 / df_PR_5km['value'])
        self.personalRecord['5km'] = df_PR_5km
        # 10 km time
        df_PR_10km = df_PR.loc[df_PR['personalRecordType'] == 'Best 10km Run'].copy()
        df_PR_10km['Time'] = df_PR_10km['value']
        df_PR_10km['Time_DT'] = pd.to_datetime(df_PR_10km['Time'], unit='s')
        df_PR_10km['Pace'] = Utils.speedToPace(10.0e3 / df_PR_10km['value'])
        self.personalRecord['10km'] = df_PR_10km
        # Half Marathon time
        df_PR_HM = df_PR.loc[df_PR['personalRecordType'] == 'Best Half Marathon'].copy()
        df_PR_HM['Time'] = df_PR_HM['value']
        df_PR_HM['Time_DT'] = pd.to_datetime(df_PR_HM['Time'], unit='s')
        df_PR_HM['Pace'] = Utils.speedToPace(Utils.halfMarathonDistance / df_PR_HM['value'])
        self.personalRecord['HM'] = df_PR_HM
        
    def importActivityFiles(self):
        """
        Imports the activity files and aggregates the metrics into a single table.
        There are several steps. First the zip files are extracted into the same folder.
        Then all files are read and filtered to only the running activities.
        Other fit files are deleted. Finally, a dataFrame with all metrics is generated.
        """
        
        # get list of zip files containing the fit files
        activityFolder = self.rootFolder + "\\DI_CONNECT\\DI-Connect-Fitness-Uploaded-Files"
        listActZipFiles = glob.glob(activityFolder + "\\*.zip")

        # Extracts all the known zip files
        for thisZipFile in listActZipFiles:
            with ZipFile(thisZipFile, 'r') as zip:
                zip.extractall(path=activityFolder)

        # Get a list of all the fit files
        listActFitFiles = glob.glob(activityFolder + "\\*.fit")

        # Import the fit files with the ActivityImporter
        activityImporters = []
        activityFiles = []
        NONactivityFilesToRemove = []
        NFitFiles = len(listActFitFiles)
        Utils.printProgressBar(0, NFitFiles, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, ActFitFile in enumerate(listActFitFiles):
            thisImporter = ActivityImporter(ActFitFile)
            # Check the validity of the imported fit file
            if thisImporter.ObjInfo['DecodeSuccess'] and thisImporter.ObjInfo['isSportActivity'] and 'running' in thisImporter.ObjInfo['sport']:
                # This is valid
                activityImporters.append(thisImporter)
                activityFiles.append(ActFitFile)
            else:
                NONactivityFilesToRemove.append(ActFitFile)
            Utils.printProgressBar(i + 1, NFitFiles, prefix = 'Progress:', suffix = 'Complete', length = 50)

        # Delete all extracted files that are not valid activities
        for fileToRM in NONactivityFilesToRemove:
            if os.path.isfile(fileToRM):
                os.remove(fileToRM)

        # Finally, go through the Imported Activities, get their metrics and create a table
        metricsList = []
        for activity in activityImporters:
            metricsList.append(activity.exportUsefulMetrics())
        self.activityMetricsDF = pd.DataFrame(metricsList)
        
        # Save the list of importers and their respective files
        self.activityImporters = activityImporters
        self.activityFiles = activityFiles