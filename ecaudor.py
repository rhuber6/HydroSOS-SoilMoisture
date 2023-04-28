import os
import geopandas as gpd
import pandas as pd

# set path to directory containing GeoJSON files
path_to_files = "/Users/rachel1/Documents/geojson_ecuador_simplified"

# create empty GeoDataFrame
gdf = gpd.GeoDataFrame()

# loop through files in directory and add them to GeoDataFrame
for file_name in os.listdir(path_to_files):
    if file_name == "Ecuador.json":
        continue
    if file_name.endswith(".json"):
        file_path = os.path.join(path_to_files, file_name)
        temp_gdf = gpd.read_file(file_path)
        gdf = pd.concat([gdf, temp_gdf], ignore_index=True)

# write out combined GeoDataFrame to new GeoJSON file
gdf.to_file("/Users/rachel1/Documents/geojson_ecuador_simplified/combined.geojson", driver="GeoJSON")
