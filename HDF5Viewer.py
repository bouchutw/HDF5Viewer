import sys
import cProfile
import pstats
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QAction,
    QComboBox, QMessageBox, QTableView, QHeaderView, QSplitter, QSizePolicy, QMenu, QInputDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT

from backend.HDF5DataLoader import HDF5Data
from frontend.Model.LazyTableModel import LazyLoadTableModel
import qt_material
from frontend.DataTree import TreeWidget
import numpy as np
from pyqtspinner import WaitingSpinner

class HDF5Viewer(QMainWindow):
    def __init__(self, filename: str = None):
        super().__init__()
        self.setGeometry(50, 50, 1800, 900)
        self.setWindowTitle("HDF5 Viewer" if not filename else filename)

        # Initialize data
        self.data: HDF5Data = None
        self.modified_columns = {}
        self.dataFrame = pd.DataFrame()
        self.item = {}

        # Tree Layout
        self.tree = TreeWidget()
        self.tree.itemClickedSignal.connect(self.update_content)

        # Table Layout
        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # Graph Layout
        self.variable_names_button = QComboBox()
        self.variable_names_button.currentTextChanged.connect(self.on_variable_names_changed)
        self.variable_names_button.setFont(QFont("", 10))

        self.figure = plt.Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Layouts
        tree_layout = QVBoxLayout()
        tree_layout.addWidget(self.tree)
        tree_widget = QWidget()
        tree_widget.setLayout(tree_layout)

        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)
        table_widget = QWidget()
        table_widget.setLayout(table_layout)

        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.variable_names_button)
        graph_layout.addWidget(self.canvas)
        graph_layout.addWidget(self.toolbar)
        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)

        # Splitter Layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(tree_widget)
        splitter.addWidget(table_widget)
        splitter.addWidget(graph_widget)
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
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

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

        if filename:
            self.open_hdf5(filename)

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
            self.spinner.start()
            self.data = HDF5Data(file_name)
            self.data.metadata_loaded.connect(self.on_metadata_loaded)
            self.data.error_occurred.connect(self.on_load_error)
            self.data.start()

    def on_metadata_loaded(self, metadata):
        self.spinner.stop()
        self.tree.update_tree(metadata, self.data.filename)  # Pass the metadata to the tree


    def on_load_error(self, error):
        self.spinner.stop()
        QMessageBox.critical(self, "Error", f"Failed to load HDF5 file: {error}")

    def fill_table(self):
        try:
            self.lazy_model = LazyLoadTableModel(self.dataFrame, rows_per_chunk=100, parent=self)
            self.table.setModel(self.lazy_model)
            self.table.verticalScrollBar().valueChanged.connect(self.check_scroll_position)
            self.table.resizeColumnsToContents()

            header = self.table.horizontalHeader()
            header.setSectionsClickable(True)
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(self.show_header_context_menu)

            self.variable_names_button.clear()
            self.variable_names_button.addItems(list(map(str, self.dataFrame.keys())))
            self.update_plot()
        except Exception as e:
            print(f'Error doing fill_table(): {e}')

    def show_header_context_menu(self, pos):
        header = self.table.horizontalHeader()

        logical_index = header.logicalIndexAt(pos)

        if logical_index != -1:
            menu = QMenu(self)
            rename_action = QAction("Rename Column", self)

            rename_action.triggered.connect(lambda: self.rename_column(logical_index))
            menu.addAction(rename_action)

            menu.exec_(header.mapToGlobal(pos))

    def rename_column(self, column_index):
        model = self.table.model()

        if model is None:
            QMessageBox.warning(self, "Error", "No model is set for the table.")
            return

        current_name = model.headerData(column_index, Qt.Horizontal, Qt.DisplayRole)

        # Get new column name
        new_name, ok = QInputDialog.getText(
            self, "Rename Column", f"Enter new name for column '{current_name}':"
        )

        # If the user cancels or provides an empty name
        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()

        # Check for duplicate column names
        if new_name in self.dataFrame.columns:
            QMessageBox.warning(
                self, "Error", f"Column name '{new_name}' already exists. Choose a different name."
            )
            return

        # Update the column name
        if model.setHeaderData(column_index, Qt.Horizontal, new_name, Qt.EditRole):
            QMessageBox.information(self, "Success", f"Column name updated to '{new_name}'.")
            self.modified_columns[current_name] = new_name
            self.dataFrame.rename(columns={current_name: new_name}, inplace=True)
            # self.fill_table()

        else:
            QMessageBox.warning(self, "Error", "Failed to update column name.")

    def check_scroll_position(self):
        scroll_bar = self.table.verticalScrollBar()
        if scroll_bar.value() == scroll_bar.maximum():
            self.lazy_model.load_more_rows()

    def on_variable_names_changed(self):
        if not self.dataFrame.empty:
            self.update_plot()

    def update_plot(self):
        try:
            ax = self.figure.gca()
            ax.clear()
            if not self.dataFrame.empty:
                try:
                    data = self.dataFrame.iloc[:, self.variable_names_button.currentIndex()]
                    ax.plot(np.arange(len(data)), data, label='Data Plot')
                    ax.set_title(f"{self.item.get('Label', '')}")
                    ax.set_ylabel(f"{self.variable_names_button.currentText()}")
                    ax.legend()
                except Exception:
                    pass
            else:
                ax.text(0.5, 0.5, 'No Data Available', fontsize=14, ha='center', va='center')
            self.canvas.draw()
        except Exception as e:
            print(f'Error doing update_plot(): {e}')

    def update_content(self, item):
        try:
            # Handle unsaved changes
            if self.modified_columns:
                reply = QMessageBox.question(
                    self,
                    "Save Changes",
                    "You have unsaved changes. Do you want to save them before switching?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    )

                if reply == QMessageBox.Yes:
                    if hasattr(self, 'current_item') and self.current_item:
                        key_path = self.current_item.get('Path')
                        if key_path and not self.dataFrame.empty:
                            self.spinner.start()
                            self.data.update_dataset(key_path, self.dataFrame)
                            self.modified_columns.clear()
                            self.spinner.stop()

                elif reply == QMessageBox.No:
                    for old_name, new_name in self.modified_columns.items():
                        self.dataFrame.rename(columns={new_name: old_name}, inplace=True)
                    self.modified_columns.clear()

                elif reply == QMessageBox.Cancel:
                    return

            self.item = item
            self.current_item = item

            if item['Type'] != 'Group' and item['Type'] != 'File' and item['Type'] != None:
                self.spinner.start()
                try:
                    key_path = self.item.get('Path')
                    if key_path:
                        self.dataFrame = self.data.get_by_key(key_path)
                    else:
                        self.dataFrame = pd.DataFrame(self.item['data'])
                    self.fill_table()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update content: {str(e)}")
                finally:
                    self.spinner.stop()
        except Exception as e:
            print(f'Error doing update_content(): {e}')


if __name__ == '__main__':
    # profiler = cProfile.Profile()
    # profiler.enable()
    app = QApplication(sys.argv)
    try:
        if len(sys.argv) > 1:
            filepath = sys.argv[1]
            viewer = HDF5Viewer(filepath)
        else:
            viewer = HDF5Viewer()
    except Exception as e:
        viewer = HDF5Viewer()
    qt_material.apply_stylesheet(app, theme='light_blue.xml')
    viewer.show()
    exit_code = app.exec_()
    # profiler.disable()
    # stats = pstats.Stats(profiler).sort_stats(pstats.SortKey.TIME)
    # stats.dump_stats("profile_result.prof")
    sys.exit(exit_code)
