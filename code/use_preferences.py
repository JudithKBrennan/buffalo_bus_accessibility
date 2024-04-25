import pandas as pd

"""
TODO: team 5 must implement this function

Purpose:
    This is the optimization step. For given preferences, find the best route(s).
    This will likely be one route. It is theoretically (but not practically?) possible
    there could be a tie between best routes. For that reason, we return a dataframe
    instead of a single row.

Input:
# TODO: team 5 can decide what they would like as input.
        However, the following options for preferences would be useful:
            -Decide whether minimum walking or minimum time is preferred.
            -If minimum walking, include a time threshold (select the min
             walking option among all the routes that take less than this 
             time threshold.
            - ... (TODO: team 5 can think of other preferences)

Output:
# TODO: team 5 can decide what columns should be included in
        the pandas dataframe. The output needs to include
        the origin and destination ids, the time, the preferences used,
        and information about the distance and time of that route.
        More information may be needed as well.
        This output will be used for computing the accessibility metric
        for each location as a function of time.
"""
def route_preferences(time, origin_id, destination_id):
    return pd.DataFrame()  # TODO: remove this line. return the routes this function creates.
