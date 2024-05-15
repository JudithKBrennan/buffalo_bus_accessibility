import pickle
import os
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor

"""

Purpose: 
    Find all possible bus routes at all times of day.
    Initially these will be 1-bus routes, however, it
    can be extended to 2-bus routes or other types of routes.
Input: None
Output: 
    Dictionary:
        keys are tuples (bus_stop_pick_up_id, bus_stop_drop_off_id)
        values are lists of RouteInfo class objects
"""


class RouteInfo:
    """
    This class stores information about a bus ride.
    It is used in the lists in the values of the dictionary bus_routes.
    """
    def __init__(self, pick_up_time, drop_off_time, walking_distance=0):
        self.pick_up_time = pick_up_time  # time of day (seconds) bus picks up rider at this stop (int)
        self.drop_off_time = drop_off_time  # time of day (seconds) bus drops off rider at this stop (int)
        self.walking_distance = walking_distance  # in a 2-bus route, the walking distance (meters) between intermediate stops (float)
        self.total_time = drop_off_time - pick_up_time  # number of seconds from pick up to drop off (int)

def get_walking_dist(row, walking_speed_kmph=5):
    """Calculates the walking distance based on arrival time by walking obtained from one_bus_transfer_routes.csv

    Args:
        row (object): row from the dataframe one_bus_transfer_routes.csv 
        walking_speed_kmph (int, optional): walking speed average in kmph

    Returns:
        int: walking distance in meters
    """
    intermediate_arrival_by_walking = pd.to_timedelta(row['Intermediate arrival by walking']).total_seconds()
    intermediate_dropoff_time = pd.to_timedelta(row['Intermediate Dropoff Time']).total_seconds()
    walking_time_sec = intermediate_arrival_by_walking - intermediate_dropoff_time
    
    walking_speed_mps = (walking_speed_kmph * 1000) / 3600.0
    
    walking_distance = walking_time_sec * walking_speed_mps
    return walking_distance

def calculate_walking_times(stops_df, walking_speed_kmph=5):
    """Calculates walking times between all the stops and stores them in a dataframe structure

    Args:
        stops_df (DataFrame object): Stops DataFrame object consisting of all the stops with their lat, lon values
        walking_speed_kmph (int, optional): Average walking speed in kmph. Defaults to 5.

    Returns:
        DataFrame object: A grid like dataframe object with index and columns as stop. The values in the dataframe indicate the walking time between two stops.
    """
    latitudes = stops_df['stop_lat'].values
    longitudes = stops_df['stop_lon'].values
    walking_speed_kmpm = walking_speed_kmph / 60.0

    lat1, lat2 = np.meshgrid(latitudes, latitudes)
    lon1, lon2 = np.meshgrid(longitudes, longitudes)

    # Calculate distances using the Manhattan metric
    avg_lat = (lat1 + lat2) / 2
    delta_lat_km = np.abs(lat2 - lat1) * 111
    delta_lon_km = np.abs(lon2 - lon1) * 111 * np.cos(np.radians(avg_lat))
    manhattan_distance_km = delta_lat_km + delta_lon_km

    # Calculate walking times in minutes
    walking_times = manhattan_distance_km / walking_speed_kmpm
    return pd.DataFrame(walking_times, index=stops_df['stop_id'], columns=stops_df['stop_id'])

def process_routes_for_origin(origin, stops_df, times_df, walking_times_matrix, MAX_WALKING_TIME):
    """Generates all the bus routes for a given origin stop. Necessary for parallel processing of all routes.

    Args:
        origin (DataFrame row object): Row from updated_stops containing unique stops
        stops_df (DataFrame object): updated_stops.csv as pandas DataFrame 
        times_df (DataFrame object): Truncated stop_times.csv to only contain stops within area of interest
        walking_times_matrix (DataFrame object): contains walking time between any two stops
        MAX_WALKING_TIME (int): Maximum walking time allowed between two stops in minutes

    Returns:
        list: list of dicts containing all information for one bus route between origin and any destination stop
    """
    routes_data = []
    origin_trips = times_df[times_df['stop_id'] == origin['stop_id']]
    for _, origin_trip in origin_trips.iterrows():
        intermediate_stops_1 = times_df[(times_df['trip_id'] == origin_trip['trip_id']) & (times_df['arrival_time'] > origin_trip['departure_time'])]
        for _, intermediate_1 in intermediate_stops_1.iterrows():
            
            # Direct route addition
            routes_data.append({
                'Origin Trip ID': origin_trip['trip_id'],
                'Origin Stop ID': origin['stop_id'],
                'Origin Pickup Time': origin_trip['departure_time'],
                'Intermediate Stop 1 ID': intermediate_1['stop_id'],
                'Intermediate Dropoff Time': intermediate_1['arrival_time'],
                'Intermediate Stop 2 ID': None,
                'Intermediate arrival by walking': intermediate_1['arrival_time'],
                'Destination Trip ID': None,
                'Intermediate Pickup Time': None,
                'Destination Stop ID': intermediate_1['stop_id'],
                'Destination Dropoff Time': intermediate_1['arrival_time'],
                'Num of Buses': 1
            })
            
            for _, intermediate_2 in stops_df.iterrows():
                
                if intermediate_2['stop_id'] == origin['stop_id']:
                    continue

                walking_time = walking_times_matrix.at[intermediate_1['stop_id'], intermediate_2['stop_id']]
                
                if walking_time > MAX_WALKING_TIME:
                    continue
                
                walking_arrival_time = intermediate_1['arrival_time'] + pd.to_timedelta(walking_time, unit='m')

                intermediate_trips_2 = times_df[(times_df['stop_id'] == intermediate_2['stop_id']) & (times_df['arrival_time'] > walking_arrival_time)]
                for _, final_trip in intermediate_trips_2.iterrows():
                    final_stops = times_df[(times_df['trip_id'] == final_trip['trip_id']) & (times_df['arrival_time'] > final_trip['departure_time'])]
                    
                    if final_trip['departure_time'] > walking_arrival_time + pd.to_timedelta('1 hour'):
                        continue
                    
                    for _, destination in final_stops.iterrows():
                        routes_data.append({
                            'Origin Trip ID': origin_trip['trip_id'],
                            'Origin Stop ID': origin['stop_id'],
                            'Origin Pickup Time': origin_trip['departure_time'],
                            'Intermediate Stop 1 ID': intermediate_1['stop_id'],
                            'Intermediate Dropoff Time': intermediate_1['arrival_time'],
                            'Intermediate Stop 2 ID': intermediate_2['stop_id'],
                            'Intermediate arrival by walking': walking_arrival_time,
                            'Destination Trip ID': final_trip['trip_id'],
                            'Intermediate Pickup Time': final_trip['departure_time'],
                            'Destination Stop ID': destination['stop_id'],
                            'Destination Dropoff Time': destination['arrival_time'],
                            'Num of Buses': 2
                        })
                        
    return routes_data

