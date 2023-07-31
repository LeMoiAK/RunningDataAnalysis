# -*- coding: utf-8 -*-
"""
Try to understand the Relative Effort metric calculated by Strava.
After some research, it seems it is based solely on Heart Rate and time spent
in each HR zone.

Created on Fri Jul 28 21:21:59 2023

@author: LeMoiAK
"""

#%% import required libraries
import pandas as pd
import numpy as np

from Utilities.GarminDataImporter import GarminDataImporter,WatchOffloadDataImporter
from Utilities.ActivityImporter import ActivityImporter
from Utilities.ActivityPlotter import ActivityPlotter as actp
import Utilities.Functions as Utils
import seaborn as sns

#%% Import the run data to get the HR metrics
folderPath = Utils.getDataPath() + "\\WatchOffloadRaw"
print(folderPath)

StravaHRzones = dict(
    Zone_1_Endurance= [0, 129],
    Zone_2_Moderate= [130, 161],
    Zone_3_Tempo= [162, 177],
    Zone_4_Threshold= [178, 195],
    Zone_5_Anaerobic= [194, np.inf]
    )

gdi = WatchOffloadDataImporter(folderPath, importActivities=True, activityImporterOptions=dict(estimateBestEfforts=False, importWeather=False, customHRzones=StravaHRzones) )
# Then get the metrics from these runs
metricsDF = gdi.activityMetricsDF

#%% Import the metrics from Strava
stravaActivitiesPath = Utils.getDataPath() + "\\2023_07_28_Strava\\activities.csv"
# Real only the potentially interesting columns
stravaDF = pd.read_csv(stravaActivitiesPath, usecols = ['Activity Date', 'Activity Name', 'Activity Type', 'Elapsed Time', 
                                                        'Max Heart Rate', 'Relative Effort', 'Moving Time', 'Distance', 
                                                        'Average Speed', 'Average Heart Rate', 'Calories'])

# Filter down to runs with Relative Effort available only
stravaDF.dropna(inplace=True) # Remove NaN, for instance activities without RE
stravaDF['Activity Date'] = pd.to_datetime(stravaDF['Activity Date'], utc=True)
stravaDF = stravaDF[ (stravaDF['Activity Type'] == 'Run') ]
stravaDF_light = stravaDF[['Activity Date', 'Relative Effort']].copy()
stravaDF_light['Metric_StartTime'] = stravaDF_light['Activity Date']

#%% Merge Metrics table together
metricsDF_light = metricsDF[['Metric_StartTime', 'Metric_TotalTimerTime', 'Metric_TotalDistance', 'HR_Time_Zone_0', 'HR_Time_Zone_1', 'HR_Time_Zone_2', 'HR_Time_Zone_3', 'HR_Time_Zone_4', 'HR_Time_Zone_5', 'HR_Time_Zone_6' ]]

fullDF = pd.merge(metricsDF_light, stravaDF_light, on='Metric_StartTime', how='inner')

#%% Now data exploration
sns.pairplot(fullDF)

#%% Create linear model of RE as a function of time in each zone
X = fullDF[['HR_Time_Zone_0', 'HR_Time_Zone_1', 'HR_Time_Zone_2',
            'HR_Time_Zone_3','HR_Time_Zone_4', 'HR_Time_Zone_5',
            'HR_Time_Zone_6']]
y = fullDF['Relative Effort']

# Split data into test and train
# Not so great to have only 173 data points
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=101)

# Train the model
from sklearn.linear_model import LinearRegression
lm = LinearRegression()
lm.fit(X_train, y_train)

# Evaluate quality of model
coeff_df = pd.DataFrame(lm.coef_, X.columns, columns=['Coefficient'])
y_pred = lm.predict(X_test)
from sklearn import metrics
print('MAE:', metrics.mean_absolute_error(y_test, y_pred))
print('MSE:', metrics.mean_squared_error(y_test, y_pred))
print('RMSE:', np.sqrt(metrics.mean_squared_error(y_test, y_pred)))

yDF = pd.DataFrame(dict(trueValue=y_test, prediction=y_pred))
sns.scatterplot(data=yDF, x='trueValue', y='prediction')

#%% Get confidence intervals on the regression coefficients
from scipy import stats
alpha = 0.05
coefs = np.r_[[lm.intercept_], lm.coef_]
X_aux = X_train.copy()
X_aux.insert(0, 'const', 1)
# degrees of freedom
dof = -np.diff(X_aux.shape)[0]
# Student's t-distribution table lookup
t_val = stats.t.isf(alpha/2, dof)
# MSE of the residuals
mse = np.sum((y_train - lm.predict(X_train)) ** 2) / dof
# inverse of the variance of the parameters
var_params = np.diag(np.linalg.inv(X_aux.T.dot(X_aux)))
# distance between lower and upper bound of CI
gap = t_val * np.sqrt(mse * var_params)

conf_int = pd.DataFrame({'lower': coefs - gap, 'upper': coefs + gap}, index=X_aux.columns)

#%% Comments
# Seeing these results, it is obvious that it is not working and while the correlation
# should be strong, it is rather bad. The 95% confidence intervals are gigantic.
# This is surprising because we expect the formula to be rather simple and just a
# linear combination of times in each zone. A possible explanation is that zones 
# are defined differently for Garmin and Strava. This is the next path of investigation.

#%% ---------------- RE-PROCESSING HR ZONES ----------------
# After some investigation; it turns out that Strave HR zones are very different
# from Garmin HR zones, and there is even a different number of zones.
# That means the Garmin generated metrics are relatively useless and might explain
# why the above linear regression did not work well.

#%% Merge Metrics table together
metricsDF_light_Custom = metricsDF[['Metric_StartTime', 'Metric_TotalTimerTime', 'Metric_TotalDistance',
                                    'HR_Custom_Time_Zone_1_Endurance','HR_Custom_Time_Zone_2_Moderate',
                                    'HR_Custom_Time_Zone_3_Tempo','HR_Custom_Time_Zone_4_Threshold',
                                    'HR_Custom_Time_Zone_5_Anaerobic' ]]

fullDF_Custom = pd.merge(metricsDF_light_Custom, stravaDF_light, on='Metric_StartTime', how='inner')

X = fullDF_Custom[['HR_Custom_Time_Zone_1_Endurance','HR_Custom_Time_Zone_2_Moderate',
                   'HR_Custom_Time_Zone_3_Tempo','HR_Custom_Time_Zone_4_Threshold',
                   'HR_Custom_Time_Zone_5_Anaerobic']]
y = fullDF_Custom['Relative Effort']

# Split data into test and train
# Not so great to have only 173 data points
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=101)

# Train the model
from sklearn.linear_model import LinearRegression
lmCustom = LinearRegression()
lmCustom.fit(X_train, y_train)

# Evaluate quality of model
coeff_df = pd.DataFrame(lmCustom.coef_, X.columns, columns=['Coefficient'])
y_pred = lmCustom.predict(X_test)
from sklearn import metrics
print('MAE:', metrics.mean_absolute_error(y_test, y_pred))
print('MSE:', metrics.mean_squared_error(y_test, y_pred))
print('RMSE:', np.sqrt(metrics.mean_squared_error(y_test, y_pred)))

yDF = pd.DataFrame(dict(trueValue=y_test, prediction=y_pred))
sns.scatterplot(data=yDF, x='trueValue', y='prediction')