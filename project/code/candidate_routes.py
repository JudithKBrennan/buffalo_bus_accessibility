import pandas as pd

"""
TODO: team 2 should write the documentation
The meaning of these variables is straightforward,
so I will leave it for team 2 to complete.
"""


"""
TODO: team 2 must implement this function

Purpose:
    Find 'reasonable' routes from the given origin to the given destination.
    This is NOT an optimization step. It is NOT finding the best route.
    It IS eliminating routes that would NEVER be optimal.
    For example, 
        -you would never get on a bus and then get off at the same stop.
        -you would never walk further to get to and from bus stops if you
         could simply walk to your destination with less walking.
        - ... (TODO: team 2 should add more examples)

Input:
    origin_id: an integer representing the origin id
    destination_id: an integer representing the destination id
    location_to_stops: a dictionary containing three pandas dataframes. 
                       Do Ctrl-F "Structure of location_to_stops" to
                       see the description.

Output:
    A list of CandidateRoute objects.
import pandas as pd

"""

class CandidateRoute:
    def __init__(self, pick_up_id, drop_off_id, dist_walk_pick_up, dist_walk_drop_off, time_walk_pick_up, time_walk_drop_off):
        self.pick_up_id = pick_up_id
        self.drop_off_id = drop_off_id
        self.dist_walk_pick_up = dist_walk_pick_up
        self.dist_walk_drop_off = dist_walk_drop_off
        self.time_walk_pick_up = time_walk_pick_up
        self.time_walk_drop_off = time_walk_drop_off

def candidate_bus_pairs(origin_id, destination_id, location_to_stops):
    # Extract dataframes from the dictionary
    df_origin = location_to_stops['origin']
    df_destination = location_to_stops['destination']
    df_od = location_to_stops['origin2destination']

    # Direct walking distance and time from origin to destination
    direct_dist = df_od.loc[(df_od['origin_id'] == origin_id) & (df_od['destination_id'] == destination_id), 'distance'].iloc[0]
    direct_time = df_od.loc[(df_od['origin_id'] == origin_id) & (df_od['destination_id'] == destination_id), 'time'].iloc[0]

    # Initialize list to store candidate routes
    candidate_routes = []

    # Iterate over possible pairs of bus stops
    for _, stop_origin in df_origin.iterrows():
        for _, stop_destination in df_destination.iterrows():
            total_walk_distance = stop_origin['distance'] + stop_destination['distance']
            total_walk_time = stop_origin['time'] + stop_destination['time']

            # Skip if total walking distance/time exceeds direct walking
            if total_walk_distance > direct_dist or total_walk_time > direct_time:
                continue 

            # Skip pairs where origin and destination are the same stop
            if stop_origin['stop_id'] == stop_destination['stop_id']:
                continue

            candidate_route = CandidateRoute(
                pick_up_id=stop_origin['stop_id'],
                drop_off_id=stop_destination['stop_id'],
                dist_walk_pick_up=stop_origin['distance'],
                dist_walk_drop_off=stop_destination['distance'],
                time_walk_pick_up=stop_origin['time'],
                time_walk_drop_off=stop_destination['time']
            )

            candidate_routes.append(candidate_route)
    return candidate_routes