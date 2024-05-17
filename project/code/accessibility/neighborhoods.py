''' IMPORTS '''
import json
import numpy as np
import os
import pandas as pd
import veroviz as vrv
vrv.checkVersion()

class Neighborhood():
    def __init__(self, boundaryTight, boundaryLoose, color, labelName, labelPoint=[]):
        self.boundaryTight = boundaryTight
        self.boundaryLoose = boundaryLoose
        self.color         = color
        self.labelName     = labelName
        
        if (len(labelPoint) == 0):
            # Find a point that is roughly in the middle of the boundary:
            corners = vrv.getMapBoundary(locs=boundaryTight)
            self.labelPoint = [(corners[0][0] + corners[1][0])/2, (corners[0][1] + corners[1][1])/2]
        else:
            self.labelPoint = labelPoint

def getNeighborhoods(url=None, file=None):
    '''
    url like "https://raw.githubusercontent.com/IE-670/bnmc/data/neighborhoods.json"
    file like "data/neighborhoods.json" 
    '''
    if (url == file == None):
        return 'ERROR: Must provide url or file.'
    
    try:
        import urllib.request
        with urllib.request.urlopen(url) as url:
            data = json.loads(url.read().decode())
        print("Loaded Neighborhood data from GitHub")				
    except:
        with open(file) as fp:
            data = json.load(fp)
        print("Loaded local copy of Neighborhood data")
       
    neighborhoods = {}
    for nb in data:
        neighborhoods[nb] = Neighborhood(data[nb]["boundaryTight"], data[nb]["boundaryLoose"], 
                                         data[nb]["color"], data[nb]["labelName"], 
                                         data[nb]["labelPoint"])

    return neighborhoods    

def createMapNeighborhoods(neighborhoods, mapObject=None, addLabel=True):

    for name in neighborhoods:
        mapObject = vrv.addLeafletPolygon(
                              mapObject     = mapObject, 
                              mapFilename   = None, 
                              mapBackground = 'CartoDB positron', 
                              mapBoundary   = None, 
                              zoomStart     = None, 
                              points        = neighborhoods[name].boundaryTight,    # Set to the appropriate boundary
                              popupText     = None, 
                              lineWeight    = 1, 
                              lineColor     = neighborhoods[name].color, 
                              lineOpacity   = 0.5, 
                              lineStyle     = 'solid', 
                              fillColor     = neighborhoods[name].color, 
                              fillOpacity   = 0.3)
        if (addLabel):
            mapObject = vrv.addLeafletText(
                            mapObject   = mapObject, 
                            anchorPoint = neighborhoods[name].labelPoint, 
                            text        = neighborhoods[name].labelName, 
                            fontSize    = 29, 
                            fontColor   = neighborhoods[name].color) 

        
    return mapObject

class Region(Neighborhood):
    def __init__(self, folder_path):
        '''self.boundaryTight, self.boundaryLoose, self.color = color, self.labelName = labelName'''
        self.folder_path = folder_path
        self.neighborhoods = getNeighborhoods(url  = "https://raw.githubusercontent.com/IE-670/bnmc/data/neighborhoods.json", 
                                              file = "../data/neighborhoods.json")
        self.saveAttributes()
        #self.getData()
        # nbhdMapObject = createMapNeighborhoods(self.neighborhoods, mapObject=None, addLabel=True)
        # vrv.createLeaflet(mapObject = nbhdMapObject, nodes = self.busStops)
    
    def saveAttributes(self):
        '''BUS STOPS'''
        # Save the bus stops to PD dataframe
        stops_file = os.path.join(self.folder_path,"stops.txt")
        stops_df = pd.read_csv(stops_file)
        stops_df = stops_df.drop(columns=["stop_code","wheelchair_boarding","platform_code"])
        
        #Initialize an array to keep the bus stops found in the region
        stops = []
        self.busStopNodes = vrv.initDataframe('nodes')
        for _,row in stops_df.iterrows():
            stop_location = [row['stop_lat'],row['stop_lon']]
            stop_id = row['stop_id']
            inRegion = any(vrv.isPointInPoly(loc= stop_location, poly=self.neighborhoods[nb].boundaryLoose) for nb in self.neighborhoods)
            if inRegion:
                stops.append(row)
                self.busStopNodes = vrv.createNodesFromLocs(locs=[stop_location],initNodes=self.busStopNodes,startNode=stop_id)

        '''TRIPS, STOP TIMES, ROUTES'''
        # Save stop times, trips and calendar attributes to PD dataframes
        stopTimes_df = pd.read_csv( os.path.join(self.folder_path,"stop_times.txt"))
        print(f"Number of stop times for entire system {len(stopTimes_df)} ")
        stopTimes_df = stopTimes_df.drop(columns=["departure_time","stop_headsign","shape_dist_traveled","timepoint"])

        trips_df = pd.read_csv( os.path.join(self.folder_path,"trips.txt"))
        trips_df = trips_df.drop(columns=["block_id","shape_id","wheelchair_accessible","bikes_allowed"])
        
        calendarAttr_df = pd.read_csv(os.path.join(self.folder_path,"calendar_attributes.txt"))
        
        routes_df = pd.read_csv(os.path.join(self.folder_path,"routes.txt"))
        routes_df = routes_df.drop(columns=["agency_id","route_url","route_desc","route_type","route_color","route_text_color","route_sort_order"])

        #save the filtered stops df to csv
        pd.DataFrame(stops).to_csv(path_or_buf=os.path.join(self.folder_path,"filteredBusStops.csv"), index=False)
        #Merge the dataframes on stop_id, trip_id, service_id and route_id
        df = stopTimes_df.merge(pd.DataFrame(stops), on="stop_id")
        print(f"Number of stop times for region {len(df)} ")
        df = df.merge(trips_df, on="trip_id")
        df = df.merge(calendarAttr_df, on="service_id")
        df = df.merge(routes_df, on="route_id")

        #Reorder the columns in the datatframe
        self.data = df.loc[:,['trip_id','trip_headsign','direction_id','service_description','service_id','route_id','route_short_name','route_long_name',\
                              'stop_id','stop_sequence','stop_name','stop_lat','stop_lon','arrival_time']]
        #self.data = df.sort_values(by = "trip_id")
        print(f"Dataframe has {self.data.shape[0]} rows across {self.data.shape[1]} columns:")
        print(f"There are {len(df.trip_id.unique())} unique trips belonging to {len(df.route_id.unique())} routes")
        print(f"These routes are {df.route_id.unique()}")

        self.data.to_csv(path_or_buf=os.path.join(self.folder_path,"myData.csv"), index=False)
        return 0

#Call the function to process raw nfta data and filter the bus stops
#region = Region(folder_path="C:\Users\krysc\Documents\veroviz-test\veroviz\IE670\data\nfta\raw")



