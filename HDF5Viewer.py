import sys
from typing import Dict
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QAction,
    QComboBox, QMessageBox, QTableView, QHBoxLayout
)
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from backend import HDF5DataLoader
from frontend.TableGrid import DataFrameTableModel
from PyQt5.QtCore import Qt
import qt_material

class HDF5Viewer(QMainWindow):
    def __init__(self, filename: str = None):
        super().__init__()
        self.setGeometry(50, 50, 1600, 800)
        self.setWindowTitle("HDF5 Viewer" if not filename else filename)

        self.data: Dict[str, pd.DataFrame] = {}
        self.dataFrame: pd.DataFrame = None
        self.timestamp_label: str = None

        # Top Layout: Dropdown Buttons
        self.sheet_names_button = QComboBox()
        self.sheet_names_button.currentTextChanged.connect(self.on_sheet_names_changed)
        self.sheet_names_button.setFont(QFont("", 10))

        self.variable_names_button = QComboBox()
        self.variable_names_button.currentTextChanged.connect(self.on_variable_names_changed)
        self.variable_names_button.setFont(QFont("", 10))

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.sheet_names_button)
        top_layout.addWidget(self.variable_names_button)

        # Left: Table Layout
        self.table_layout = QVBoxLayout()
        self.table = QTableView()
        self.table_layout.addWidget(self.table)
        table_widget = QWidget()
        table_widget.setLayout(self.table_layout)

        # Right: Graph Layout with Toolbar
        self.figure = plt.Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.canvas)
        graph_layout.addWidget(self.toolbar)
        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)

        # Central Splitter: Resizable Table and Graph
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(table_widget)
        splitter.addWidget(graph_widget)
        splitter.setSizes([900, 600])  # Initial sizes: Table 700px, Graph 900px

        # Main Layout: Top + Splitter
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)  # Top layout for dropdown buttons
        main_layout.addWidget(splitter)  # Splitter for resizable central area

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
        try:
            # Load data synchronously
            data = HDF5DataLoader.hdf5_to_dataframe(file_path)
            self.data = data
            self.sheet_names_button.clear()
            sheet_names = list(data.keys())
            if sheet_names:
                self.sheet_names_button.addItems(sheet_names)
                self.sheet_names_button.setCurrentText(sheet_names[0])
                self.dataFrame = data[sheet_names[0]]
                self.fill_table()
                variable_names = list(self.dataFrame.keys())
                self.variable_names_button.clear()
                self.variable_names_button.addItems(variable_names)
                self.variable_names_button.setCurrentText(variable_names[0])
                self.update_plot()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load HDF5 file: {str(e)}")

    def fill_table(self):
        model = DataFrameTableModel(self.dataFrame)
        self.timestamp_label = model.gettimestamp()
        self.table.setModel(model)

    def on_sheet_names_changed(self):
        if self.data:
            try:
                selected_sheet = self.sheet_names_button.currentText()
                self.dataFrame = self.data[selected_sheet]
                self.fill_table()
                variable_names = list(self.dataFrame.keys())
                self.variable_names_button.clear()
                self.variable_names_button.addItems(variable_names)
                self.variable_names_button.setCurrentText(variable_names[0])
                self.update_plot()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error changing sheet: {str(e)}")

    def on_variable_names_changed(self):
        if self.dataFrame is not None and not self.dataFrame.empty:
            self.update_plot()

    def update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if self.dataFrame is not None and not self.dataFrame.empty:
            try:
                ax.plot(self.dataFrame[self.timestamp_label],
                        self.dataFrame[self.variable_names_button.currentText()],
                        label='Data Plot')
                ax.set_title("Plot of Data")
                ax.set_xlabel(f"{self.timestamp_label}")
                ax.set_ylabel(f"{self.variable_names_button.currentText()}")
            except Exception as e:
                pass
        else:
            ax.text(0.5, 0.5, 'No Data Available', fontsize=14, ha='center', va='center')

        # Redraw the canvas
        self.canvas.draw()

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
