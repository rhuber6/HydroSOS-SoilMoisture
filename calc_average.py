import numpy as np
import pandas as pd
import xarray
import os
import glob

folder_path = '/Users/rachel1/downloads/vpu_101/'
ds = xarray.open_mfdataset(os.path.join(folder_path, '*.nc'))
# Use glob to get a list of all .nc files in the folder
nc_files = glob.glob(os.path.join(folder_path, '*.nc'))

ds_filtered = ds.sel(time=slice('1991-01-01', '2020-12-31'))
ds_grouped_avg = ds.resample(time='1M').mean(dim='time')

# Convert the data type of ds_grouped_avg to float64
#ds_grouped_avg = ds_grouped_avg.astype(np.float64)

#ds_grouped_volume = ds_grouped_avg * 60 * 60 * 24 * ds_grouped_avg.time.dt.days_in_month / 1_000_000
ds_grouped_median = ds.resample(time='1M').mean(dim='time')

# Convert the data type of ds_grouped_median to float64
#ds_grouped_median = ds_grouped_median.astype(np.float64)

# Combine the datasets into one dataset

combined_dataset = xarray.Dataset({
    'ds_grouped_avg': ds_grouped_avg.to_array(),
    #'ds_grouped_volume': ds_grouped_volume.to_array(),
    'ds_grouped_median': ds_grouped_median.to_array()
})

# Save the combined dataset to a NetCDF file
combined_dataset.to_netcdf(os.path.join(folder_path, 'combined_all_data_101.nc'))

monthly_average = ds_filtered.groupby('time.month').mean(dim='time')
monthly_std_dev = ds_filtered.groupby('time.month').std(dim='time')

# Convert the data type of monthly_average and monthly_std_dev to float64
# monthly_average = monthly_average.astype(np.float64)
# monthly_std_dev = monthly_std_dev.astype(np.float64)

# Combine the two data arrays into one dataset
combined_dataset_monthly = xarray.Dataset({
    'monthly_average': monthly_average.drop_vars('Qout_err').to_array(),
    'monthly_std_dev': monthly_std_dev.drop_vars('Qout_err').to_array()
})

# Save the combined dataset to a NetCDF file
combined_dataset_monthly.to_netcdf(os.path.join(folder_path, 'combined_monthly_data.nc'))