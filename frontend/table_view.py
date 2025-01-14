from PyQt5.QtWidgets import QWidget, QTableView, QHeaderView, QVBoxLayout, QMessageBox, QInputDialog, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal

from backend.dataset_model import DatasetModel
from frontend.Model.LazyTableModel import LazyLoadTableModel


class TableWidget(QWidget):

    rename_trigger = pyqtSignal(DatasetModel)

    def __init__(self):
        super().__init__()

        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setModel(None)

        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)

        self.setLayout(table_layout)

        self._datasetModel = DatasetModel()
        self.modified_columns = {}


    @property
    def datasetModel(self) -> DatasetModel:
        return self._datasetModel

    @datasetModel.setter
    def datasetModel(self, value: DatasetModel):
        if not isinstance(value, DatasetModel):
            raise ValueError("datasetModel must be an instance of DatasetModel.")
        if self._datasetModel == value:
            return
        self._datasetModel = value
        self.fill_table()


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

        if not ok or not new_name.strip():
            return

        new_name = new_name.strip()

        if new_name in self.datasetModel.dataFrame.columns:
            QMessageBox.warning(
                self, "Error", f"Column name '{new_name}' already exists. Choose a different name."
            )
            return

        if model.setHeaderData(column_index, Qt.Horizontal, new_name, Qt.EditRole):
            QMessageBox.information(self, "Success", f"Column name updated to '{new_name}'.")
            self.modified_columns[current_name] = new_name
            self.datasetModel.dataFrame.rename(columns={current_name: new_name}, inplace=True)
            self.rename_trigger.emit(self.datasetModel)

        else:
            QMessageBox.warning(self, "Error", "Failed to update column name.")

    def fill_table(self):
        try:
            self.modified_columns.clear()
            self.lazy_model = LazyLoadTableModel(self.datasetModel.dataFrame, rows_per_chunk=100, parent=self)
            self.table.setModel(self.lazy_model)
            self.table.verticalScrollBar().valueChanged.connect(self.check_scroll_position)
            self.table.resizeColumnsToContents()

            header = self.table.horizontalHeader()
            header.setSectionsClickable(True)
            header.setContextMenuPolicy(Qt.CustomContextMenu)
            header.customContextMenuRequested.connect(self.show_header_context_menu)
        except Exception as e:
            print(f'Error doing fill_table(): {e}')

    def clear_table(self):
        self.table.setModel(None)
        self.modified_columns.clear()

    def check_scroll_position(self):
        scroll_bar = self.table.verticalScrollBar()
        if scroll_bar.value() == scroll_bar.maximum():
            self.lazy_model.load_more_rows()

    def show_header_context_menu(self, pos):
        header = self.table.horizontalHeader()

        logical_index = header.logicalIndexAt(pos)

        if logical_index != -1:
            menu = QMenu(self)
            rename_action = QAction("Rename Column", self)
            rename_action.triggered.connect(lambda: self.rename_column(logical_index))
            menu.addAction(rename_action)
            menu.exec_(header.mapToGlobal(pos))
