import os
import pandas as pd
import sys
import veroviz as vrv

def accessibility(origins, destinations, results):
    # Determine the maximum values in 'start_name' and 'poi_name' columns
    number_of_origins = origins['name'].max()
    number_of_destinations = destinations['name'].max()

    # Generate all possible combinations of start and end numbers
    all_combinations = pd.DataFrame([(i, j) for i in range(1, number_of_origins + 1) for j in range(1, number_of_destinations + 1)], columns=['start_name', 'poi_name'])

    # Check which combinations are not present in the dataset
    missing_combinations = all_combinations[~all_combinations.apply(lambda x: ((x['start_name'], x['poi_name']) in zip(results['start_name'], results['poi_name'])), axis=1)]

    # Rename columns
    missing_combinations.columns = ['missing_start', 'missing_end']
    
    # Calculate the count of each start point
    start_counts = missing_combinations['missing_start'].value_counts()

    # Create a DataFrame to store accessibility information
    accessibility_df = pd.DataFrame(columns=['start_point', 'accessibility_score'])

    # Check accessibility for each start point
    for start_point, count in start_counts.items():
        if count == number_of_destinations:
            accessibility_score = 0
        else:
            accessibility_score = 1 - (count/number_of_destinations)

        accessibility_df = pd.concat([accessibility_df, pd.DataFrame({'start_point': [start_point], 'accessibility_score': [accessibility_score]})], ignore_index=True)

     # Include start points not present in missing_combinations
    existing_start_points = set(missing_combinations['missing_start'])
    all_start_points = set(range(1, number_of_origins + 1))
    remaining_start_points = all_start_points - existing_start_points

    for start_point in remaining_start_points:
        accessibility_df = pd.concat([accessibility_df, pd.DataFrame({'start_point': [start_point], 'accessibility_score': [1]})], ignore_index=True)

    # Merge origins DataFrame with accessibility_df
    accessibility_df = pd.merge(origins, accessibility_df, left_on='name', right_on='start_point', how='left')
    accessibility_df = accessibility_df.sort_values(by = "name")

    #create 3 different dataframes for each accessibility types:
    #accessible (=1), partially accessible (0,1), not accessible (0)

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

    destinations_only_map = vrv.createLeaflet(
    mapObject=None,
    nodes = destinations_nodesdf)

    accessibility_map1 = vrv.createLeaflet(
    mapObject=destinations_only_map,
    nodes = full_accessible_nodesdf)

    accessibility_map2 = vrv.createLeaflet(
    mapObject=accessibility_map1,
    nodes = partial_accessible_nodesdf)

    accessibility_map = vrv.createLeaflet(
    mapObject=accessibility_map2,
    nodes = not_accessible_nodesdf,
    mapFilename = "accessibility_map_v2.html")
    
    return accessibility_map

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py <experiment_id>")
        sys.exit(1)
    experiment_id = sys.argv[1]

    directory = f"experiments/{experiment_id}/"
    if not os.path.exists(directory):
        print("ERROR: Experiment ID not found!")
        exit()

    origins = pd.read_csv(f"{directory}origins.csv")
    destinations = pd.read_csv(f"{directory}destinations.csv")
    results = pd.read_csv(f"{directory}results.csv")

    # Visualize the origin and destination points
    accessibility = accessibility(origins=origins, destinations=destinations, results=results)