import sys
from typing import List, Dict
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, \
    QWidget, QAction, QComboBox, QDialogButtonBox, QMessageBox
from PyQt5.QtGui import QIcon, QFont
from backend import HDF5DataLoader

class HDF5Viewer(QMainWindow):
    def __init__(self, filename: str = None):
        super().__init__()
        if filename:
            self.setWindowTitle(filename)
        self.setGeometry(50, 50, 1600, 800)

        self.data: Dict[pd.DataFrame]() = {}

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

        self.table = QTableWidget()

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
            self.open_excel(filename)

    def create_action(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
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

    def open_hdf5(self, filename):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        if not filename:
            file_name, _ = QFileDialog.getOpenFileName(self, 'Open hdf5 File', '',
                                                       'hdf5 Files (*.hdf5);;All Files (*)',
                                                       options=options)
        else:
            file_name = filename
        if file_name:
            try:
                self.data.clear()
                self.sheet_names_button.clear()
                self.data = HDF5DataLoader.hdf5_to_dataframe(file_name)
                sheet_names = list(self.data.keys())
                self.sheet_names_button.addItems(sheet_names)
                self.sheet_names_button.setCurrentText(sheet_names[0])
                df = self.data[sheet_names[0]]
                self.fill_table(df)
                print("table charged")
            except Exception as e:
                message_box = QMessageBox()
                message_box.setText(f"Error opening Excel File: {e}")
                message_box.exec_()



    def fill_table(self, df: pd.DataFrame):
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        for i in range(len(df)):
            for j in range(len(df.columns)):
                self.table.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))
        self.table.resizeColumnsToContents()

    def on_sheet_names_changed(self):
        if self.data:
            self.fill_table(df= self.data[self.sheet_names_button.currentText()])
            print("table update")
        else: print('data not found')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        # Check if a file path is provided in the arguments
        if len(sys.argv) > 1:
            filepath = sys.argv[1]
            print(f"Opening file: {filepath}")  # Debugging log to verify filepath
            viewer = HDF5Viewer(filepath)
        else:
            print("No file path provided. Opening without file.")  # Debugging log
            viewer = HDF5Viewer()
    except Exception as e:
        print(f"An error occurred: {e}")  # Catch and log any unexpected errors
        viewer = HDF5Viewer()
    viewer.show()
    sys.exit(app.exec_())
