'''
Usage:
cd project/
python code/vizRoute.py --origin_id=1 --destination_id=1 --experiment_id=BNMC --preference=min_time --time_of_day=28800
'''
#Modules
import os
import argparse
import pandas as pd
import time
import sys
import numpy as np
import veroviz as vrv
import matplotlib.pyplot as plt
#Functions
from use_preferences import route_preferences
from accessibility.utils import getDirectory, getResults, checkPreference, getExperimentOD, \
    getAPIKey
from accessibility.neighborhoods import getNeighborhoods, createMapNeighborhoods
#GET API Key
ORS_API_KEY = getAPIKey()

def getData():
    '''
    Return pd dataframes retrieved from files
    Assume current directory has subdirectories code, dta and experiments
    '''
    stops_df = pd.read_csv(f"data/google_transit/stops.txt")
    shapes_df = pd.read_csv(f"data/google_transit/shapes.txt")
    trips_df = pd.read_csv(f"data/google_transit/trips.txt")
    return stops_df, shapes_df, trips_df

def creatMapObj(origin_id: int, destination_id: int, mode: str, time: int):
    '''
    Use existing code to create a map oject
    '''
    neighborhoods = getNeighborhoods(url  = "https://raw.githubusercontent.com/IE-670/bnmc/data/neighborhoods.json", 
                                    file = f"data/neighborhoods.json")
    nbhdMapObject = createMapNeighborhoods(neighborhoods, mapObject=None, addLabel=False)

    map_name = "route-"+ str(origin_id) + "-" + str(destination_id) + "-" + mode + str(time) + ".html"
    return nbhdMapObject, map_name

def showWalking(routeMap, start: list, start_name: str, start_icon: str, end: list, end_name : str, end_icon: str):
    '''
    Add arcs walking from an origin to a destination to the map object
    e.g. start=[origin_lat, origin_lon] start_icon="home" start_name="Origin 24"
    end = [bus_start_lat,bus_start_lon] end_icon="star" end_name="Bus Stop 1234"
    '''

    mapObj, mapFile = routeMap

    nodesDF = vrv.initDataframe('nodes')
    #origin
    nodesDF = vrv.createNodesFromLocs(locs=[start],
                                      leafletIconPrefix="glyphicon",
                                      leafletIconType=start_icon,
                                      leafletColor="black",
                                      popupText=start_name,
                                      initNodes=nodesDF)
    #destination
    nodesDF = vrv.createNodesFromLocs(locs=[end],
                                      leafletIconPrefix="glyphicon",
                                      leafletIconType=end_icon,
                                      leafletColor="black",
                                      popupText=end_name,
                                      initNodes=nodesDF)

    assignmentsDF = vrv.initDataframe('assignments')
    #arcs
    shapepointsDF = vrv.getShapepoints2D(
                    startLoc         = start,
                    endLoc           = end,
                    routeType        = 'pedestrian',
                    leafletColor     = 'black',
                    dataProvider     = 'ORS-online',
                    dataProviderArgs = {'APIkey': ORS_API_KEY})
    assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)

    #add to map
    mapObj = vrv.createLeaflet(mapObject= mapObj, mapFilename= mapFile, nodes= nodesDF, arcs= assignmentsDF)

    return mapObj, mapFile

def isCloseTo(i,j,k):
    '''
    Return True if c is on or next to the line connecting a and b
    '''

    tolerance = 1e-8
    #change lat lon order to reflect x and y
    i = [ i[1], i[0]]
    j = [ j[1], j[0]]
    k = [ k[1], k[0]]

    delta_x = j[0] - i[0]
    delta_y = j[1] - i[1]
    direction = None
   
    #Check if ab is a vertical line
    if delta_x == 0 and delta_y != 0:
        if delta_y < 0:
            direction = "down"
        elif delta_y > 0: #vertical going up
            direction = "up"
    #Check if line is horizontal
    elif delta_x != 0 and delta_y == 0:
        if delta_x < 0:
            direction = "left"
        elif delta_x > 0:
            direction = "right"
    #Check direction of diagonal line
    elif delta_x >= 0 and delta_y >= 0: #ij goes up from left to right or just straight up
        direction = "up-right"
    elif delta_x >= 0 and delta_y <= 0:
        direction = "down-right"
    elif delta_x <= 0 and delta_y >= 0:
        direction = "up-left"   
    elif delta_x <= 0 and delta_y <= 0:    
        direction = "down-left"
        
    if direction=="up":
        top_right   = [i[0] + tolerance, i[1] + delta_y]
        bottom_left = [i[0] - tolerance, i[1]]
    elif direction=="down":
        top_right   = [i[0] + tolerance, i[1]]
        bottom_left = [i[0] - tolerance, i[1] + delta_y]
    elif direction=="right":
        top_right   = [i[0] + delta_x, i[1] + tolerance]
        bottom_left = [i[0], i[1] - tolerance]
    elif direction == "left":
        top_right   = [i[0], i[1] + tolerance]
        bottom_left = [i[0] + delta_x, i[1] - tolerance]
    elif direction=="up-right":   
        top_right   = [i[0] + delta_x + tolerance, i[1] + delta_y]
        bottom_left = [i[0] - tolerance, i[1]]
    elif direction=="up-left":
        top_right   = [i[0] + tolerance, i[1] + delta_y]
        bottom_left = [i[0] + delta_x - tolerance, i[1]]
    elif direction=="down-right":
        top_right   = [i[0] + delta_x + tolerance, i[1] + delta_y]
        bottom_left = [i[0] - tolerance, i[1] + delta_y]
    elif direction=="down-left":
        top_right   = [i[0] + tolerance, i[1]]
        bottom_left = [j[0] + delta_x - tolerance, i[1] + delta_y]

    # Check if point_c is within the rectangle boundaries
    return (bottom_left[0] <= k[0] <= top_right[0] and bottom_left[1] <= k[1] <= top_right[1])


