from typing import Dict
import h5py
import numpy as np
import pandas as pd


def hdf5_to_dataframe(data_path: str) -> Dict[str, pd.DataFrame]:
    """
    Decomposes an HDF5 file into a dictionary of DataFrames, one per group.

    Args:
        data_path (str): Path to the HDF5 file.

    Returns:
        Dict[str, pd.DataFrame]: A dictionary where keys are group names and values are DataFrames.
    """
    group_dataframes = {}  # To store DataFrames with group names as keys

    try:
        # Open the HDF5 file in read mode
        with h5py.File(data_path, 'r') as hdf:
            print(f"Opened HDF5 file: {data_path}")

            # Recursive function to explore groups and datasets
            def explore_group(group, prefix=""):
                group_dict = {}  # Dictionary to collect data for this group

                for key in group:
                    item = group[key]
                    if isinstance(item, h5py.Group):
                        explore_group(item, prefix=f"{key}")  # Recursive exploration
                    elif isinstance(item, h5py.Dataset):
                        try:
                            # Add dataset to group_dict
                            group_dict[key] = np.array(item)
                        except Exception as dataset_error:
                            print(f"Error reading dataset {prefix}_{key}: {dataset_error}")

                # If the group has datasets, convert the dict to a DataFrame
                if group_dict:
                    try:
                        df = pd.DataFrame(group_dict)
                        group_dataframes[prefix] = df
                        print(f"Created DataFrame for group: {prefix}")
                    except Exception as dataframe_error:
                        print(f"Error creating DataFrame for group {prefix}: {dataframe_error}")

            # Start exploring from the root
            explore_group(hdf)

        return group_dataframes

    except Exception as e:
        print(f"Error processing HDF5 file: {e}")
        return group_dataframes