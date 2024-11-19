import sys
from typing import Dict
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QAction, QComboBox, QMessageBox, QProgressDialog, QTableView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from backend import HDF5DataLoader
from frontend.TableGrid import DataFrameTableModel


class HDF5LoaderThread(QThread):
    data_loaded = pyqtSignal(dict)  # Signal to send the loaded data back
    progress = pyqtSignal(int)  # Signal to update progress

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            # Call the loader function directly
            data = HDF5DataLoader.hdf5_to_dataframe(self.file_path)
            self.data_loaded.emit(data)
        except Exception as e:
            self.data_loaded.emit({"error": str(e)})


class HDF5Viewer(QMainWindow):
    def __init__(self, filename: str = None):
        super().__init__()
        self.setGeometry(50, 50, 1600, 800)
        self.setWindowTitle("HDF5 Viewer" if not filename else filename)

        self.data: Dict[str, pd.DataFrame] = {}
        self.loader_thread: HDF5LoaderThread = None
        self.progress_dialog: QProgressDialog = None

        # Create a QVBoxLayout
        self.layout = QVBoxLayout()

        # Create a QWidget and set the layout
        central_widget = QWidget()
        central_widget.setLayout(self.layout)

        self.sheet_names_button = QComboBox()
        self.sheet_names_button.currentTextChanged.connect(self.on_sheet_names_changed)
        font = QFont()
        font.setPointSize(12)
        self.sheet_names_button.setFont(font)

        self.table = QTableView()

        self.layout.addWidget(self.sheet_names_button)
        self.layout.addWidget(self.table)

        # Add the central widget to the Main window
        self.setCentralWidget(central_widget)

        self.statusBar()
        open_action = self.create_action('Open', self.open_hdf5, 'Ctrl+O')
        self.menu = self.menuBar()
        file_menu = self.menu.addMenu('File')
        file_menu.addAction(open_action)
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
            self.start_loader(file_name)

    def start_loader(self, file_path):
        self.progress_dialog = QProgressDialog("Loading HDF5 file...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        # Start the loader thread
        self.loader_thread = HDF5LoaderThread(file_path)
        self.loader_thread.data_loaded.connect(self.on_data_loaded)
        self.loader_thread.start()

    def on_data_loaded(self, data):
        self.progress_dialog.close()

        if "error" in data:
            QMessageBox.critical(self, "Error", f"Failed to load HDF5 file: {data['error']}")
            return

        self.data = data
        self.sheet_names_button.clear()
        sheet_names = list(data.keys())
        self.sheet_names_button.addItems(sheet_names)
        if sheet_names:
            self.sheet_names_button.setCurrentText(sheet_names[0])
            self.fill_table(data[sheet_names[0]])

    def fill_table(self, df: pd.DataFrame):
        model = DataFrameTableModel(df)  # Create the custom model
        self.table.setModel(model)


    def on_sheet_names_changed(self):
        if self.data:
            selected_sheet = self.sheet_names_button.currentText()
            self.fill_table(self.data[selected_sheet])

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
    viewer.show()
    sys.exit(app.exec_())
