'''
Usage:
cd project/
python code/ai.py --experiment_id=BNMC
'''

#MODULES
import os
import argparse
import pandas as pd
import sys
import veroviz as vrv
import numpy as np
#FUNCTIONS
from accessibility.utils import getDirectory, getExperimentOD, getAPIKey, getAccessibilityScores
ORS_API_KEY = getAPIKey()

def accessibility(origins: pd.DataFrame, destinations: pd.DataFrame, accessibility_scores: np.ndarray):
    '''
    Parameters
    ----------
    origins: pd.DataFrame
        stores information and location of origin points
    destinations: pd.DataFrame
        stores information and location of destination points
    results: pd.DataFrame
        stores information about all routes produced by the experiments
    accessibility_scores: np.ndarray
        array which stores the accessibility score for each origin (0 to 1)

    Returns
    -------

    '''
    # Determine the maximum values in 'start_name' and 'poi_name' columns
    number_of_origins = origins['name'].max()

    accessibility_df = pd.DataFrame({'name': np.arange(1,number_of_origins+1),\
                                        'lat' : origins['lat'].values,
                                        'lon' : origins['lon'].values,
                                      'accessibility_score': accessibility_scores})

    full_accessible_df = accessibility_df[accessibility_df['accessibility_score'] == 1]
    partial_accessible_df = accessibility_df[(accessibility_df['accessibility_score'] < 1) & (accessibility_df['accessibility_score'] > 0)]
    not_accessible_df = accessibility_df[accessibility_df['accessibility_score'] == 0]

    full_accessible_nodesdf = vrv.initDataframe('nodes')
    partial_accessible_nodesdf = vrv.initDataframe('nodes')
    not_accessible_nodesdf = vrv.initDataframe('nodes')

    destinations_nodesdf = vrv.initDataframe('nodes') 
    # transform pandas dfs to nodes dfs for origins to be used in leaflet 
    full_accessible_nodesdf['id'] = full_accessible_df['name']
    full_accessible_nodesdf['lat'] = full_accessible_df['lat']
    full_accessible_nodesdf['lon'] = full_accessible_df['lon']
    full_accessible_nodesdf['popupText'] = full_accessible_df['name']
    full_accessible_nodesdf['leafletIconPrefix'] = 'custom'
    full_accessible_nodesdf['leafletIconType'] = '20-white-12'
    full_accessible_nodesdf['leafletColor'] = 'green'
    full_accessible_nodesdf['leafletIconText'] = full_accessible_df['accessibility_score']
    full_accessible_nodesdf['cesiumIconType'] = 'pin'
    full_accessible_nodesdf['cesiumColor'] = 'green'
    full_accessible_nodesdf['cesiumIconText'] = None

    partial_accessible_nodesdf['id'] = partial_accessible_df['name']
    partial_accessible_nodesdf['lat'] = partial_accessible_df['lat']
    partial_accessible_nodesdf['lon'] = partial_accessible_df['lon']
    partial_accessible_nodesdf['popupText'] = partial_accessible_df['name']
    partial_accessible_nodesdf['leafletIconPrefix'] = 'custom'
    partial_accessible_nodesdf['leafletIconType'] = '20-white-12'
    partial_accessible_nodesdf['leafletColor'] = 'orange'
    partial_accessible_nodesdf['leafletIconText'] = partial_accessible_df['accessibility_score']
    partial_accessible_nodesdf['cesiumIconType'] = 'pin'
    partial_accessible_nodesdf['cesiumColor'] = 'green'
    partial_accessible_nodesdf['cesiumIconText'] = None

    not_accessible_nodesdf['id'] = not_accessible_df['name']
    not_accessible_nodesdf['lat'] = not_accessible_df['lat']
    not_accessible_nodesdf['lon'] = not_accessible_df['lon']
    not_accessible_nodesdf['popupText'] = not_accessible_df['name']
    not_accessible_nodesdf['leafletIconPrefix'] = 'custom'
    not_accessible_nodesdf['leafletIconType'] = '20-white-12'
    not_accessible_nodesdf['leafletColor'] = 'red'
    not_accessible_nodesdf['leafletIconText'] = not_accessible_df['accessibility_score']
    not_accessible_nodesdf['cesiumIconType'] = 'pin'
    not_accessible_nodesdf['cesiumColor'] = 'green'
    not_accessible_nodesdf['cesiumIconText'] = None

    # transform pandas df to nodes df for destination to be used in leaflet 
    destinations_nodesdf['id'] = destinations['name']
    destinations_nodesdf['lat'] = destinations['lat']
    destinations_nodesdf['lon'] = destinations['lon']
    destinations_nodesdf['popupText'] = destinations['name']
    destinations_nodesdf['leafletIconPrefix'] = 'custom'
    destinations_nodesdf['leafletIconType'] = '20-white-9'
    destinations_nodesdf['leafletColor'] = 'purple'
    destinations_nodesdf['leafletIconText'] = destinations['block_id']
    destinations_nodesdf['cesiumIconType'] = 'pin'
    destinations_nodesdf['cesiumColor'] = 'red'
    destinations_nodesdf['cesiumIconText'] = None

    #create the map

    accessibility_map = vrv.createLeaflet(
    mapObject=None,
    nodes = destinations_nodesdf,
    mapFilename = "accessibility_map.html")

    if not full_accessible_df.empty:
        accessibility_map = vrv.createLeaflet(
        mapObject=accessibility_map,
        nodes = full_accessible_nodesdf,
        mapFilename = "accessibility_map.html")

    if not partial_accessible_nodesdf.empty:
        accessibility_map = vrv.createLeaflet(
        mapObject=accessibility_map,
        nodes = partial_accessible_nodesdf,
        mapFilename = "accessibility_map.html")

    if not not_accessible_nodesdf.empty:
        accessibility_map = vrv.createLeaflet(
        mapObject=accessibility_map,
        nodes = not_accessible_nodesdf,
        mapFilename = "accessibility_map.html")
        
    return accessibility_map

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Experiment Details")
    parser.add_argument('experiment_id', type=str, help='Experiment ID')
    args = parser.parse_args()

    directory = getDirectory(args.experiment_id)
    origins, destinations = getExperimentOD(directory)
    scores = getAccessibilityScores(directory)

    # Visualize the origin and destination points
    accessibility = accessibility(origins, destinations, scores)