import geopandas as gpd
import networkx as nx
import argparse

from shapely.ops import unary_union

if __name__ == '__main__':
    """
    Prepare rapid namelist files for a directory of VPU inputs
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--vpu_number', type=int, required=True,
                           help='VPU Number')

    args = argparser.parse_args()
    vpu = args.vpu_number
    # Path to your SpatiaLite database file
    database_path = f'/Volumes/EB406_T7_2/source_catchments/catchments_{vpu}.spatialite'

    # Create a connection to the database
    # engine = create_engine(f'spatialite:///{database_path}')

    # Specify the table you want to read
    table_name = 'your_table_name'

    # Read the table into a GeoDataFrame
    # catchment_gdf = gpd.read_postgis(f'SELECT * FROM {table_name}', con=engine)
    catchment_gdf = gpd.read_file(database_path)
    if 100 <= vpu < 200:
        basin = "af"
    elif 200 <= vpu < 300:
        basin = "eu"
    elif 300 <= vpu < 400:
        basin = "si"
    elif 400 <= vpu < 500:
        basin = "as"
    elif 500 <= vpu < 600:
        basin = "au"
    elif 600 <= vpu < 700:
        basin = "sa"
    elif 700 <= vpu < 800:
        basin = "na"
    elif 800 <= vpu < 900:
        basin = "ar"
    else:
        print("FAILED")

    HydroBasins = gpd.read_file(f'/Users/rachel1/Downloads/hybas_{basin}_lev01-12_v1c/hybas_{basin}_lev04_v1c.shp')

    # Step 2: Read the Shapefile
    streams = gpd.read_file(f'/Volumes/EB406_T7_2/source_streams/streams_{vpu}.gpkg')

    if streams.crs != HydroBasins.crs:
        HydroBasins = HydroBasins.to_crs(streams.crs)

    print("read in files")


    def create_directed_graph(gdf):
        G = nx.DiGraph()
        for _, row in gdf.iterrows():
            if row['DSLINKNO'] != -1:  # Only add edges where DSLINKNO is not -1
                G.add_edge(row['DSLINKNO'], row['LINKNO'])
        return G


    G = create_directed_graph(streams)

    outlet_streams = (HydroBasins.set_geometry(HydroBasins.boundary).overlay(streams, keep_geom_type=False)).explode(
        ignore_index=True)

    outlet_streams["ratio"] = (outlet_streams["DSContArea"] / 1000 / 1000) / outlet_streams["UP_AREA"]
    print("have outlet streams")
    # Find rows with duplicated LINKNO values
    duplicated_linkno = outlet_streams[outlet_streams.duplicated(subset=['LINKNO'], keep=False)]

    # Iterate over duplicated LINKNO groups
    for linkno, group in duplicated_linkno.groupby('LINKNO'):
        # Check if any HYBAS_ID in the group is in the NEXT_DOWN column of the same group
        indices_to_delete = group[group['HYBAS_ID'].isin(group['NEXT_DOWN'])].index
        # Drop these rows from the original DataFrame
        outlet_streams = outlet_streams.drop(indices_to_delete)

    # Reset index after deletion
    outlet_streams.reset_index(drop=True, inplace=True)
    outlet_streams = outlet_streams[outlet_streams['ratio'] >= 0.1]
    def closest_to_one(group):
        return group.loc[(group['ratio'] - 1).abs().idxmin()]


    # Apply the function to each group
    result = outlet_streams.groupby('HYBAS_ID').apply(closest_to_one).reset_index(drop=True)


    # result = result[result['DSContArea'] >= 500000000]

    result.set_crs(epsg=4326, inplace=True)

    needed_links = result["LINKNO"].tolist()


    def custom_dfs_paths(G, source, stop_nodes):
        """ Perform DFS from source, generating all paths until a stop node or dead-end is encountered. """
        stack = [(source, [source])]
        while stack:
            (node, path) = stack.pop()
            neighbors = list(G.successors(node))
            if not neighbors or node in stop_nodes:
                yield path
            else:
                for neighbor in neighbors:
                    if neighbor not in path:  # Avoid cycles
                        stack.append((neighbor, path + [neighbor]))


    def custom_dfs(G, source, stop_nodes):
        """ Perform DFS from source, stopping if a node in stop_nodes is encountered. """
        stack = [source]
        visited = set()
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            if node in stop_nodes and node != source:
                continue  # Skip adding to visited and continue
            visited.add(node)
            for neighbor in G.successors(node):
                if neighbor not in visited:
                    stack.append(neighbor)
        return visited


    # Create your directed graph G and GeoDataFrame catchment_gdf
    # G = nx.DiGraph()
    # catchment_gdf = gpd.GeoDataFrame(...)

    # List of LINKNOs to find related rows for
    # needed_links = [160157577, ...]

    # Aggregate all related nodes
    all_related_nodes = set()
    combined_features = []
    linkno_related_nodes_dict = {}
    for linkno in needed_links:
        related_nodes = custom_dfs(G, linkno, set(needed_links))
        linkno_related_nodes_dict[linkno] = related_nodes
        all_related_nodes.update(related_nodes)
        related_rows = catchment_gdf[catchment_gdf['linkno'].isin(related_nodes)]
        related_rows = related_rows.merge(streams[['LINKNO', 'USContArea', 'DSContArea', 'musk_k']], left_on='linkno',
                                          right_on='LINKNO', how='left')
        related_rows['BasinArea'] = related_rows['DSContArea'] - related_rows['USContArea']

        # Combine geometries using unary_union
        combined_geometry = unary_union(related_rows.geometry)
        # k_sums = []

        # Calculate the sum of "k" for each path separately
        # for path in custom_dfs_paths(G, linkno, set(needed_links)):
        #    path_k_sum = related_rows[related_rows['linkno'].isin(path)]['musk_k'].sum()
        #    k_sums.append(path_k_sum)

        # Calculate the average sum of "k"
        # if k_sums:
        #     average_k_sum = sum(k_sums) / len(k_sums)
        # else:
        #     average_k_sum = 0

        combined_attributes = {'LINKNO': linkno, 'geometry': combined_geometry, 'area': related_rows['BasinArea'].sum()}
        combined_features.append(combined_attributes)
    # Create a new GeoDataFrame with the combined features
    combined_gdf = gpd.GeoDataFrame(combined_features, crs=catchment_gdf.crs)
    # Check for rows in the streams GeoDataFrame where DSLINKNO is -1 and LINKNO is not in any related rows
    streams_with_condition = streams[(streams['DSLINKNO'] == -1) & (~streams['LINKNO'].isin(all_related_nodes))]

    # If you want to print or process these rows further
    # print(streams_with_condition)

    # If you want to perform some operation on these rows, you can do so here
    # For example, you might want to flag these rows or save them to a new GeoDataFrame
    # flagged_streams = streams_with_condition.copy()

    # new_needed_links = streams_with_condition["LINKNO"].tolist()

    # all_related_nodes = set()
    # linkno_related_nodes_missed_dict = {}
    # combined_features = []
    # for linkno in new_needed_links:
    #     print(linkno)
    #     related_nodes = custom_dfs(G, linkno, set(needed_links))
    #     linkno_related_nodes_missed_dict[linkno] = related_nodes
    #     # print("check")
    #     all_related_nodes.update(related_nodes)
    #     related_rows = catchment_gdf[catchment_gdf['linkno'].isin(related_nodes)]
    #     related_rows = related_rows.merge(streams[['LINKNO', 'USContArea', 'DSContArea', 'DSLINKNO', 'musk_k']],
    #                                       left_on='linkno', right_on='LINKNO', how='left')
    #     related_rows['BasinArea'] = related_rows['DSContArea'] - related_rows['USContArea']
    #
    #     # Combine geometries using unary_union
    #     combined_geometry = unary_union(related_rows.geometry)
    #     k_sums = []
    #
    #     # Calculate the sum of "k" for each path separately
    #     for path in custom_dfs_paths(G, linkno, set(needed_links)):
    #         path_k_sum = related_rows[related_rows['linkno'].isin(path)]['musk_k'].sum()
    #         k_sums.append(path_k_sum)
    #
    #     # Calculate the average sum of "k"
    #     if k_sums:
    #         average_k_sum = sum(k_sums) / len(k_sums)
    #     else:
    #         average_k_sum = 0
    #
    #     combined_attributes = {'LINKNO': linkno, 'geometry': combined_geometry, 'area': related_rows['BasinArea'].sum(),
    #                            'downstream': related_rows.loc[related_rows['LINKNO'] == linkno, 'DSLINKNO'].iloc[0],
    #                            "musk_k": average_k_sum}
    #     combined_features.append(combined_attributes)
    print("finished_loop")
    # Create a new GeoDataFrame with the combined features
    # combined_gdf_2 = gpd.GeoDataFrame(combined_features, crs=catchment_gdf.crs)
    combined_gdf = combined_gdf.merge(result[['LINKNO', 'HYBAS_ID']], on='LINKNO', how='left')
    combined_gdf = combined_gdf.drop_duplicates()
    combined_gdf = combined_gdf[combined_gdf['area'] >= 100000000]
    combined_gdf.to_file(f"/Volumes/EB406_T7_2/combined_catchments/{vpu}_withHydroBasin_lake_v4.gpkg")
    print("done")
    # combined_gdf_2.to_file("/Users/rachel1/Downloads/combined_catchments_122_K_missed_v4.gpkg")
