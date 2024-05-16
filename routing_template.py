"""
Template for our new routing function.

Author: Adam DeHollander
Date: April 16, 2024

How to run the code:
python3 routing_template.py --experiment_id BNMC
You can change the experiment id from 'BNMC' to other ids as desired.
There are other arguments you can specify as well, which can be
found in the first few lines of the intialize() funciton.
"""
import pickle
import json
import argparse
import os
import pandas as pd
import numpy as np
import veroviz as vrv
from datetime import datetime
from datetime import timedelta
from code.candidate_routes import candidate_bus_pairs
from code.find_all_routes import find_routes
from code.use_preferences import route_preferences


# Finds how long it takes to walk to/from every bus stop (uses VeroViz).
# this is a modification of 'stops_df' in the previous code
"""
Purpose:
    Compute the walking times and distances from:
        -origins to bus stops
        -bus stops to destinations
        -origins to destinations

This function has already been implemented.
Do not worry about the details of this function.
Focus on understanding the output. The output is described
later in this code. Do Ctrl-F "Structure of location_to_stops" to
see the description.
"""
def get_walking_df(df, origins, destinations, filepath, overwrite=False):
    location_to_stops = {
        'origin': None,
        'destination': None,
        'origin2destination': None
    }

    origin_file_path = filepath + 'walking_origins_to_stops.csv'
    destination_file_path = filepath + 'walking_destinations_to_stops.csv'
    walking_file_path = filepath + 'walking_origins_to_destinations.csv'

    # Do not recompute if the files already exist
    if os.path.exists(origin_file_path) and not overwrite:
        location_to_stops['origin'] = pd.read_csv(origin_file_path)
    if os.path.exists(destination_file_path) and not overwrite:
        location_to_stops['destination'] = pd.read_csv(destination_file_path)
    if os.path.exists(walking_file_path) and not overwrite:
        location_to_stops['origin2destination'] = pd.read_csv(walking_file_path)
    if ((location_to_stops['origin'] is not None)
            and (location_to_stops['destination'] is not None)
            and (location_to_stops['origin2destination'] is not None)):
        return location_to_stops

    # Filter based on weekday or weekend
    df = df[df["service_description"] == input['day_of_week']]

    # Only look at the bus stops.
    # In this dataframe, we only care about the bus stop location and ID.
    # We will remove the extra columns we don't care about after calling
    # the VeroViz function.
    stops_full = df.drop_duplicates(subset='id', keep='first')

    def walking_iterate_helper(stops_full, pois, file_path, rename_cols=False):
        full_df = pd.DataFrame()

        for index, row in pois.iterrows():
            poi = {
                'lat': row['lat'],
                'lon': row['lon'],
                'name': row['name'],
                'id': 'point_of_interest'
            }

            def get_walking_helper(stops_full, point_of_interest, computing_origin=True):
                def add_row(data, new_row):
                    # Convert new_row to a DataFrame with a single row
                    new_row_df = pd.DataFrame([new_row])

                    # Ensure new_row_df columns match the data DataFrame, filling missing with np.nan
                    new_row_df = new_row_df.reindex(columns=data.columns, fill_value=np.nan)

                    # Use .dropna to avoid a pandas warning while using .concat
                    data_filtered = data.dropna(axis=1, how='all')
                    new_row_df_filtered = new_row_df.dropna(axis=1, how='all')
                    return pd.concat([data_filtered, new_row_df_filtered], ignore_index=True)

                stops = add_row(stops_full.copy(), point_of_interest)

                # Documentation: https://veroviz.org/docs/veroviz.getTimeDist2D.html
                if computing_origin:
                    matrixType = 'one2many'
                    fromNodeID = point_of_interest['id']
                    toNodeID = None
                else:
                    matrixType = 'many2one'
                    fromNodeID = None
                    toNodeID = point_of_interest['id']

                [origin_time, origin_distance] = vrv.getTimeDist2D(
                    nodes=stops,
                    matrixType=matrixType,
                    fromNodeID=fromNodeID,
                    toNodeID=toNodeID,
                    routeType='manhattan',
                    speedMPS=input['walk_speed'],
                    outputTimeUnits='seconds',
                    outputDistUnits='meters')

                stops = stops[['stop_id', 'id', 'lat', 'lon']]  # Can't do this earlier because of vrv calls

                stops['time'] = -1.0
                stops['distance'] = -1.0

                # Add the results to the dataframe containing the information about each stop
                for index in stops.index:
                    origin_key = (point_of_interest['id'], stops.loc[index, 'id'])
                    stops.loc[index, 'time'] = float(origin_time[origin_key])
                    stops.loc[index, 'distance'] = float(origin_distance[origin_key])

                stops = stops[stops['id'] != 'point_of_interest']
                stops['id'] = point_of_interest['name']
                # stops['stop_id'] = stops['stop_id'].astype(int)

                return stops

            stops = get_walking_helper(stops_full, poi, computing_origin=True)
            full_df = pd.concat([full_df, stops])

        full_df.reset_index(drop=True, inplace=True)

        if rename_cols:
            full_df = full_df.rename(columns={
                'stop_id': 'destination_id', 'id': 'origin_id'})
            full_df = full_df.drop(columns=['lat', 'lon'])

        # Save the data to avoid extra API calls in future runs of the code.
        full_df.to_csv(file_path, index=False)
        return full_df

    if location_to_stops['origin'] is None:
        print("Computing walking distances from origins to bus stops...")
        location_to_stops['origin'] = walking_iterate_helper(stops_full=stops_full,
                                                             pois=origins,
                                                             file_path=origin_file_path)
    if location_to_stops['destination'] is None:
        print("Computing walking distances from bus stops to destination...")
        location_to_stops['destination'] = walking_iterate_helper(stops_full=stops_full,
                                                                  pois=destinations,
                                                                  file_path=destination_file_path)

    if location_to_stops['origin2destination'] is None:
        print("Computing pairwise walking distances between origins and destinations..")
        destinations_copy = destinations.copy()
        destinations_copy['stop_id'] = destinations_copy['name']  # temporary name
        destinations_copy['id'] = destinations_copy['name']
        destinations_copy = vero_viz_node_dataframe(destinations_copy)
        location_to_stops['origin2destination'] = walking_iterate_helper(
            stops_full=destinations_copy, pois=origins,
            file_path=walking_file_path, rename_cols=True)

    return location_to_stops