def getDistancebw(a: list, b: list):
    '''
    Calculate euclidean distance between points a and b
    '''
    distance = ( ((b[0] - a[0])**2) + ((b[1] - a[1]) **2) ) ** 0.5
    return distance

def getCommuteShape(trip_shape, bus_start, bus_end):
    '''
    Get the shape points along the bus route

    Paramters
    ---------
    trip_df: pd.DataFrame
        rows from the shape df for this trip, sorted by shape_pt_sequence
    bus_start: list
        [lat,lon] location of the bus stop which starts the trip
    bus_end: list
        [lat,lon] location of the bus stop which ends the trip

    Returns
    -------
    shape: list
        list of [lat,lon] shape points along the bus route

    '''
    start_idx, start_pt, end_idx, end_pt = 0, [0,0], 0, [0,0]
    fig, ax = plt.subplots()
    ax.plot(bus_start[1], bus_start[0], marker='o', label='Bus stop start')
    for i in trip_shape.index:
        j = i+1
        if j <= trip_shape.index.max():
            loc_i = list([ trip_shape.iloc[i]["shape_pt_lat"] , trip_shape.iloc[i]["shape_pt_lon"] ])
            loc_j = list([ trip_shape.iloc[j]["shape_pt_lat"] , trip_shape.iloc[j]["shape_pt_lon"] ])
            #plt.plot([loc_i[1], loc_j[1]], [loc_i[0], loc_j[0]])
            if isCloseTo(loc_i,loc_j,bus_start):
                start_idx = j
                start_pt = loc_j
                break
    plt.legend()
    plt.show()

    print(f"Bus start {bus_start} and closest shape point {start_pt}")
    
    for i, _ in trip_shape.loc[start_idx:].iterrows():
        j = i+1
        if j <= trip_shape.index.max():
            loc_i = [ trip_shape.iloc[i]["shape_pt_lat"] , trip_shape.iloc[i]["shape_pt_lon"] ]
            loc_j = [ trip_shape.iloc[j]["shape_pt_lat"] , trip_shape.iloc[j]["shape_pt_lon"] ]
            if isCloseTo(loc_i,loc_j,bus_end):
                end_idx = i
                end_pt = loc_i
                break
    
    print(f"Bus end {bus_end} and closest shape point {end_pt}")
    
    if start_idx == end_idx:
        if getDistancebw(bus_start, end_pt) >= getDistancebw(bus_start, bus_end):
            shape = None
        else:
            shape = end_pt
    else:
        shape = []
        for i,row in trip_shape.iloc[start_idx:end_idx+1].iterrows():
            lat = row["shape_pt_lat"]
            lon = row["shape_pt_lon"]
            shape.append([lat,lon])
    
    return shape

def showBus(routeMap, bus_start: list, bus_end: list, route_shape):
    '''
    Plot arcs along bus route as defined by NFTA shape data
    '''
    mapObj, mapFile = routeMap

    assignmentsDF = vrv.initDataframe('assignments')
    if route_shape:
        #Add first arc from the bus_stop_start to the first shape point
        shapepointsDF = vrv.getShapepoints2D(
                        startLoc         = bus_start,
                        endLoc           = route_shape[0],
                        routeType        = 'fastest',
                        leafletColor     = 'black',
                        dataProvider     = 'ORS-online',
                        dataProviderArgs = {'APIkey': ORS_API_KEY})
        assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)

        if len(route_shape)>1:
            for i, pt in enumerate(route_shape):
                j = i+1
                if j < len(route_shape):
                    shapepointsDF = vrv.getShapepoints2D(
                                startLoc         = route_shape[i],
                                endLoc           = route_shape[j],
                                routeType        = 'fastest',
                                leafletColor     = 'black',
                                dataProvider     = 'ORS-online',
                                dataProviderArgs = {'APIkey': ORS_API_KEY})
                    assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)

        #Add last arc from the last shape point to bus_stop_end
        shapepointsDF = vrv.getShapepoints2D(
                startLoc         = route_shape[-1],
                endLoc           = bus_end,
                routeType        = 'fastest',
                leafletColor     = 'black',
                dataProvider     = 'ORS-online',
                dataProviderArgs = {'APIkey': ORS_API_KEY})
        assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)
    
    else:
        #shape is simply a straight line connecting two bus stops
        shapepointsDF = vrv.getShapepoints2D(
                startLoc         = bus_start,
                endLoc           = bus_end,
                routeType        = 'fastest',
                leafletColor     = 'black',
                dataProvider     = 'ORS-online',
                dataProviderArgs = {'APIkey': ORS_API_KEY})
        assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)

    nodesDF = vrv.initDataframe('nodes')
    mapObj = vrv.createLeaflet(mapObject = mapObj, mapFilename=mapFile, nodes=nodesDF, arcs=assignmentsDF)

    return mapObj, mapFile

