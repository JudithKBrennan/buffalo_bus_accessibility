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
    all_routes = []

    # Iterate through each candidate bus pair
    for bus_pair in bus_pairs:
        pick_up_id = bus_pair.pick_up_id
        drop_off_id = bus_pair.drop_off_id

        # Retrieve the list of RouteInfo objects for the given bus stop pair
        route_infos = bus_routes.get((pick_up_id, drop_off_id), [])

        # Iterate through each RouteInfo object
        for route_info in route_infos:
            pick_up_time = seconds_to_hms(route_info.pick_up_time)
            drop_off_time = seconds_to_hms(route_info.drop_off_time)
            bus_riding_time = seconds_to_hms(route_info.drop_off_time - route_info.pick_up_time)

            # Calculate walking times and distances
            walk_to_start_time = seconds_to_hms(bus_pair.time_walk_pick_up)
            walk_to_destination_time = seconds_to_hms(bus_pair.time_walk_drop_off)

            total_time = seconds_to_hms(route_info.total_time + bus_pair.time_walk_pick_up + bus_pair.time_walk_drop_off)

            start_time = seconds_to_hms(route_info.pick_up_time - bus_pair.time_walk_pick_up)
            end_time = seconds_to_hms(route_info.drop_off_time + bus_pair.time_walk_drop_off)

            route_dict = {
                'trip_id': None,
                'bus_start_time': pick_up_time,
                'bus_end_time': drop_off_time,
                'bus_riding_time': bus_riding_time,
                'waiting_time': '00:00:00',
                'walk_to_start_time': walk_to_start_time,
                'walk_to_destination_time': walk_to_destination_time,
                'walk_to_start': bus_pair.dist_walk_pick_up,
                'walk_to_destination': bus_pair.dist_walk_drop_off,
                'poi_name': destination_id,
                'start_name': origin_id,
                'origin_lat': None,
                'origin_lon': None,
                'destination_lat': None,
                'destination_lon': None,
                'total_walk': bus_pair.dist_walk_pick_up + bus_pair.dist_walk_drop_off,
                'total_time': total_time,
                'best_walk': False,
                'best_time': False,
                'start_time': start_time,
                'end_time': end_time
            }

            all_routes.append(route_dict)

    return pd.DataFrame(all_routes)

def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"