"""
This function has already been implemented.
You could look at the first few lines to see what arguments you can pass to this code.
Specifically you will want to use --experiment_id to set the experiment.

Purpose:
    Parse the arguments.
    Read in the data files.
Output:
"""
def initialize():
    # Set up the argument parser
    parser = argparse.ArgumentParser(description='Process input parameters for the experiment.')
    parser.add_argument('--experiment_id', default="test", help='Unique identifier for the experiment.')
    parser.add_argument('--day_of_week', default='Weekday', choices=['Weekday', 'Weekend'],
                        help='Day type: "Weekday" or "Weekend". Default is "Weekday".')
    parser.add_argument('--walk_speed', type=float, default=1.4,
                        help='Walking speed in meters per second (m/s). Default is 1.4.')
    parser.add_argument('--overwrite_routes', type=bool, default=True,
                        help='If false, the routes will not be calculated again if they already exist. Default is True.')
    parser.add_argument('--time_inc', type=float, default=15 * 60,  # default = 15 min
                        help='The time increment when using route_preferences(). Default is 900s (15 min).')

    # Parse the arguments
    args = parser.parse_args()

    # Construct the input dictionary with command line arguments or defaults
    input = {
        'experiment_id': args.experiment_id,
        'day_of_week': args.day_of_week,
        'walk_speed': args.walk_speed,
        'overwrite_routes': args.overwrite_routes,
        'time_inc': args.time_inc
    }

    experiment_id = input['experiment_id']
    directory = f"experiments/{experiment_id}/"
    if not os.path.exists(directory):
        print("ERROR: Experiment ID not found!")
        exit()

    file_path = f"{directory}/params.json"
    with open(file_path, 'w') as json_file:
        json.dump(input, json_file, indent=4)

    # Load the origins and destinations
    origins = pd.read_csv(f"{directory}origins.csv")
    destinations = pd.read_csv(f"{directory}destinations.csv")

    # This merges the NFTA files into a combined dataframe.
    def perform_merge(target_file='all'):
        """
        Finds all entries in the target_file file that are connected to the elements in 'stops'.

        Parameters:
        - target_file: The name of the target_file file (e.g., 'trips', 'all')

        Returns:
        - A DataFrame containing all connected entries from the target_file file.
        """

        # Read the updated stops data from the CSV file
        # This is my cleaned, filtered dataframe of only the stops we care about.
        # TODO: if we want to include stops outside of our neighborhoods, this will need to be extended
        updated_stops_df = pd.read_csv('data/updated_stops.csv')

        # Initialize an empty dictionary to store your dataframes
        df = {'stops': updated_stops_df}  # Add the updated stops dataframe with the key 'stops'

        # Loop through each file in the directory
        directory = 'data/google_transit'
        for filename in os.listdir(directory):
            if filename.endswith('.txt') and filename != 'stops.txt':  # Skip the stops.txt file
                file_path = os.path.join(directory, filename)  # get the full path of the file
                key = filename[:-4]  # remove the '.txt' extension from the filename
                df[key] = pd.read_csv(file_path,
                                      sep=',')  # read the file into a dataframe and store it in the dictionary

        # Merge 'stops' with 'stop_times' using 'stop_id'
        stop_times_merged = pd.merge(df['stops'], df['stop_times'], on='stop_id', how='inner')

        # Merge the result with 'trips' using 'trip_id'
        trips_merged = pd.merge(stop_times_merged, df['trips'], on='trip_id', how='inner')

        # Further merge with 'calendar_attributes' using 'service_id'
        calendar_merged = pd.merge(trips_merged, df['calendar_attributes'], on='service_id', how='inner')

        # If 'all' is specified, proceed to merge with both 'routes' and 'shapes' sequentially
        if target_file == 'all':
            routes_merged = pd.merge(calendar_merged, df['routes'], on='route_id', how='inner')
            all_merged = pd.merge(routes_merged, df['shapes'], on='shape_id', how='inner')
            return all_merged

        # For specific target files, return the respective merged DataFrame
        if target_file == 'stops':
            return df['stops']
        elif target_file == 'stop_times':
            return stop_times_merged
        elif target_file == 'trips':
            return calendar_merged
        elif target_file == 'calendar':
            return calendar_merged
        elif target_file == 'routes':
            return pd.merge(calendar_merged, df['routes'], on='route_id', how='inner')
        elif target_file == 'shapes':
            return pd.merge(calendar_merged, df['shapes'], on='shape_id', how='inner')
        else:
            print(f"Error in perform_merge()! 'target_file'={target_file} is not a recognized option.")
            return None

    # NOTE: If using target_file='all', it is ***significantly*** faster
    #       to perform the merge instead of loading the large csv file.
    #       Otherwise, you could precompute the file instead of merging
    #       each time you run the code. However, the merge happens almost
    #       instantaneously, even when using when using target_file='all',
    #       so there is no major reason to avoid calling this function.
    df = perform_merge(target_file='calendar')

    # Add the columns needed to be considered a veroviz nodes dataframe
    df = vero_viz_node_dataframe(df=df)

    return df, origins, destinations, input


