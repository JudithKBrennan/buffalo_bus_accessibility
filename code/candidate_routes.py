"""
TODO: team 2 should write the documentation
The meaning of these variables is straightforward,
so I will leave it for team 2 to complete.
"""
class CandidateRoute:
    def __init__(self, pick_up_id, drop_off_id,
                 dist_walk_pick_up, dist_walk_drop_off,
                 time_walk_pick_up, time_walk_drop_off):
        self.pick_up_id = pick_up_id
        self.drop_off_id = drop_off_id
        self.dist_walk_pick_up = dist_walk_pick_up  # meters
        self.dist_walk_drop_off = dist_walk_drop_off  # meters
        self.time_walk_pick_up = time_walk_pick_up  # seconds
        self.time_walk_drop_off = time_walk_drop_off  # seconds


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
"""
def candidate_bus_pairs(origin_id, destination_id, location_to_stops):
    # TODO: team 2 must implement this funtions
    # Example (TODO: delete this example)
    bus_pairs = [
        CandidateRoute(pick_up_id=0, drop_off_id=1,
                       dist_walk_pick_up=100, dist_walk_drop_off=50,
                       time_walk_pick_up=80, time_walk_drop_off=40),
        CandidateRoute(pick_up_id=0, drop_off_id=2,
                       dist_walk_pick_up=100, dist_walk_drop_off=250,
                       time_walk_pick_up=80, time_walk_drop_off=200)
    ]

    return bus_pairs