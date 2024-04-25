import pandas as pd
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
def find_routes(bus_routes, location_to_stops,
                bus_pairs, origin_id, destination_id):
    return pd.DataFrame()  # TODO: remove this line. return the routes this function creates.