"""
This is a (unneccessary/unsafe/bad) method of hand-creating a VeroViz
dataframe in order to keep all the other columns that we want to use.
But in lieu of knowing a better way, I came up with this approach.
"""
def vero_viz_node_dataframe(df):
    # Factorize the 'stop_id' column to get a unique index starting from 0
    labels, unique = pd.factorize(df['stop_id'])

    # Add 1 to make the index 1-based and assign it to a new column 'id'
    df['id'] = labels + 1

    if 'stop_lat' in df.columns and 'stop_lon' in df.columns:
        df = df.rename(columns={'stop_lat': 'lat', 'stop_lon': 'lon'})

    df['altMeters'] = 0
    id_col = 'stop_id' if 'stop_id' in df.columns else 'id'
    df['nodeName'] = df[id_col]
    df['nodeType'] = "bus stop"
    name = 'stop_name' if 'stop_name' in df.columns else 'name'
    df['popupText'] = df[name]
    df['leafletIconPrefix'] = "glyphicon"
    df['leafletIconType'] = "info-sign"

    if 'in_multiple_neighborhoods' in df.columns:
        # Define conditions
        conditions = [
            df['in_multiple_neighborhoods'],
            df['is_in_AT'],
            df['is_in_FB'],
            df['is_in_MP']
        ]
        # Define corresponding choices
        choices = ['red', 'green', 'orange', 'blue']
        df['leafletColor'] = np.select(conditions, choices, default='blue')
        df['cesiumColor'] = df['leafletColor']
    else:
        df['leafletColor'] = 'blue'
        df['cesiumColor'] = df['leafletColor']

    df['leafletIconText'] = 1
    df['cesiumIconType'] = "pin"

    df['cesiumIconText'] = 1
    df['elevMeters'] = 0  # TODO: get data for elevation

    return df


