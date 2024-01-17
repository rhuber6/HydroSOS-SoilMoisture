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

startDate = datetime(2001, 1, 1)
endDate = datetime(2023, 1, 1)

current_date = startDate
while current_date < endDate:
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

    # Create the colormap
    cmap = ListedColormap(list(colors.values()))

    # Plot the GeoDataFrame and set the fill color based on the "classification_cat" column
    map_this.plot(column="classification_cat", cmap=cmap, linewidth=0.5, edgecolor="black", ax=ax)

    # Create a list of Patch objects, one for each color in the colormap
    patches = [mpatches.Patch(color=color, label=label) for label, color in colors.items()]

    # Add the legend above the plot
    ax.legend(handles=patches, bbox_to_anchor=(0.5, 1.2), loc='upper center', ncol=len(colors))

    # Add a title and remove the axis ticks and labels
    ax.set_title(f'Soil Moisture {month_year}')
    ax.set_xticks([])
    ax.set_yticks([])

    month_str = f"{month:02}"

    plt.savefig(f'/Users/rachel1/Downloads/Ecuador_maps/Ecuador_{year}_{month_str}_precip.png')
    plt.close()
    print(month_year)

    current_date += relativedelta.relativedelta(months=1)
