#Modules
import argparse
import folium
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point, box
import veroviz as vrv
#Functions
from utils import getDirectory, getResults, checkPreference
ORS_API_KEY = getAPIKey()



def aggregateResults(df: pd.DataFrame):
    '''
    Group the rows of the df by the columns poi_name and start_name
    Aggregate the total_time and total_walk columns by getting the max or mean of those

    Parameters
    ----------
    agg_func: str
        Can be "max" or "mean"

    Returns
    -------
    sorted_group: pd.DataFrame
        grouped and sorted dataframe

    '''
    def calculate_max(series):
        return series.max()

    agg_operation = calculate_max

    grouped = df.groupby(['origin_id', 'destination_id']).agg({
        'total_time': agg_operation,  # Aggregation based on the argument
        'total_walk': agg_operation,  # Aggregation based on the argument
        'origin_lat': 'first',
        'origin_lon': 'first',
        'destination_lat': 'first',
        'destination_lon': 'first'
    }).reset_index()

    sorted_group = grouped.sort_values(by='origin_id').reset_index(drop=True)

    return sorted_group


def createHeatmap(results_df: pd.DataFrame, preference: str):
    '''
    Create heatmap which layers over a map of the 3 neigborhoods

    Parameters
    ----------
    results_df: pd.DataFrame
        read from results.csv file
    
    preferences: str
        preference must be to minimize either time or walking | "min_time" or "min_walk"

    Returns
    ----------
    m
        heatmap

    Notes

    '''

    grouped = aggregateResults(results_df)

    gdf = gpd.GeoDataFrame(grouped, geometry=gpd.points_from_xy(grouped.origin_lon, grouped.origin_lat))

    if preference == 'best_time':
        obj_col = 'total_time'
    else:
        obj_col = 'total_walk'

    # Define the bounds of the grid
    num_div = 10  # 10 seems like a good number for this value
    x_min, y_min, x_max, y_max = gdf.total_bounds
    width = (x_max - x_min) / num_div  # Number of cells horizontally
    height = (y_max - y_min) / num_div  # Number of cells vertically

    # Create the cells in the grid
    rows = int(np.ceil((y_max - y_min) / height))
    cols = int(np.ceil((x_max - x_min) / width))
    grid_cells = []

    for i in range(cols):
        for j in range(rows):
            minx = x_min + i * width
            maxx = x_min + (i + 1) * width
            miny = y_min + j * height
            maxy = y_min + (j + 1) * height
            grid_cells.append(box(minx, miny, maxx, maxy))

    grid = gpd.GeoDataFrame(grid_cells, columns=['geometry'])

    # Ensure the grid has an explicit index column before the spatial join
    grid['grid_index'] = range(len(grid))

    # Spatial join between the grid and the GeoDataFrame
    merged = gpd.sjoin(grid, gdf, how='left', predicate='intersects')

    # Ensure 'total_time' is a float to avoid data type issues during aggregation
    merged[obj_col] = merged[obj_col].astype(float)

    # Aggregate 'total_time' in each grid cell using 'grid_index' to identify cells
    aggregated = merged.dissolve(by="grid_index", aggfunc="mean")

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 10))
    grid.plot(ax=ax, facecolor='none', edgecolor='grey')

    if preference== 'best_time':
        lg_txt = 'Time'
    else:
        lg_txt = 'Walking Distance'

    if preference == 'no_bus':
        lg_txt += ' (only walking; no buses)'
    else:
        lg_txt += ' (using buses)'

    if agg_metric == 'mean':
        lg_metric = "Average"
    if agg_metric == 'max':
        lg_metric = "Maximum"
    else:
        lg_metric = "Range"
    aggregated.plot(column=obj_col, ax=ax, legend=True,
                    legend_kwds={'label': f"{lg_metric} {lg_txt} by Grid Cell",
                                'orientation': "horizontal"})
    plt.show()

    # After aggregating, reset the index so 'grid_index' becomes a column
    aggregated.reset_index(inplace=True)

    # Convert the aggregated GeoDataFrame to GeoJSON
    aggregated_json = aggregated.to_json()

    # Create a folium map centered around the mean of the data points
    map_center_lat = gdf.geometry.y.mean()
    map_center_lon = gdf.geometry.x.mean()
    m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=14)

    # Add choropleth layer without drawing the grid lines
    folium.Choropleth(
        geo_data=aggregated_json,
        name='choropleth',
        data=aggregated,
        columns=['grid_index', obj_col],
        key_on='feature.properties.grid_index',
        fill_color='YlOrRd',  # Color scheme
        fill_opacity=0.7,
        line_opacity=0,  # Setting line opacity to 0 to hide grid lines
        legend_name=f'{lg_metric} {lg_txt}',
        nan_fill_color='none',  # Set empty cells to be transparent
    ).add_to(m)

    # Add a layer control panel to the map
    folium.LayerControl().add_to(m)

    # Save to HTML file
    m.save(f'heatmap_{preference}.html')

    return m
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Experiment Details")
    parser.add_argument('experiment_id', type=str, help='Experiment ID')
    parser.add_argument('preference', type=str, help='Preference for the experiment')
    args = parser.parse_args()

    preference = checkPreference(args.preference)
    directory = getDirectory(args.experiment_id)
    all_routes = getResults(directory)

    createHeatmap(all_routes, preference)
    



