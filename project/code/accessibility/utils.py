import os
import pandas as pd
import sys
import veroviz as vrv

def getDirectory(experiment_id: str):
    '''
    Return path to the experiments folder.
    Assumes current directory has subdirectories code, data and experiments

    Parameters
    ----------
    experiment_id: str
        unique identifier for the experiment being run
    
    Returns
    -------
    directory: str
        path to the folder with the experiment |
        should contain origins.csv, destinations.csv and results.csv

    '''
    directory = f"../../experiments/{experiment_id}/"
    try:
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Experiment {experiment_id} not found!")
        else:
            return directory
    except FileNotFoundError as e:
        print(e)
        directory = input("Enter the correct path to the experiment folder: ")
        return directory

def getResults(directory: str):
    '''
    Return pd dataframe taken from results.csv within the experiment folder

    Parameters
    ----------
    directory
        path to the experiment folder

    Notes
    -----
    Example usage: 
    experiment_id = "BNMC" | 
    directory = f"../../experiments/{experiment_id}/" |
    all_routes = getResults(directory)

    '''
    results_path = directory+"results.csv"
    try:
        if not os.path.exists(results_path):
            raise FileNotFoundError(f"Results of experiment not found!")
        else:
            return pd.read_csv(results_path)
    except FileNotFoundError as e:
        print(e)
        #TODO replace with instructions on how to run the experiment and get results
        sys.exit(1)

def checkPreference(preference: str):
    '''
    Check that the preference entered is valid
    '''
    try:
        if preference != "min_time" or preference != "min_walk":
            raise ValueError(f"Invalid Preference. Preference must be min_time or min_walk")
        else:
            return preference
    except ValueError as e:
        print(e)
        preference = input("Enter a correct preference: ")
        return preference
    
def getExperimentOD(directory:str):
    '''
    Returns a single row from origins and destinations dataframes
    Assme that if the directory exists then the origins and destinations files also exist
    '''
    origins = pd.read_csv(f"{directory}origins.csv")
    destinations = pd.read_csv(f"{directory}destinations.csv")

    return origins, destinations

def getAPIKey():
    '''
    Check veroviz version and return api key
    '''
    print(vrv.checkVersion())
    return os.environ['ORSKEY']