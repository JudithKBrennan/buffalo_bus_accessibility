import pickle
import json
import argparse
import os
import pandas as pd
import numpy as np
import veroviz as vrv

"""
TODO: team 0 must complete this function

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


def pre_compute_bus_routes():
    # Team 0: DO NOT DELETE THIS
    # Check if we have already precomputed the bus routes
    bus_route_filename = 'bus_routes.pkl'  # this can be modified if desired
    if not os.path.exists('data/'):
        os.makedirs('data/')  # Create the directory
    if os.path.exists(f'data/{bus_route_filename}'):
        with open(f'data/{bus_route_filename}', 'rb') as f:
            routes = pickle.load(f)
            return routes

    # TODO: team 0 must implement this function
    # Example (DELETE THIS)
    routes = {
        #  Structure: (pick_up_id, drop_off_id) : [RouteInfo(), RouteInfo, ...]
        (0, 0): [],  # empty because getting picked up and dropped off at the same stop does not make sense
        (0, 1): [RouteInfo(7 * 60 * 60, 7 * 60 * 60 + 10 * 60),  # pick_up_time = 7am, drop_off_time = 7:10am
                 RouteInfo(8 * 60 * 60 + 30 * 60, 9 * 60 * 60)]  # pick_up_time = 8:30am, drop_off_time = 9am
    }

    # Team 0: DO NOT DELETE THIS
    # Save the routes to a pickle file (pickle is likely the most efficient storage format)
    with open(bus_route_filename, 'wb') as f:
        pickle.dump(routes, f)
    return routes


"""
This class stores information about a bus ride.
It is used in the lists in the values of the dictionary bus_routes.
"""
class RouteInfo:
    def __init__(self, pick_up_time, drop_off_time, walking_distance=0):
        self.pick_up_time = pick_up_time  # time of day (seconds) bus picks up rider at this stop (int)
        self.drop_off_time = drop_off_time  # time of day (seconds) bus drops off rider at this stop (int)
        self.walking_distance = walking_distance  # in a 2-bus route, the walking distance (meters) between intermediate stops (float)
        self.total_time = drop_off_time - pick_up_time  # number of seconds from pick up to drop off (int)