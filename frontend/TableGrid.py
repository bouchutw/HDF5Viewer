from PyQt5.QtCore import QAbstractTableModel, Qt, QDir
import pandas as pd
from PyQt5.QtWidgets import QInputDialog, QLineEdit

def check_dataframe(func):
    def wrapper(self, *args, **kwargs):
        if self._data is None or self._data.empty:
            raise Exception('dataframe is empty')
        return func(self, *args, **kwargs)
    return wrapper

class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, dataframe: pd.DataFrame):
        super().__init__()
        self._data = dataframe


    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            # Return the data to display in the table
            return str(self._data.iat[index.row(), index.column()])

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            elif orientation == Qt.Vertical:
                return str(self._data.index[section])
        return None

    @check_dataframe
    def gettimestamp(self) -> str:
        try:
            timestamp: str = next((key for key in self._data.keys() if 'timestamp' in key or 'time' in key), None)
            if timestamp is not None:
                return timestamp
            else:
                timestamp, ok = QInputDialog().getText(self, title="Error getting timestamp label",
                                              label= "Timestamp label:", echo=QLineEdit.Normal)
            if ok and timestamp:
                return timestamp
            return None
        except Exception as e:
            print("Problem getting timestamp label: \n", e)