import sys
from typing import Dict
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QAction,
    QComboBox, QMessageBox, QTableView, QHBoxLayout, QTableWidgetItem
)
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from backend.HDF5DataLoader import HDF5Data
from frontend.TableGrid import DataFrameTableModel
from PyQt5.QtCore import Qt
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
        self.data: HDF5Data = HDF5Data()
        self.dataFrame: pd.DataFrame = None
        self.item = {}

        # Tree Layout
        self.tree = TreeWidget()
        self.tree.itemClickedSignal.connect(self.update_content)

        # Table Layout
        self.table = QTableView()

        # Graph Layout with ComboBox for Variable Names
        self.variable_names_button = QComboBox()
        self.variable_names_button.currentTextChanged.connect(self.on_variable_names_changed)
        self.variable_names_button.setFont(QFont("", 10))

        self.figure = plt.Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
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

        # Splitter Layout: Resizable Tree, Table, Graph
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(tree_widget)
        splitter.addWidget(table_widget)
        splitter.addWidget(graph_widget)

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

        # About Menu with Version
        about_menu = self.menu.addMenu('About')
        version_action = QAction(f"Version: v1.0.0", self)
        about_menu.addAction(version_action)

        # Open file if provided
        if filename:
            self.open_hdf5(filename)

    def create_action(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
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
            self.load_data(file_name)

    def load_data(self, file_path):
        # self.spinner.start()
        try:
            self.table.setModel(None)
            self.variable_names_button.clear()
            self.figure.clear()
            self.data = HDF5Data(file_path)
            self.tree.update_tree(self.data)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load HDF5 file: {str(e)}")
        #
        # finally:
        #     self.spinner.stop()

    def fill_table(self):
        model = DataFrameTableModel(self.dataFrame)
        self.table.setModel(model)
        self.table.resizeColumnsToContents()
        self.variable_names_button.clear()
        self.variable_names_button.addItems(list(map(str, self.dataFrame.keys())))
        self.update_plot()

    def on_variable_names_changed(self):
        if self.dataFrame is not None and not self.dataFrame.empty:
            self.update_plot()

    def update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if self.dataFrame is not None and not self.dataFrame.empty:
            try:
                data = self.dataFrame.loc[:, self.variable_names_button.currentIndex()]
                ax.plot(np.arange(len(data)),
                        data,
                        label='Data Plot')
                ax.set_title(f"{self.item['Label']}")
                ax.set_ylabel(f"{self.variable_names_button.currentText()}")
            except Exception as e:
                pass
        else:
            ax.text(0.5, 0.5, 'No Data Available', fontsize=14, ha='center', va='center')

        # Redraw the canvas
        self.canvas.draw()

    def update_content(self, item):
        self.item = item
        if item['Type'] != 'Group' and item['Type'] != 'File':
            # self.spinner.start()
            try:
                self.dataFrame = pd.DataFrame(item['data'])
                self.fill_table()
                self.update_plot()
            except Exception as e:
                print(e)
            # finally:
            #     self.spinner.stop()


if __name__ == '__main__':
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
    sys.exit(app.exec_())