def generate_valid_stops_df():
    """Generates and saves the valid_stops.csv which is a truncated version of the 'stop_times.csv' containing only the valid stops within our area of interest

    Raises:
        FileNotFoundError: if updated_stops.csv is not found
        FileNotFoundError: if stop_times.csv is not found

    Returns:
        DataFrame object: valid_stops dataframe containing all stop_times of stops withing area of interest
    """
    if os.path.exists('data/updated_stops.csv'):
        stops_df = pd.read_csv('data/updated_stops.csv')
    else:
        raise FileNotFoundError
    
    if os.path.exists('data/google_transit/stop_times.csv'):
        times_df = pd.read_csv('data/google_transit/stop_times.csv')
    else:
        raise FileNotFoundError
    
    valid_stops_df = pd.merge(times_df, stops_df, on='stop_id')
    
    valid_stops_df.to_csv('data/valid_stops.csv')
    return valid_stops_df
    
def generate_one_transfer_bus_csv(MAX_WALKING_TIME=20):
    """Generates the one_transfer_bus_routes.csv file enumerating all possible bus routes within our area of interest

    Args:
        MAX_WALKING_TIME (int, optional): Maximum walking time between stops. Defaults to 20.

    Raises:
        FileNotFoundError: if updated_stops.csv is not found
    """
    
    if os.path.exists('data/updated_stops.csv'):
        stops_df = pd.read_csv('data/updated_stops.csv')
    else:
        raise FileNotFoundError
    
    if os.path.exists('data/valid_stops.csv'):
        times_df = pd.read_csv('valid_stops.csv')
    else:
        times_df = generate_valid_stops_df()
        
    times_df['arrival_time'] = pd.to_timedelta(times_df['arrival_time'])
    times_df['departure_time'] = pd.to_timedelta(times_df['departure_time'])
    walking_times_matrix = calculate_walking_times(stops_df)
    
    executor = ProcessPoolExecutor(max_workers=6)
    futures = []
    for idx, origin in stops_df.iterrows():
        print(f"Origin: {origin['stop_id']}")
        futures.append(executor.submit(process_routes_for_origin, origin, stops_df, times_df, walking_times_matrix, MAX_WALKING_TIME))
    all_routes_data = []
    for future in futures:
        all_routes_data.extend(future.result())
    routes_df = pd.DataFrame(all_routes_data)
    routes_df.to_csv('data/one_transfer_bus_routes.csv')

def pre_compute_bus_routes():
    """Precomputes all the bus routes from the bus routes csv files and stores it in a pickle file

    Returns:
        dict: routes dictionary with keys (pick_up_id, drop_off_id) and values RouteInfo objects of all feasible bus routes between the two ids
    """
    # Team 0: DO NOT DELETE THIS
    # Check if we have already precomputed the bus routes
    bus_route_filename = 'bus_routes.pkl'  # this can be modified if desired
    if not os.path.exists('data/'):
        os.makedirs('data/')  # Create the directory
    if os.path.exists(f'data/{bus_route_filename}'):
        with open(f'data/{bus_route_filename}', 'rb') as f:
            routes = pickle.load(f)
            return routes
    
    if os.path.exists('data/one_transfer_bus_routes.csv'):
        routes_df = pd.read_csv('data/one_transfer_bus_routes.csv')
    else:
        generate_one_transfer_bus_csv()
        routes_df = pd.read_csv('data/one_transfer_bus_routes.csv')
    
    routes = {}
    
    for _, row in routes_df.iterrows():
        
        pick_up_id = row['Origin Stop ID']
        drop_off_id = row['Destination Stop ID']
        
        pick_up_time = pd.to_timedelta(row['Origin Pickup Time']).total_seconds()
        drop_off_time = pd.to_timedelta(row['Destination Dropoff Time']).total_seconds()
        walking_distance = 0 if pd.isna(row['Intermediate Stop 2 ID']) else get_walking_dist(row)
        
        route_info = RouteInfo(pick_up_time, drop_off_time, walking_distance)
        
        if (pick_up_id, drop_off_id) not in routes:
            routes[(pick_up_id, drop_off_id)] = []
        routes[(pick_up_id, drop_off_id)].append(route_info)
        
    # Team 0: DO NOT DELETE THIS
    # Save the routes to a pickle file (pickle is likely the most efficient storage format)
    with open(bus_route_filename, 'wb') as f:
        pickle.dump(routes, f)
    return routes


