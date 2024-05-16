'''Modules'''
import os
import argparse
import pandas as pd
import time
import sys
import numpy as np
import veroviz as vrv
import matplotlib.pyplot as plt
'''Files'''
from ..use_preferences import route_preferences
from neighborhoods import getNeighborhoods, createMapNeighborhoods
'''Get API Key'''
ORS_API_KEY = os.environ['ORSKEY']

def getData():
    '''Return pd dataframes retrieved from files'''
    stops_df = pd.read_csv(f"data/google_transit/stops.txt")
    shapes_df = pd.read_csv(f"data/google_transit/shapes.txt")
    trips_df = pd.read_csv(f"data/google_transit/trips.txt")
    return stops_df, shapes_df, trips_df

def getOD(directory:str, origin: int, destination: int):
    ''' Returns a single row from origins and destinations dataframes'''
    origins = pd.read_csv(f"{directory}origins.csv")
    destinations = pd.read_csv(f"{directory}destinations.csv")
    origin = origins.loc[origins["name"] == origin]
    destination = destinations.loc[destinations["name"] == destination]

    return origin, destination

def creatMapObj(origin_name: str, destination_name: str, mode: str):
    '''
    Use existing code to create a map oject
    '''
    neighborhoods = getNeighborhoods(url  = "https://raw.githubusercontent.com/IE-670/bnmc/data/neighborhoods.json", 
                                    file = "data/neighborhoods.json")
    nbhdMapObject = createMapNeighborhoods(neighborhoods, mapObject=None, addLabel=False)

    map_name = "route"+ origin_name + "-" + destination_name + "-" + mode + ".html"
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

def isCloseTo(i,j,k,tolerance):
    '''
    Return True if c is on or next to the line connecting a and b
    '''
    #Check if ab is a vertical line
    if (j[1] - i[1]) == 0:
        delta_lon = 0
        delta_lat = j[0] - i[0]
        if delta_lat <= 0: #vertical going down
            m = -1
        else: #vertical going up
            m = 1
    #Otherwise find slope of line ab
    else:
        delta_lon = j[1] - i[1]
        delta_lat = j[0] - i[0]
        m = delta_lat / delta_lon
    
    if m > 0: #ij goes up from left to right or just straight up
        top_right = [j[1] + tolerance, j[0]]
        bottom_left = [i[1] - tolerance, i[0]]
    elif m < 0: #ab goes down from left to right or just straight down
        top_right = [i[1] + delta_lon + tolerance, i[0]]
        bottom_left = [j[1] - tolerance - delta_lon, j[0]]
    else:
        top_right = [j[1], j[0] + tolerance]
        bottom_left = [i[1], i[0] - tolerance]

    # Check if point_c is within the rectangle boundaries
    return (bottom_left[0] <= k[1] <= top_right[0] and
            bottom_left[1] <= k[0] <= top_right[1])

def getDistancebw(a,b):
    distance = ( ((b[0] - a[0])**2) + ((b[1] - a[1]) **2) ) ** 0.5
    return distance

