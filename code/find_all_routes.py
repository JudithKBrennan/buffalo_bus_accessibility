import pandas as pd
from datetime import datetime
"""
TODO: team 3 must implement this function

Purpose:
    Find all possible routes (at all times of day) from the given origin
    to the given destination destination.
    The pairs of potential pick up and drop off locations are given by bus_pairs.

Input:
    bus_routes: this is the output from pre_compute_bus_routes().
                It is a dictionary where:
                    -keys are tuples (bus_stop_pick_up_id, bus_stop_drop_off_id)
                    -values are lists of RouteInfo class objects
    location_to_stops: Do Ctrl-F "Structure of location_to_stops" to see the description.
    bus_pairs: the output of candidate_bus_pairs. It is a list of CandidatePair objects.
    origin_id: an integer.
    destination_id: an integer.

Output:
    Pandas dataframe.
    TODO: Team 3 can determine exactly what columns they would like to include.
    It should be similar to results.csv from our previous routing algorithm.
    However, you MUST include the following new columns:
        'start_time': the latest possible time this route can begin. It is calculated
                      as the bus pick up time minus the walking time to that bus stop.
        'end_time': the earlist possible time this route could end. It is calculated
                    as the bus drop off time plus the walking time to the destination.

NOTE: 
bus_pairs contains a lot of information about times and distances. It is possible (likely?)
that we can remove location_to_stops as input because the needed info is already
contained more efficiently in bus_pairs. However, I will leave it as an argument for now,
and team 3 can remove it later if it isn't needed.
"""




'''
def filter_routes_by_current_time(all_routes):

    """
    Filter out routes where the current time is greater than the pick-up time
    """   

    # Get the current time as a datetime object
    now = datetime.now()
    # Convert 'bus_start_time' from HH:MM:SS to today's datetime for comparison
    all_routes['bus_start_time_dt'] = pd.to_datetime(now.date().isoformat() + ' ' + all_routes['bus_start_time'])
    # Filter out rows where the current time is greater than the pick-up time
    filtered_routes = all_routes[all_routes['bus_start_time_dt'] > now]
    # Drop the temporary datetime column if no longer needed
    filtered_routes.drop('bus_start_time_dt', axis=1, inplace=True)
    return filtered_routes
'''

'''
def convert_into_seconds(time):
    """convert from "0 days 08:31:26" to seconds"""
    time = str(time).split(' ')[-1]
    h, m, s = map(int, time.split(':'))
    return h*60*60 + m*60 + s



def get_bus_routes():
    routes_df = pd.read_csv('data/routes_data.csv')
    bus_routes = {}
    for index, row in routes_df.iterrows():
        pick_up_id = row['Pick_up_id']
        drop_off_id = row['drop_off_id']
        route_info = RouteInfo(convert_into_seconds(row['pick_up_time']), 
                               convert_into_seconds(row['drop_off_time']), 
                               row['trip_id'], 
                               row['walking_distance'])
        if (pick_up_id, drop_off_id) not in bus_routes:
            bus_routes[(pick_up_id, drop_off_id)] = []
        bus_routes[(pick_up_id, drop_off_id)].append(route_info)
    return bus_routes
'''

def find_routes(bus_routes, location_to_stops, bus_pairs, origin_id, destination_id):
    all_routes = []
    is_feasible = True # Assume the bus pair is feasible - will be set to False if no routes are found

    # Extract data from location_to_stops
    df_origin = location_to_stops['origin']
    df_destination = location_to_stops['destination']
    df_od = location_to_stops['origin2destination'] 

    # direct walking distance and time from origin to destination
    direct_dist = df_od.loc[(df_od['origin_id'] == origin_id) & (df_od['destination_id'] == destination_id), 'distance'].iloc[0]
    direct_time = df_od.loc[(df_od['origin_id'] == origin_id) & (df_od['destination_id'] == destination_id), 'time'].iloc[0]

    # Get the lat and lon of the origin and destination
    origin_lat = df_origin.loc[df_origin['id'] == origin_id, 'lat'].iloc[0]
    origin_lon = df_origin.loc[df_origin['id'] == origin_id, 'lon'].iloc[0]
    destination_lat = df_destination.loc[df_destination['id'] == destination_id, 'lat'].iloc[0]
    destination_lon = df_destination.loc[df_destination['id'] == destination_id, 'lon'].iloc[0]

    # Iterate through each candidate bus pair
    for bus_pair in bus_pairs:
        pick_up_id = bus_pair.pick_up_id
        drop_off_id = bus_pair.drop_off_id
        route_infos = bus_routes.get((pick_up_id, drop_off_id), [])

        if not route_infos:
            is_feasible = False

        # Process each RouteInfo object
        for route_info in route_infos:
            route_dict = {
                'trip_id': route_info.trip_id,
                'bus_start_time': (route_info.pick_up_time),
                'bus_end_time': (route_info.drop_off_time),
                'bus_riding_time': (route_info.drop_off_time - route_info.pick_up_time),
                'walk_to_start_time': (bus_pair.time_walk_pick_up),
                'walk_to_destination_time': (bus_pair.time_walk_drop_off),
                'walk_to_start': bus_pair.dist_walk_pick_up,
                'walk_to_destination': bus_pair.dist_walk_drop_off,
                'total_walk_time': (bus_pair.time_walk_pick_up + bus_pair.time_walk_drop_off),
                'destination_id': destination_id,
                'origin_id': origin_id,
                'origin_lat': origin_lat,
                'origin_lon': origin_lon,
                'destination_lat': destination_lat,
                'destination_lon': destination_lon,
                'start_stop_id': pick_up_id,
                'end_stop_id': drop_off_id,
                'total_walk': bus_pair.dist_walk_pick_up + bus_pair.dist_walk_drop_off,
                'total_time': (route_info.drop_off_time - route_info.pick_up_time + bus_pair.time_walk_pick_up + bus_pair.time_walk_drop_off),
                'start_time': (route_info.pick_up_time - bus_pair.time_walk_pick_up),
                'end_time': (route_info.drop_off_time + bus_pair.time_walk_drop_off),
                'bus_used': 1,
                'is_feasible': is_feasible
            }
            all_routes.append(route_dict)
    
    # add the direct walking route
    direct_walk_route = {
        'trip_id': None,
        'bus_start_time': None,
        'bus_end_time': None,
        'bus_riding_time': None,
        'walk_to_start_time': None,
        'walk_to_destination_time': None,
        'walk_to_start': None,
        'walk_to_destination': None,
        'total_walk_time': (direct_time),
        'destination_id': destination_id,
        'origin_id': origin_id,
        'origin_lat': origin_lat,
        'origin_lon': origin_lon,
        'destination_lat': destination_lat,
        'destination_lon': destination_lon,
        'start_stop_id': None,
        'end_stop_id': None,
        'total_walk': direct_dist,
        'total_time': (direct_time),
        'start_time': None,
        'end_time': None,
        'bus_used': 0,
        'is_feasible': is_feasible
    }
    all_routes.append(direct_walk_route)

    # filter out the routes based on the current time
    #all_routes = filter_routes_by_current_time(pd.DataFrame(all_routes))

    return pd.DataFrame(all_routes)