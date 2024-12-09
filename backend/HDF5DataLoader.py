import h5py
import numpy as np
from typing import Dict, List

class HDF5Data:
    """
    A class to encapsulate and interact with data loaded from an HDF5 file.
    """

    def __init__(self, filename = None):
        """
        Initialize the HDF5Data object by loading data from the given file.

        Args:
            filename (str): Path to the HDF5 file.
        """
        self.filename = filename
        if filename:
            self.data = self._load_hdf5_data()

    def _load_hdf5_data(self):
        """Load data from the HDF5 file and store it as a nested dictionary."""
        with h5py.File(self.filename, 'r') as h5file:
            return self._load_group(h5file, '/')

    def _load_group(self, h5file, path):
        """Recursively load the contents of an HDF5 group into a dictionary."""
        result = {}
        for key, item in h5file[path].items():
            if isinstance(item, h5py.Dataset):
                result[key] = self._process_dataset(item)
            elif isinstance(item, h5py.Group):
                result[key] = self._load_group(h5file, f"{path}{key}/")
            else:
                raise TypeError(f"Unsupported HDF5 item type for key '{key}': {type(item)}")
        return result

    def _process_dataset(self, dataset):
        """Process an HDF5 dataset into a Python-compatible object."""
        if 'is_bytes' in dataset.attrs:
            return dataset[()]

        if h5py.check_string_dtype(dataset.dtype):
            data = dataset[()]
            if isinstance(data, np.ndarray):
                return data.astype(str)  # Convert arrays of bytes to strings
            if isinstance(data, bytes):
                return data.decode('utf-8')  # Convert single byte string
            return data

        return dataset[()]  # Handle numeric datasets (scalars or arrays)

    def get_data(self):
        """Get the entire loaded data as a dictionary."""
        return self.data

    def get_by_key(self, key_path):
        """
        Get a specific item from the data using a dot-separated key path.

        Args:
            key_path (str): Dot-separated path to the desired item (e.g., "group1.dataset1").

        Returns:
            The requested data or None if the key path does not exist.
        """
        keys = key_path.split('.')
        current = self.data
        for key in keys:
            if key in current:
                current = current[key]
            else:
                return None
        return current

    def __repr__(self):
        """Provide a string representation of the loaded data for debugging."""
        return f"HDF5Data(filename='{self.filename}', data_keys={list(self.data.keys())})"
