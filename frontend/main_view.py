import pandas as pd
from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QVBoxLayout, QWidget, QAction,
    QMessageBox, QTableView, QHeaderView, QSplitter, QMenu, QInputDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from backend.dataset_model import DatasetModel
from backend.hdf5_data import HDF5Data
from frontend.Model.LazyTableModel import LazyLoadTableModel

from frontend.graph_view import GraphWidget
from frontend.table_view import TableWidget
from frontend.tree_view import TreeWidget
import numpy as np
from pyqtspinner import WaitingSpinner


class HDF5Viewer(QMainWindow):
    def __init__(self, filepath: str = None):

        super().__init__()

        self.setGeometry(50, 50, 1800, 900)

        self.setWindowTitle("HDF5 Viewer" if not filepath else filepath)

        self.setWindowIcon(QIcon(r'../resources/HDF5Viewer.ico'))

        # Initialize data & CustomWidget
        self.data: HDF5Data = None

        self.datasetModel = DatasetModel()

        self.tree = TreeWidget()

        self.tree.itemClickedSignal.connect(self.update_content)

        self.table = TableWidget()

        self.graph = GraphWidget()

        self.table.rename_trigger.connect(lambda dataset_model: setattr(self.graph, "datasetModel", dataset_model))

        # Splitter Layout
        splitter = QSplitter(Qt.Horizontal)

        splitter.addWidget(self.tree)

        splitter.addWidget(self.table)

        splitter.addWidget(self.graph)

        splitter.setStretchFactor(0, 1)

        splitter.setStretchFactor(1, 2)

        splitter.setStretchFactor(2, 1)

        splitter.setChildrenCollapsible(False)

        splitter.setHandleWidth(5)

        total_width = self.width()

        splitter.setSizes([int(total_width * 0.2), int(total_width * 0.4), int(total_width * 0.4)])

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)

        # Central Widget
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Menu Bar
        self.statusBar()
        open_action = self.create_action('Open', self.open_hdf5, 'Ctrl+O')
        self.menu = self.menuBar()
        file_menu = self.menu.addMenu('File')
        file_menu.addAction(open_action)

        about_menu = self.menu.addMenu('About')
        version_action = QAction(f"Version: v1.0.1", self)
        about_menu.addAction(version_action)

        # Spinner (Overlay)
        self.spinner = WaitingSpinner(
            self,
            center_on_parent=True,
            disable_parent_when_spinning=True,
            roundness=100.0,
            fade=80.0,
            radius=10,
            lines=20,
            line_length=10,
            line_width=2,
            speed=1.5707963267948966,
        )

        if filepath:
            self.open_hdf5(filepath)

    def create_action(self, text, slot=None, shortcut=None, tip=None):
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        return action

    def open_hdf5(self, filename=None):

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        if not filename:
            file_name, _ = QFileDialog.getOpenFileName(self, 'Open HDF5 File', '',
                                                       'HDF5 Files (*.hdf5);;All Files (*)',
                                                       options=options)
        else:
            file_name = filename

        if file_name:
            # Clear plot
            self.graph.clear_graph()
            self.table.clear_table()

            self.spinner.start()
            self.data = HDF5Data(file_name)
            self.data.metadata_loaded.connect(self.on_metadata_loaded)
            self.data.error_occurred.connect(self.on_load_error)
            self.data.start()

    def on_metadata_loaded(self, metadata):
        self.spinner.stop()
        self.tree.update_tree(metadata, self.data.filename)
        self.graph.clear_graph()

    def on_load_error(self, error):
        self.spinner.stop()
        QMessageBox.critical(self, "Error", f"Failed to load HDF5 file: {error}")

    def update_content(self, item):
        try:
            if self.table.modified_columns:
                reply = QMessageBox.question(
                    self,
                    "Save Changes",
                    "You have unsaved changes. Do you want to save them before switching?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                )

                if reply == QMessageBox.Yes:
                    if self.datasetModel.keypath and not self.datasetModel.dataFrame.empty:
                        self.spinner.start()
                        self.data.update_dataset(self.datasetModel)
                        self.spinner.stop()

                elif reply == QMessageBox.No:
                    for old_name, new_name in self.table.modified_columns.items():
                        self.datasetModel.dataFrame.rename(columns={new_name: old_name}, inplace=True)

                elif reply == QMessageBox.Cancel:
                    return

            self.item = item

            if item['Type'] != 'Group' and item['Type'] != 'File' and item['Type'] != None:
                self.spinner.start()
                try:
                    key_path = self.item.get('Path')
                    self.datasetModel = self.data.get_by_key(key_path)
                    self.graph.datasetModel = self.datasetModel
                    self.table.datasetModel = self.datasetModel

                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update content: {str(e)}")
                finally:
                    self.spinner.stop()
        except Exception as e:
            print(f'Error doing update_content(): {e}')
