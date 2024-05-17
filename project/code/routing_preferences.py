import pandas as pd
import veroviz as vrv
import numpy as np
import datetime

#* valid preference values: 'min_time' (default) or 'min_walk'
#* beta (default 140) is a tuning parameter bounded between 0 and 1. 
      #It controls the penalty term in our function.
      #if increased, the routes require more time will be punished more 
      #and the value will converge to 0 more quickly. If you want to penalize 
      #time more, decrease this term.
#* time: format for time as follows: "HH:MM:SS"
#* origin_id and destination_id: must be present in all_routes dataframe
#* all_routes: dataframe. output from find_all_routes.py


def route_preferences(all_routes, time, origin_id, destination_id, preference = 'min_time', beta = 140): 
    # Convert time string to datetime object
    time = datetime.datetime.strptime(time, "%H:%M:%S")
    #filter the routes based on the origin and destionation
    filtered_routes = all_routes[(all_routes['origin_id'] == origin_id) & 
                                 (all_routes['destination_id'] == destination_id) & 
                                 (all_routes['start_time'] >= time.strftime("%H:%M:%S")) & 
                                 (all_routes['end_time'] <= (time + datetime.timedelta(hours=1)).strftime("%H:%M:%S"))]
    
    # Create identical time columns to process later
    filtered_routes['bus_riding_time_mins'] = filtered_routes['bus_riding_time']
    filtered_routes['waiting_time_mins'] = filtered_routes['waiting_time'] #waiting from start time to first bus time, can be removed
    filtered_routes['total_walking_time_mins'] = filtered_routes['total_walking_time']
    filtered_routes['adjusted_total_time_mins'] = filtered_routes['adjusted_total_time']

    time_cols = ['bus_riding_time_mins', 'waiting_time_mins', 'total_walking_time_mins', 'adjusted_total_time_mins']

    #convert identical time columns to minutes for exponential calculations
    for col in time_cols:
        filtered_routes[col] = pd.to_datetime(filtered_routes[col], format='%H:%M:%S')
        filtered_routes[col] = filtered_routes[col].dt.hour * 60 + filtered_routes[col].dt.minute + filtered_routes[col].dt.second / 60
        
    
    #time impedance function - will be used in part for accessibility measure
    #total_time_score is the value of the exponential time impedance function for total trip time (walking to/from buses + bus riding time)
    #walking_score is the value of the exponential time impedance function for total walking time only (walking to/from buses)
    #both might be used with different weights to calculate one single score for each optimal (based on preference) trip

    filtered_routes['total_time_score'] = np.exp(-filtered_routes['adjusted_total_time_mins']**2 / beta)
    #filtered_routes['waiting_score'] = np.exp(-filtered_routes['waiting_time_mins']**2 / beta) #will be used when 2-bus routes are used 
    filtered_routes['walking_score'] = np.exp(-filtered_routes['total_walking_time_mins']**2 / beta)

    #locate the route with minimum walking distance
    min_walking_distance = filtered_routes.loc[filtered_routes['total_walk'].idxmin()]

    #locate the route with minimum total time
    min_time = filtered_routes.loc[filtered_routes['adjusted_total_time'].idxmin()]
    
    #return the trip that has the minimum overall time 
    if preference == 'min_time':
        return pd.DataFrame([min_time], columns=['bus_used', 'trip_id', 'bus_start_time', 'bus_end_time', 'bus_riding_time', 'total_walk', 'total_walking_time',
                                                              'adjusted_total_time','waiting_score','walking_score','total_time_score'])
    
    #return the trip that has the minimum walking distance/time 
    elif preference == 'min_walk':
        return pd.DataFrame([min_walking_distance], columns=['bus_used', 'trip_id', 'bus_start_time', 'bus_end_time', 'bus_riding_time', 'total_walk', 'total_walking_time',
                                                              'adjusted_total_time','waiting_score','walking_score','total_time_score'])
    
    #TODO: for now, we have two preferences... will be expanded
    else:
        return "invalid preference... please provide 'min_time' or 'min_walk'"