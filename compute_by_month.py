import pandas as pd
import numpy as np
import geopandas as gpd
import json
import datetime
from datetime import date
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from datetime import datetime, timedelta
from dateutil import relativedelta
import matplotlib.patches as mpatches

plt.ioff()  # Turn off interactive mode

hist = pd.read_csv("/Users/rachel1/Downloads/Ecuador_precip.csv")
hist["month"] = pd.to_datetime(hist["month"], format="%Y-%m-%d")

area = gpd.read_file("/Users/rachel1/Documents/geojson_ecuador_simplified/combined.geojson")
#area.loc[11, "ADM1_ES"] = "Imbabura"

#print(area)



current_date = datetime(2005, 1, 1)

cuencas = []
classification = []
month = current_date.month
year = current_date.year
for region in hist.columns:
    if region == "month":
        continue
    hist_df = pd.DataFrame(hist.set_index("month")[region])
    avg_df = hist_df.copy()
    avg_df = avg_df[avg_df.index.year >= 2001]
    avg_df = avg_df[avg_df.index.year <= 2020]
    filtered_month = pd.DataFrame(hist_df[hist_df.index.month == month])
    avg = avg_df.groupby(avg_df.index.month).mean()[region][month]
    filtered_month["ratio"] = filtered_month[region] / avg
    filtered_month["rank"] = filtered_month["ratio"].rank()
    filtered_month.loc[:, "percentile"] = filtered_month.loc[:, "rank"] / (len(filtered_month["rank"]) + 1)
    df_subset = filtered_month.loc[filtered_month.index.year == year]
    val = df_subset["percentile"][0]
    if val >= 0.87:
        category = "extremely wet"
    elif val >= 0.72:
        category = "wet"
    elif val >= 0.28:
        category = "Normal range"
    elif val >= 0.13:
        category = "dry"
    else:
        category = "extremely dry"

    classification.append(category)
    cuencas.append(region)
dict_cuencas = {"classification": classification, "ADM1_ES": cuencas}
vals_df = pd.DataFrame(dict_cuencas)
map_this = area.merge(vals_df, on="ADM1_ES")
month_year = current_date.strftime("%B %Y")
# Create a new figure and axes
fig, ax = plt.subplots(figsize=(10, 10))

colors = {
    "extremely dry": "#CD233F",
    "dry": "#FFA885",
    "Normal range": "#E7E2BC",
    "wet": "#8ECEEE",
    "extremely wet": "#2C7DCD"
}

# Define the order of the categories in the classification column
cat_order = ["extremely dry", "dry", "Normal range", "wet", "extremely wet"]

# Create a Pandas categorical variable for the classification column, using the cat_order
map_this["classification_cat"] = pd.Categorical(map_this["classification"], categories=cat_order)

gdf = gpd.GeoDataFrame(map_this, geometry='geometry')
gdf = gdf.drop(columns=['validOn', 'validTo'])
gdf['date'] = gdf['date'].dt.date.astype(str)


# Convert the GeoDataFrame to GeoJSON
geojson_to_map = gdf.to_json()

print("finished")