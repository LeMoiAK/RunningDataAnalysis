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
import numpy as np
import glob
import json
import datetime
from zipfile import ZipFile
import os

#%% StandardDataImporter class
class StandardDataImporter:
    """
    This class defines methods common to all DataImporters. Other importers can
    then inherit from it and define their own methods.
    """
    
    #%% Data Import Methods
    def importActivityFiles(self, listActFitFiles):
        """
        Imports the activity files and aggregates the metrics into a single table.
        listActFitFiles is given and contains the list of all fit files to consider
        Then all files are read and filtered to only the running activities.
        Other fit files are deleted. Finally, a dataFrame with all metrics is generated.
        """
        
        # Import the fit files with the ActivityImporter
        activityImporters = []
        activityFiles = []
        NONactivityFiles = []
        NONrunningFiles = []
        NFitFiles = len(listActFitFiles)
        Utils.printProgressBar(0, NFitFiles, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, ActFitFile in enumerate(listActFitFiles):
            thisImporter = ActivityImporter(ActFitFile)
            # Check the validity of the imported fit file
            if thisImporter.ObjInfo['DecodeSuccess'] and thisImporter.ObjInfo['isSportActivity']:
                # This is valid activity, we keep all valid files but import only running activities
                if 'running' in thisImporter.ObjInfo['sport']:
                    activityImporters.append(thisImporter)
                    activityFiles.append(ActFitFile)
                else:
                    NONrunningFiles.append(ActFitFile)
            else:
                NONactivityFiles.append(ActFitFile)
            Utils.printProgressBar(i + 1, NFitFiles, prefix = 'Progress:', suffix = 'Complete', length = 50)

        # Finally, go through the Imported Activities, get their metrics and create a table
        metricsList = []
        for activity in activityImporters:
            metricsList.append(activity.exportUsefulMetrics())
        self.activityMetricsDF = pd.DataFrame(metricsList)
        
        # Save the list of importers and their respective files
        self.activityImporters = activityImporters
        self.activityFiles = activityFiles
        
        # Finally returns the list of files to be deleted because they are not activity files
        return (NONactivityFiles, NONrunningFiles)
    
    #%% Data Export Methods
    def getBestPacePerTimeEffortForPeriod(self, periodStart, periodEnd):
        """
        Finds the best effort distances and paces among all activities in the
        given time frame defined by periodStart and periodEnd.
        """
        
        # Find the activities that are in the period
        idxActivities = self.activityMetricsDF.index[(periodStart < self.activityMetricsDF["Metric_StartTime"]) & (self.activityMetricsDF["Metric_StartTime"] <= periodEnd)]
        # Get their times and paces into an array
        Nactivities = len(idxActivities)
        NTimes = len(self.activityImporters[idxActivities[0]].bestEffortData['Time_Times'])
        timesNamesList = self.activityImporters[idxActivities[0]].bestEffortData['Time_Names']
        timesValuesArray = np.array(self.activityImporters[idxActivities[0]].bestEffortData['Time_Times'])

        bestDistancePerTime = np.ones((Nactivities,NTimes)) * np.nan
        bestPacePerTime = np.empty((Nactivities,NTimes), dtype='datetime64[us]')

        for i in np.arange(Nactivities):
            thisActIdx = idxActivities[i]
            bestDistancePerTime[i, :] = np.array(list(self.activityImporters[thisActIdx].bestEffortData['Time_Distances'].values()))
            bestPacePerTime[i, :] = np.array(self.activityImporters[thisActIdx].bestEffortData['Time_Paces'], dtype='datetime64')
            
        # Then get the best pace among all the activities and return it
        bestDistancePerTimeAllActivities = bestDistancePerTime.max(axis=0)
        bestPacePerTimeAllActivities = bestPacePerTime.min(axis=0)
        
        return (timesNamesList, timesValuesArray, bestDistancePerTimeAllActivities, bestPacePerTimeAllActivities)
    
    def getBestPacePerDistanceEffortForPeriod(self, periodStart, periodEnd):
        """
        Finds the best effort paces  per distance among all activities in the
        given time frame defined by periodStart and periodEnd.
        """
        
        # Find the activities that are in the period
        idxActivities = self.activityMetricsDF.index[(periodStart < self.activityMetricsDF["Metric_StartTime"]) & (self.activityMetricsDF["Metric_StartTime"] <= periodEnd)]
        # Get their times and paces into an array
        Nactivities = len(idxActivities)
        NTimes = len(self.activityImporters[idxActivities[0]].bestEffortData['Distance_Distances'])
        distancesNamesList = self.activityImporters[idxActivities[0]].bestEffortData['Distance_Names']
        distancesValuesArray = np.array(self.activityImporters[idxActivities[0]].bestEffortData['Distance_Distances'])

        bestTimePerDistance = np.ones((Nactivities,NTimes)) * np.nan
        bestPacePerDistance = np.empty((Nactivities,NTimes), dtype='datetime64[us]')

        for i in np.arange(Nactivities):
            thisActIdx = idxActivities[i]
            bestTimePerDistance[i, :] = np.array(list(self.activityImporters[thisActIdx].bestEffortData['Distance_Times'].values()))
            bestPacePerDistance[i, :] = np.array(self.activityImporters[thisActIdx].bestEffortData['Distance_Paces'], dtype='datetime64')
            
        # Then get the best pace among all the activities and return it
        bestTimePerDistanceAllActivities = bestTimePerDistance.max(axis=0)
        bestPacePerDistanceAllActivities = bestPacePerDistance.min(axis=0)
        
        return (distancesNamesList, distancesValuesArray, bestTimePerDistanceAllActivities, bestPacePerDistanceAllActivities)

#%% GarminDataImporter class
class GarminDataImporter(StandardDataImporter): # Inherits from StandardDataImporter
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
        Imports the user profile and makes somes calculations like age and unit conversions.
        New data seems a different format than previously so makes it a bit harder to find all the data
        """
        userFolder = self.rootFolder + "\\DI_CONNECT\\DI-Connect-User"
        with open(userFolder + '\\user_profile.json', 'r') as f:
            self.userProfile = json.load(f)
        self.userProfile['birthDate'] = datetime.datetime.strptime(self.userProfile['birthDate'], '%Y-%m-%d')
        self.userProfile['age'] = Utils.getAge(self.userProfile['birthDate'])
        
        with open(userFolder + '\\' + self.userProfile['userName'] + '-social-profile.json', 'r') as f:
            socialProfile = json.load(f)
        self.userProfile['profileId'] = socialProfile['profileId'] # To get the Profile ID to get biometrics data file path
        
        # Add the handedness (Heart Rate Zones not available anymore)
        with open(userFolder + '\\user_settings.json', 'r') as f:
            userSettings = json.load(f)
        self.userProfile['handedness'] = userSettings['handedness']
        
        wellnessFolder = self.rootFolder + "\\DI_CONNECT\\DI-Connect-Wellness"
        with open(wellnessFolder + '\\' + str(self.userProfile['profileId']) + '_userBioMetricProfileData.json', 'r') as f:
            wellnessData = json.load(f)[0]
        self.userProfile['weight'] = Utils.valuesOrDict(wellnessData, 'weight', np.nan) / 1e3 # Weight saved in g
        self.userProfile['height'] = Utils.valuesOrDict(wellnessData, 'height', np.nan) / 1e2 # Height saved in cm
            
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
        Redefine method from parent class. For the GarminDataImporter, we need to
        extract the zip file containing all files.
        
        Imports the activity files and aggregates the metrics into a single table.
        There are several steps. First the zip files are extracted into the same folder.
        Then all files are read and filtered to only the running activities.
        Other fit files are deleted. Finally, a dataFrame with all metrics is generated.
        """
        
        # get list of zip files containing the fit files
        activityFolder = self.rootFolder + "\\DI_CONNECT\\DI-Connect-Uploaded-Files"
        listActZipFiles = glob.glob(activityFolder + "\\*.zip")

        # Extracts all the known zip files
        for thisZipFile in listActZipFiles:
            with ZipFile(thisZipFile, 'r') as zip:
                zip.extractall(path=activityFolder)

        # Get a list of all the fit files
        listActFitFiles = glob.glob(activityFolder + "\\*.fit")

        # Import the fit files using the parent class
        (NONactivityFiles, NONrunningFiles) = super().importActivityFiles(listActFitFiles)
        
        # Stopped removing files that are not activity files. This should not be
        # an automatic process.
        
                
#%% WatchOffloadDataImporter class
class WatchOffloadDataImporter(StandardDataImporter): # Inherits from StandardDataImporter
    """
    This class imports data from all files contained within the folder of data offloaded manually by the user.
    """
    
    def __init__(self, folderPath, importActivities=True):
        """
        Constructor of the WatchOffloadDataImporter class

        Parameters
        ----------
        folderPath : String
            Path to the root folder of the Folder containing the watch offload.
        importActivities : String, optional
            Bool on whether to import the activity files. WARNING IS SLOW. The default is True.

        Returns
        -------
        None.

        """        
        
        # Save folder for us in other methods
        self.rootFolder = folderPath
        
        # Imports the activities if requested
        if importActivities:
            self.importActivityFiles()
    
    def importActivityFiles(self):
        """
        Redefine method from parent class. For the WatchOffloadDataImporter, we need to
        just need to get the list of files contained within the folder.
        
        Imports the activity files and aggregates the metrics into a single table.
        All files are read and filtered to only the running activities.
        Finally, a dataFrame with all metrics is generated.
        """
        
        # Get a list of all the fit files
        listActFitFiles = glob.glob(self.rootFolder + "\\*.fit")

        # Import the fit files using the parent class
        (NONactivityFiles, NONrunningFiles) = super().importActivityFiles(listActFitFiles)
        
        # No need to delete or remove the fit files here because cleaning is done elsewhere
        # Might decide to add cleaning here as well, but wanted to keep cleaning separate so folders can be separate.        