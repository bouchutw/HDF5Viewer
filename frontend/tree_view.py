from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMessageBox


class TreeWidget(QTreeWidget):
    """
    A QTreeWidget for displaying the structure of an HDF5 file.
    """

    itemClickedSignal = pyqtSignal(dict)

    def __init__(self, hdf5_metadata=None):
        """
        Initialize the TreeWidget. Can be initialized with or without HDF5 metadata.

        :param hdf5_metadata: Dictionary representing the HDF5 file structure.
                              Should include groups and datasets with their paths.
        """
        super().__init__()
        self.hdf5_metadata = hdf5_metadata

        # Set up the QTreeWidget
        self.setHeaderLabels(["Key", "Type"])
        self.itemClicked.connect(self.handle_item_click)

        # Populate the tree if metadata is available
        if hdf5_metadata:
            self.populate_tree()

    def populate_tree(self, path_file: str = " ... "):
        """Populate the QTreeWidget with metadata from the HDF5Data instance."""
        if not self.hdf5_metadata:
            return

        self.clear()

        # Add the root item and populate the tree using metadata
        root_item = QTreeWidgetItem(self, ["Path", path_file ])
        self._populate_tree_recursive(root_item, self.hdf5_metadata)
        self.expandAll()
        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)

    def _populate_tree_recursive(self, parent_item, metadata):
        """Recursively add items to the QTreeWidget from the metadata."""
        for key, value in metadata.items():
            if value.get("Type") == "Group":
                group_item = QTreeWidgetItem(parent_item, [key, "Group"])
                self._populate_tree_recursive(group_item, value.get("Children", {}))
            elif value.get("Type") == "Dataset":
                QTreeWidgetItem(parent_item, [key, "Dataset"])

    def handle_item_click(self, item):
        """
        Handle the item click event and emit information about the clicked item.

        - Emits the usable path for the `get_by_key` function.
        - Emits the type of the item and the label for additional context.
        """
        # Build the HDF5 path based on the item's position in the tree
        hdf5_path = []
        current_item = item
        while current_item:
            hdf5_path.insert(0, current_item.text(0))
            current_item = current_item.parent()

        # Join the path components to create the usable path for get_by_key
        usable_path = "/".join(hdf5_path[1:])  # Skip the root filename

        # Traverse the metadata to find the item's information
        current_metadata = self.hdf5_metadata
        for key in hdf5_path[1:]:
            current_metadata = current_metadata.get(key, {}).get("Children", current_metadata.get(key, {}))

        if not current_metadata:
            QMessageBox.warning(self, "Error", f"Key '{usable_path}' not found in metadata.")
            return

        # Emit the item's information
        self.itemClickedSignal.emit({
            "Label": item.text(0),
            "Type": current_metadata.get("Type"),
            "Path": usable_path
        })

    def update_tree(self, hdf5_metadata, path_file = None):
        """
        Update the tree widget with new HDF5 metadata.

        :param hdf5_metadata: Dictionary representing the updated HDF5 file structure.
        """
        self.hdf5_metadata = hdf5_metadata
        self.populate_tree(path_file)