if __name__ == '__main__':
    df, origins, destinations, input = initialize()  # This has already been implemented

    # support function
    def seconds_to_hms(seconds):
        """
        to convert seconds to HH:MM:SS format
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}" 

    def convert_into_seconds(time):
        total_seconds = 0
        parts = time.split()
        if len(parts) == 1:
            time_parts = parts[0].split(":")
            total_seconds += int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
        else:
            if parts[0] != "0":
                total_seconds += int(parts[0]) * 86400
            time_parts = parts[-1].split(":")
            total_seconds += int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
        return total_seconds

    # Obtain the bus route dictionary (does NOT consider walking, origins, or destinations)
    print("Getting bus route info...")

    # Define the RouteInfo class
    class RouteInfo:
        def __init__(self, trip_id, pick_up_time, drop_off_time, walking_distance=0):
            self.trip_id = trip_id
            self.pick_up_time = pick_up_time
            self.drop_off_time = drop_off_time
            self.walking_distance = walking_distance
            #self.total_time = (drop_off_time - pick_up_time).total_seconds()

    # Read the CSV file into a DataFrame
    routes_df = pd.read_csv('data/routes_data.csv')

    # Initialize an empty dictionary to store the data
    bus_routes = {}

    for index, row in routes_df.iterrows():
        pick_up_id = row['pick_up_id']
        drop_off_id = row['drop_off_id']
        route_info = RouteInfo(row['trip_id'],
                            convert_into_seconds(row['pick_up_time']), 
                            convert_into_seconds(row['drop_off_time']), 
                            row['walking_distance'])
        if (pick_up_id, drop_off_id) not in bus_routes:
            bus_routes[(pick_up_id, drop_off_id)] = []
        bus_routes[(pick_up_id, drop_off_id)].append(route_info)
    print("Beginning Algorithm...")

    """
    This function computes walking times and distances (this is where we use/used VeroViz).
    I completed the implementation of this function. Do not bother with looking at this function,
    only understand the output, which is described below.

    Structure of location_to_stops (a dictionary with three keys):

    location_to_stops = {
        'origin': pandas dataframe with the following columns:
                    'stop_id' (the bus stop id),
                    'id' (the origin id),
                    'lat', 'lon' (the lat and lon of the bus stop, can probably ignore this!),
                    'time', 'distance' (the walking time (seconds) and distance (meters) between the origin and the bus stop)

        'destination': pandas dataframe with the same columns as above except this dataframe
                        is computing the walking distance from the stops to the destinations

        'origin2destination': pandas dataframe with the following columns:
                    'origin_id', 'destination_id',
                    'time', 'distance' (the walking time and distance between origin and destination)
    }

    Moreover, after running the code, you can see these three pandas dataframes. They are
    saved as csv files in the experiment folder.
    """
    location_to_stops = get_walking_df(df=df,
                                       origins=origins, destinations=destinations,
                                       filepath=f"experiments/{input['experiment_id']}/",
                                       overwrite=False)  # This has already been implemented

    # Do not recalculate the routes if they already exist
    routes_file_path = f"experiments/{input['experiment_id']}/routes.csv"
    if not os.path.exists(routes_file_path):
        # Loop through the origins and destinations to find all routes
        routes = pd.DataFrame()
        for _, origin_row in origins.iterrows():
            for _, destination_row in destinations.iterrows():
                bus_pairs = candidate_bus_pairs(origin_id=origin_row['name'],
                                                destination_id=destination_row['name'],
                                                location_to_stops=location_to_stops)

                these_routes = find_routes(bus_routes=bus_routes,
                                            location_to_stops=location_to_stops,
                                            bus_pairs=bus_pairs,
                                            origin_id=origin_row['name'],
                                            destination_id=destination_row['name'])
                routes = pd.concat([routes, these_routes])
        routes.reset_index(drop=True, inplace=True)
        routes.to_csv(routes_file_path, index=False)
        
    else:
        routes = pd.read_csv(routes_file_path)
    print("All routes dataframe created...")  
      
    # Analyze the routes
    best_routes = pd.DataFrame()
    print("Calculating best routes...")
    for time in range(60 * 60 * 5, 60 * 60 * 22, input['time_inc']):  # 5am to 10pm
        for _, origin_row in origins.iterrows():
            for _, destination_row in destinations.iterrows():
                these_best_routes = route_preferences(time=time,
                                                      origin_id=origin_row['name'],
                                                      destination_id=destination_row['name'],
                                                      all_routes=routes,
                                                      preference='min_time',
                                                      beta=140
                                                      )
                best_routes = pd.concat([best_routes, these_best_routes])
                
    best_routes.reset_index(drop=True, inplace=True)
    best_routes.to_csv(f"experiments/{input['experiment_id']}/best_routes.csv",
                       index=False)

    # TODO: use best_routes to create accessibility metrics
    # TODO: plot the accessibility metrics