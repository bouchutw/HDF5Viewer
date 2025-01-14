from PyQt5.QtCore import QAbstractTableModel, Qt

class LazyLoadTableModel(QAbstractTableModel):
    def __init__(self, data_frame, rows_per_chunk=100, parent=None):
        super().__init__(parent)
        self._data = data_frame
        self._rows_per_chunk = rows_per_chunk
        self._rows_loaded = rows_per_chunk  # Initially load the first chunk

    def rowCount(self, parent=None):
        return min(self._rows_loaded, len(self._data))

    def columnCount(self, parent=None):
        return len(self._data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row, column = index.row(), index.column()
        if role == Qt.DisplayRole:
            return str(self._data.iat[row, column])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._data.columns[section]
        elif role == Qt.DisplayRole and orientation == Qt.Vertical:
            return str(self._data.index[section])
        return None

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role == Qt.EditRole and orientation == Qt.Horizontal:
            try:
                # Ensure all column names are strings
                self._data.columns = self._data.columns.astype(str)

                # Update the column name
                self._data.columns.values[section] = str(value)

                # Emit a signal to notify the view
                self.headerDataChanged.emit(orientation, section, section)
                return True
            except Exception as e:
                print(f"Error updating column name: {e}")
                return False
        return False

    def flags(self, index):
        # Allow editing of data cells and headers
        default_flags = super().flags(index)
        return default_flags | Qt.ItemIsEditable

    def load_more_rows(self):
        previous_rows = self._rows_loaded
        self._rows_loaded = min(self._rows_loaded + self._rows_per_chunk, len(self._data))

        if self._rows_loaded > previous_rows:
            self.layoutChanged.emit()