def getCommuteShape(trip_shape, bus_start, bus_end):
    '''
    Get the shape points along the bus route
    '''
    for i in trip_shape.index:
        j = i+1
        if j <= trip_shape.index.max():
            loc_i = list([ trip_shape.iloc[i]["shape_pt_lat"] , trip_shape.iloc[i]["shape_pt_lon"] ])
            loc_j = list([ trip_shape.iloc[j]["shape_pt_lat"] , trip_shape.iloc[j]["shape_pt_lon"] ])
            if isCloseTo(loc_i,loc_j,bus_start,1e-8):
                start_idx = j
                start_pt = loc_j
                break

    print(f"Bus start {bus_start} and closest shape point {start_pt}")
    
    for i, _ in trip_shape.loc[start_idx:].iterrows():
        j = i+1
        if j <= trip_shape.index.max():
            loc_i = [ trip_shape.iloc[i]["shape_pt_lat"] , trip_shape.iloc[i]["shape_pt_lon"] ]
            loc_j = [ trip_shape.iloc[j]["shape_pt_lat"] , trip_shape.iloc[j]["shape_pt_lon"] ]
            if isCloseTo(loc_i,loc_j,bus_end,1e-8):
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
        for i,row in shape.iloc[start_idx:end_idx+1].iterrows():
            lat = row["shape_pt_lat"]
            lon = row["shape_pt_on"]
            shape.append([lat,lon])

    
    return shape #return as a np.array instead of dataframe

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
                        routeType        = 'manhattan',
                        leafletColor     = 'black',
                        dataProvider     = 'ORS-online',
                        dataProviderArgs = {'APIkey': ORS_API_KEY})
        assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)

        if len(route_shape>1):
            for i, pt in enumerate(route_shape):
                j = i+1
                if j < len(route_shape):
                    shapepointsDF = vrv.getShapepoints2D(
                                startLoc         = route_shape[i],
                                endLoc           = route_shape[j],
                                routeType        = 'manhattan',
                                leafletColor     = 'black',
                                dataProvider     = 'ORS-online',
                                dataProviderArgs = {'APIkey': ORS_API_KEY})
                    assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)

        #Add last arc from the last shape point to bus_stop_end
        shapepointsDF = vrv.getShapepoints2D(
                startLoc         = route_shape[-1],
                endLoc           = bus_end,
                routeType        = 'manhattan',
                leafletColor     = 'black',
                dataProvider     = 'ORS-online',
                dataProviderArgs = {'APIkey': ORS_API_KEY})
        assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)
    
    else:
        #shape is simply a straight line connecting two bus stops
        shapepointsDF = vrv.getShapepoints2D(
                startLoc         = bus_start,
                endLoc           = bus_end,
                routeType        = 'shortest',
                leafletColor     = 'black',
                dataProvider     = 'ORS-online',
                dataProviderArgs = {'APIkey': ORS_API_KEY})
        assignmentsDF = pd.concat([assignmentsDF, shapepointsDF], ignore_index=True, sort=False)

    nodesDF = vrv.initDataframe('nodes')
    mapObj = vrv.createLeaflet(mapObject = mapObj, mapFilename=mapFile, nodes=nodesDF, arcs=assignmentsDF)

    return mapObj, mapFile

def lookup(df,id_col_name:str, id_value, target_col_name:str):
    '''Use the known id value to find the target value in df when the name of both columns are known also'''
    row = df.loc[df[id_col_name] == id_value]
    target_value = row.iloc[0][target_col_name]
    return target_value

def lookupIdx(df,col_name,value):
    idx = list(np.where(df[col_name] == value))[0][0]
    return idx

def viewRoute(all_routes: pd.DataFrame, origin: int, destination: int, preference: str, directory: str):
    '''
    Visualize the result returned from experiment
    Parameters
    ----------
    result : pd.Series
        The row of the results.csv file which represents a single O/D route to be visualized
    Returns
    -------
    routeMap
        Map created using leaflet in veroviz
    '''

    routeMap = creatMapObj(origin_name, destination_name, preference)
    result = route_preferences(all_routes,time,origin,destination,preference)

    origin, destination = getOD(directory, origin, destination)

    if result["bus_used"]==0:
        origin_loc = [origin["lat"],origin["lon"]]
        destination_loc = [destination["lat"],destination["lon"]]
        routeMap = showWalking(routeMap, origin_loc,origin_name,"home",destination_loc,destination_name,"home")

    else:

        #get trip_id and stop-id for starting and ending bus stop
        trip_id = int(result["trip_id"])
        start_id= int(result['bus_id_start'])
        end_id = int(result['bus_id_end'])
        #get origin location and destination location
        origin_loc = [ result["origin_lat"], result["origin_lon"]]
        origin_name = result["start_name"]
        destination_loc = [ result["destination_lat"], result["destination_lon"]]
        destination_name = result["poi_name"]
        
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
        commute_shape = getCommuteShape(trip_shape, bus_start_lat, bus_start_lon, bus_end_lat, bus_end_lon)
        #plot the shape of the trip betwen the starting and ending bus stops
        routeMap = showBus(routeMap, bus_start_loc, bus_end_loc, commute_shape)

    return routeMap

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Experiment Details")
    parser.add_argument('origin_id', type=int, help='ID of the origin')
    parser.add_argument('destination_id', type=int, help='ID of the destination')
    parser.add_argument('experiment_id', type=int, help='ID of the experiment')
    parser.add_argument('preference', type=str, help='Preference for the experiment')
    args = parser.parse_args()
    experiment_id = args.experiment_id

    directory = f"experiments/{experiment_id}/"
    if not os.path.exists(directory):
        print("ERROR: Experiment ID not found!")
        exit()

    all_routes = pd.read_csv(directory+"results.csv")
    viewRoute(all_routes, args.origin_id, args.destination_id, args.preference, directory)

    