def lookup(df: pd.DataFrame, id_col_name:str, id_value, target_col_name:str):
    '''
    Use the known id value to find the target value in df when the name of both columns are known also
    '''
    row = df.loc[df[id_col_name] == id_value]
    target_value = row.iloc[0][target_col_name]
    return target_value

def lookupIdx(df: pd.DataFrame, col_name: str, value):
    '''
    Use the known id value to find the index of the target value in df when the name of the column is known
    '''
    idx = list(np.where(df[col_name] == value))[0][0]
    return idx

def getValue(df: pd.DataFrame, column_name: str):
    return df[column_name].tolist()[0]

def viewRoute(result: pd.DataFrame, origin: pd.DataFrame, destination: pd.DataFrame, preference:str, time: int):
    '''
    Visualize the result returned from experiment
    
    Returns
    -------
    routeMap
        Map created using leaflet in veroviz
    '''

    origin_name = getValue(origin, "name")
    destination_name = getValue(destination, "name")
    origin_loc = [ getValue(origin, "lat") , getValue(origin, "lon")]
    destination_loc = [getValue(destination, "lat"),getValue(destination, "lon")]
    routeMap = creatMapObj(origin_name, destination_name, preference, time)

    if result["bus_used"]==0:
        routeMap = showWalking(routeMap, origin_loc,origin_name,"home",destination_loc,destination_name,"home")
    else:
        #get trip_id and stop-id for starting and ending bus stop
        trip_id = int(result["trip_id"])
        start_id= int(result['start_stop_id'])
        end_id = int(result['end_stop_id'])
        #get origin location and destination location
        
        stops, shapes, trips = getData()
        #find location of the starting bus stop from stops_df
        bus_start_lat = lookup(stops, "stop_id", start_id, "stop_lat")
        bus_start_lon = lookup(stops, "stop_id", start_id, "stop_lon")
        bus_start_loc = [ float(bus_start_lat), float(bus_start_lon) ]
        #add walking from origin to the bus stop
        routeMap = showWalking(routeMap, origin_loc, origin_name,"home", bus_start_loc, "Bus Stop" + str(start_id), "star")
        #find location of the ending bus stop from stops df
        bus_end_lat = lookup(stops, "stop_id", end_id, "stop_lat")
        bus_end_lon = lookup(stops, "stop_id", end_id, "stop_lon")
        bus_end_loc = [ float(bus_end_lat), float(bus_end_lon) ]
        #add walking from bus stop to destination
        routeMap = showWalking(routeMap, bus_end_loc, "Bus Stop" + str(end_id), "star", destination_loc, destination_name, "home")

        #Get the shape_id for this trip from trips df
        shape_id = lookup(trips, "trip_id", trip_id, "shape_id")
        #Lookup that shape_id in shapes to get the rows representing the shape of this trip
        trip_shape = shapes.loc[shapes["shape_id"] == shape_id]
        #sort the rows by stop sequence
        trip_shape = pd.DataFrame(trip_shape).sort_values(by="shape_pt_sequence").reset_index(drop=True)
        #get the points in the shape of the commuter's trip only between the bus stops
        commute_shape = getCommuteShape(trip_shape, bus_start_loc, bus_end_loc)
        #plot the shape of the trip betwen the starting and ending bus stops
        routeMap = showBus(routeMap, bus_start_loc, bus_end_loc, commute_shape)

    return routeMap

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Experiment Details")
    parser.add_argument('--origin_id', type=int, help='ID of the origin')
    parser.add_argument('--destination_id', type=int, help='ID of the destination')
    parser.add_argument('--experiment_id', type=str, help='ID of the experiment')
    parser.add_argument('--preference', type=str, help='Preference for the experiment')
    parser.add_argument('--time_of_day', type=int, help='Time of Day in seconds')
    args = parser.parse_args()

    preference = checkPreference(args.preference)
    directory = getDirectory(args.experiment_id)

    result = getResults(directory,args.origin_id,args.destination_id,args.time_of_day,args.preference)
    
    origins, destinations = getExperimentOD(directory)
    origin = origins.loc[origins["name"] == args.origin_id]
    destination = destinations.loc[destinations["name"] == args.destination_id]

    viewRoute(result, origin, destination, args.preferemce, args.time_of_day)

    
