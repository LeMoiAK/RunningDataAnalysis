def getDataPath():
    """Gets the path to the data folder from the designated text file that will be ignored in GIT"""
    with open("dataFolderPath.txt", "r") as f:
        return f.readline() # Returns the file path