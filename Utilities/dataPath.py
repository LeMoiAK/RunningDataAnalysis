# -*- coding: utf-8 -*-
"""
Utilities related to the data path

Created on Thu Jun 14 21:30:00 2023

@author: LeMoiAK
"""

def getDataPath():
    """Gets the path to the data folder from the designated text file that will be ignored in GIT"""
    txtFilePath = __file__.split("dataPath.py")[0] + "dataFolderPath.txt"
    with open(txtFilePath, "r") as f:
        return f.readline() # Returns the file path