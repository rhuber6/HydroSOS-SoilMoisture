import numpy as np
import pandas as pd
import s3fs
import xarray

ds = xarray.open_dataset("/Users/rachel1/downloads/Qout_101_20150101_20191231.nc")
print(ds)
print(len(ds['rivid'].values))
result_dict = {}
for rivid_value in ds['rivid'].values:
    df_rivid = ds['Qout'].sel(rivid=rivid_value).to_dataframe()
    df_rivid = df_rivid.reset_index().set_index('time').pivot(columns='rivid', values='Qout')
    df_jan_2018 = df_rivid[(df_rivid.index >= '2018-01-01') & (df_rivid.index < '2018-02-01')]
    df_jan_2018 = df_jan_2018.rename(columns={df_jan_2018.columns[0]: 'discharge'})
    total_volume = (df_jan_2018["discharge"] * 60 * 60 * 24 / 1_000_000).sum()
    max_flow = df_jan_2018["discharge"].max()
    min_flow = df_jan_2018["discharge"].min()
    avg_flow = df_jan_2018["discharge"].mean()
    median_flow = df_jan_2018["discharge"].median()
    result_dict[f"{rivid_value}"] = {'total_volume': total_volume, 'max_discharge': max_flow, 'min_discharge': min_flow, 'avg_discharge': avg_flow, 'median_discharge': median_flow}
    # print(rivid_value)

# Convert the result to a new xarray dataset
result_ds = xarray.Dataset(result_dict)
result_ds.to_netcdf("/Users/rachel1/downloads/January_2018.nc")

# Display the resulting xarray dataset
print(result_ds)