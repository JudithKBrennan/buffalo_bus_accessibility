import os
import pandas as pd
import sys
import veroviz as vrv
import numpy as np

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
        directory = input("Enter the correct path to the experiment folder, ensuring the path ends with a \ ")
        return directory

def getResults(directory: str, origin_id: int, destination_id: int, time: int, preference: str):
    '''
    Return a single route from the pd dataframe taken from results.csv within the experiment folder

    '''
    results_path = directory+"results.csv"
    try:
        if not os.path.exists(results_path):
            raise FileNotFoundError(f"Results of experiment not found!")
        else:
            all_routes = pd.read_csv(results_path)
            filtered_routes = all_routes[(all_routes['origin_id'] == origin_id) & 
                                (all_routes['destination_id'] == destination_id) &
                                (all_routes['start_time'] >= float(time)) &
                                (all_routes['end_time'] <= float((time + 3600))) &
                                (all_routes['preference'] == preference)
                                ]
            earliest_route = filtered_routes.loc[filtered_routes['start_time'].idxmin()]
            
            return earliest_route

    except FileNotFoundError as e:
        #TODO replace with instructions on how to run the experiment and get results
        sys.exit(e)

def checkPreference(preference: str):
    '''
    Check that the preference entered is valid
    '''
    try:
        if not ((preference == "min_time") or (preference == "min_walk")):
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

def getAllRoutes(directory: str):
    '''
    Read dataframe with all routes from the experiment
    '''
    results_path = directory+"results.csv"
    try:
        if not os.path.exists(results_path):
            raise FileNotFoundError(f"Results of experiment not found!")
        else:
            all_routes = pd.read_csv(results_path)
            return all_routes
    except FileNotFoundError as e:
        #TODO replace with instructions on how to run the experiment and get results
        sys.exit(e)

def getAccessibilityScores(directory: str):
    '''
    Read list of all the acecssiblity scores
    '''
    score_path = directory+"AI\\ai_1.txt"
    try:
        if not os.path.exists(score_path):
            raise FileNotFoundError(f"Accessibility scores not found!")
        else:
            data = np.loadtxt(score_path, delimiter=',')
            return data
    except FileNotFoundError as e:
        #TODO replace with instructions on how to run the file to get accessibility scores
        sys.exit(e)