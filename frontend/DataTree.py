from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction


#TODO: Set bigger column width to see at least the average label size

class TreeWidget(QTreeWidget):

    itemClickedSignal = pyqtSignal(dict)
    # timestampSelectedSignal = pyqtSignal(str)

    def __init__(self, hdf5_data=None):
        """
        Initialize the DataTree widget. Can be initialized with or without HDF5 data.

        :param hdf5_data: Optional HDF5 data object.
                          Must provide `filename` and `get_data()` methods if provided.
        """
        super().__init__()
        self.hdf5_data = hdf5_data

        # Set up the QTreeWidget
        self.setHeaderLabels(["Key", "Type/Value"])
        self.itemClicked.connect(self.handle_item_click)

        # Populate the tree if data is available
        if hdf5_data:
            self.populate_tree()

    def populate_tree(self):
        """Populate the QTreeWidget with data from the HDF5Data instance."""
        if not self.hdf5_data:
            return

        # Clear the tree before populating it
        self.clear()

        # Add the root item and populate the tree
        root_item = QTreeWidgetItem(self, [self.hdf5_data.filename, "File"])
        self._populate_tree_recursive(root_item, self.hdf5_data.get_data())
        self.expandAll()
        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)


    def _populate_tree_recursive(self, parent_item, data):
        """Recursively add items to the QTreeWidget from the nested dictionary."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    group_item = QTreeWidgetItem(parent_item, [key, "Group"])
                    self._populate_tree_recursive(group_item, value)
                else:
                    QTreeWidgetItem(parent_item, [key, str(type(value).__name__)])
        else:
            QTreeWidgetItem(parent_item, ["Value", str(data)])

    def handle_item_click(self, item):
        """
        Handle the item click event and emit either the group label or the dataset.

        - If the item is a group, emit its label (excluding the root filename).
        - If the item is a dataset, emit the data.
        """
        key_path = []
        current_item = item
        while current_item:
            key_path.insert(0, current_item.text(0))
            current_item = current_item.parent()

        key_path = key_path[1:] if len(key_path) > 1 else []

        dot_path = ".".join(key_path)

        data_or_group = self.hdf5_data.get_by_key(dot_path)
        self.itemClickedSignal.emit({
            "Label": item.text(0),
            "Type": item.text(1),
            "Path": dot_path,
            "data": data_or_group
        })

    def update_tree(self, hdf5_data):
        """
        Update the tree widget with new HDF5 data.

        :param hdf5_data: New HDF5 data object.
                          Must provide `filename` and `get_data()` methods.
        """
        self.hdf5_data = hdf5_data
        self.populate_tree()

    def contextMenuEvent(self, event):

        """Override contextMenuEvent to show a custom right-click menu."""
        # Create a QMenu instance
        menu = QMenu(self)

        # Get the item under the mouse cursor
        item = self.itemAt(event.pos())

        # Check if item was clicked
        if item:
            # Add actions to the menu
            open_action = QAction("set as timestamp", self)
            menu.addAsction(open_action)

        # Show the menu
        menu.exec_(event.globalPos())
