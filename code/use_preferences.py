import pandas as pd
import numpy as np

#* valid preference values: 'min_time' (default) or 'min_walk'
#* beta (default 140) is a tuning parameter bounded between 0 and 1. 
      #It controls the penalty term in our function.
      #if increased, the routes require more time will be punished more 
      #and the value will converge to 0 more quickly. If you want to penalize 
      #time more, decrease this term.
#* time: format for time as follows: "HH:MM:SS"
#* origin_id and destination_id: must be present in all_routes dataframe
#* all_routes: dataframe. output from find_all_routes.py

# support function

def seconds_to_hms(seconds):
    """
    to convert seconds to HH:MM:SS format
    """
    hours = int(seconds // 3600)
    minutes =int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def route_preferences(all_routes, time, origin_id, destination_id, preference = 'min_time', beta = 140): 

    # Update 'start_time' and 'end_time' columns for only walking routes for each 'time'
    all_routes.loc[all_routes[all_routes['bus_used'] == 0].index, 'start_time'] = time
    all_routes.loc[all_routes[all_routes['bus_used'] == 0].index, 'end_time'] = time + all_routes[all_routes['bus_used'] == 0]['total_time']
    #filter the routes based on the origin and destination
    filtered_routes = all_routes[(all_routes['origin_id'] == origin_id) & 
                                 (all_routes['destination_id'] == destination_id) &
                                 (all_routes['start_time'] >= float(time)) &
                                 (all_routes['end_time'] <= float((time + 3600)))] # look through a 1 hour window
        
    #time impedance function - will be used in part for accessibility measure
    #total_time_score is the value of the exponential time impedance function for total trip time (walking to/from buses + bus riding time)
    #walking_score is the value of the exponential time impedance function for total walking time only (walking to/from buses)
    #both might be used with different weights to calculate one single score for each optimal (based on preference) trip

    filtered_routes['total_time_score'] = np.exp(-((filtered_routes['total_time'] / 60) ** 2) / beta)
    filtered_routes['walking_score'] = np.exp(-((filtered_routes['total_walk_time'] / 60) ** 2) / beta)
    filtered_routes['preference'] = 0
    filtered_routes['time'] = time

    #locate the route with minimum walking distance & minimum total time 


    min_walking_distance = filtered_routes.loc[filtered_routes['total_walk_time'].idxmin()]
    min_time = filtered_routes.loc[filtered_routes['total_time'].idxmin()]

        
    #return the trip that has the minimum overall time 
    
    if preference == 'min_time':
        min_time['preference'] = 'min_time'
        return pd.DataFrame([min_time], columns=['origin_id','destination_id','bus_used', 'trip_id', 'time', 'bus_start_time', 'bus_end_time', 'bus_riding_time', 'total_walk', 
                                                 'total_walk_time', 'total_time','walking_score','total_time_score','preference'])
    
    #return the trip that has the minimum walking distance/time 
    elif preference == 'min_walk':
        min_walking_distance['preference'] = 'min_walk'
        return pd.DataFrame([min_walking_distance], columns=['origin_id','destination_id','bus_used', 'trip_id', 'time', 'bus_start_time', 'bus_end_time', 'bus_riding_time', 'total_walk', 
                                                             'total_walk_time', 'total_time', 'walking_score','total_time_score','preference'])
    
    #TODO: for now, we have two preferences... will be expanded
    else:
        return "invalid preference... please provide 'min_time' or 'min_walk'"