import h5py
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from backend.dataset_model import DatasetModel


class HDF5Data(QThread):
    metadata_loaded = pyqtSignal(dict)  # Emits metadata for the QTreeWidget
    error_occurred = pyqtSignal(str)  # Emits error messages

    def __init__(self, filename=None):
        """
        Initialize the HDF5Data object.

        Args:
            filename (str): Path to the HDF5 file.
        """
        super().__init__()
        self.filename = filename
        self.metadata = {}  # Store metadata here

    def run(self):
        """
        Load the HDF5 file metadata in a separate thread.
        """
        try:
            if not self.filename:
                raise ValueError("Filename not provided.")
            self.metadata = self._load_metadata()  # Store metadata
            self.metadata_loaded.emit(self.metadata)  # Emit metadata to the app
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _load_metadata(self):
        """
        Load metadata (groups and datasets) for the HDF5 file.

        Returns:
            dict: Metadata representing the structure of the HDF5 file.
        """
        metadata = {}

        with h5py.File(self.filename, 'r') as h5file:
            self._process_group(h5file, '/', metadata)

        return metadata

    def _process_group(self, h5file, path, metadata):
        """
        Recursively process an HDF5 group to extract metadata.

        Args:
            h5file (h5py.File): Open HDF5 file object.
            path (str): Current group path.
            metadata (dict): Dictionary to store metadata.
        """
        for key in h5file[path].keys():
            item_path = f"{path}{key}"
            if isinstance(h5file[item_path], h5py.Group):
                # Add group to metadata and recurse
                metadata[key] = {"Type": "Group", "Path": item_path, "Children": {}}
                self._process_group(h5file, f"{item_path}/", metadata[key]["Children"])
            elif isinstance(h5file[item_path], h5py.Dataset):
                # Add dataset to metadata
                metadata[key] = {"Type": "Dataset", "Path": item_path}

    def get_metadata(self):
        """
        Get the stored metadata.

        Returns:
            dict: The metadata dictionary.
        """
        if not self.metadata:
            raise ValueError("Metadata has not been loaded yet.")
        return self.metadata

    def get_by_key(self, key_path):
        """
        Get a specific dataset or group from the HDF5 file by its key.

        Args:
            key_path (str): Full path to the dataset or group.

        Returns:
            object: Dataset or group data.
        """
        if not self.filename:
            raise ValueError("Filename not provided.")
        with h5py.File(self.filename, 'r') as h5file:
            if key_path in h5file:
                dataset = h5file[key_path]
                if isinstance(dataset, h5py.Dataset):
                    if 'columns' in dataset.attrs:
                        columns = dataset.attrs['columns']
                        return DatasetModel(key_path, pd.DataFrame(dataset[()], columns=columns))
                    return DatasetModel(key_path, pd.DataFrame(dataset[()]))
                else:
                    raise ValueError("Path does not point to a dataset.")
            else:
                raise KeyError(f"Key '{key_path}' not found in HDF5 file.")


    def update_dataset(self, datasetModel: DatasetModel):
        """
        Update a specific dataset in the HDF5 file and in the in-memory data.

        Args:
            key_path (str): Dot-separated path to the dataset to update.
            data (pd.DataFrame): The updated data to write back.

        Raises:
            KeyError: If the dataset path does not exist in the HDF5 file.
        """
        try:
            keys = datasetModel.keypath.split('.')
            dataset_path = '/' + '/'.join(keys)

            with h5py.File(self.filename, 'a') as h5file:
                if dataset_path not in h5file:
                    raise KeyError(f"Dataset '{dataset_path}' not found in HDF5 file.")

                del h5file[dataset_path]
                h5file.create_dataset(dataset_path, data=datasetModel.dataFrame.to_numpy())

                h5file[dataset_path].attrs['columns'] = datasetModel.dataFrame.columns.tolist()

        except Exception as e:
            QMessageBox.Warning('update_dataset failed', str(e))
