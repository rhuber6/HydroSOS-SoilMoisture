import numpy as np
import pandas as pd
import s3fs
import xarray

# You may set anon to False if you have a credential file stored on your system but it is not necessary for this demonstration
bucket_uri = 's3://geoglows-v2/retro.zarr'
region_name = 'us-west-2'
s3 = s3fs.S3FileSystem(anon=True, client_kwargs=dict(region_name=region_name))
s3store = s3fs.S3Map(root=bucket_uri, s3=s3, check=False)

ds = xarray.open_zarr(s3store)

# Create an empty list to store DataFrames for each month
monthly_stats_list = []
reach_id = 760021611
df = ds['Qout'].sel(rivid=reach_id).to_dataframe()
df = df.reset_index().set_index('time').pivot(columns='rivid', values='Qout')
# Use the first date in the existing DataFrame as the start date
start_date = df.index[0]
end_date = pd.to_datetime(df.index[-1])  # Use the last date in your existing DataFrame

current_date = start_date
while current_date < end_date:
    # Filter the DataFrame for the current month
    df_month = df[(df.index >= current_date) & (df.index < current_date + pd.DateOffset(months=1))]

    # Check if there is data for the current month
    if not df_month.empty:
        # Rename columns and calculate statistics
        df_month = df_month.rename(columns={df_month.columns[0]: 'discharge'})
        total_volume = (df_month["discharge"] * 60 * 60 * 24 / 1_000_000).sum()
        max_flow = df_month["discharge"].max()
        min_flow = df_month["discharge"].min()
        avg_flow = df_month["discharge"].mean()
        median_flow = df_month["discharge"].median()

        # Create a DataFrame for the current month's statistics
        monthly_stats_df = pd.DataFrame({
            'Total Volume': [total_volume],
            'Max Flow': [max_flow],
            'Min Flow': [min_flow],
            'Avg Flow': [avg_flow],
            'Median Flow': [median_flow]
        }, index=[current_date])

        # Append the current month's DataFrame to the list
        monthly_stats_list.append(monthly_stats_df)

    # Move to the next month
    current_date = current_date + pd.DateOffset(months=1)

# Concatenate all DataFrames in the list into a single DataFrame
monthly_stats = pd.concat(monthly_stats_list)
print(len(ds['rivid'].values))