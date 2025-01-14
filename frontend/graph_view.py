from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QComboBox, QSizePolicy
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from backend.dataset_model import DatasetModel

class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._datasetModel = DatasetModel()

        self.variable_names_button = QComboBox()
        self.variable_names_button.currentTextChanged.connect(self.plot)
        self.variable_names_button.addItems(list(map(str, self.datasetModel.dataFrame.keys())))
        self.variable_names_button.setFont(QFont("", 10))

        self.figure = plt.Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.variable_names_button)
        graph_layout.addWidget(self.canvas)
        graph_layout.addWidget(self.toolbar)
        self.setLayout(graph_layout)

    @property
    def datasetModel(self) -> DatasetModel:
        """
        Property getter for datasetModel.
        """
        return self._datasetModel

    @datasetModel.setter
    def datasetModel(self, value: DatasetModel):
        if not isinstance(value, DatasetModel):
            raise ValueError("datasetModel must be an instance of DatasetModel.")
        self._datasetModel = value
        self.variable_names_button.clear()
        if not self._datasetModel.dataFrame.empty:
            self.variable_names_button.addItems(list(self._datasetModel.dataFrame.keys()))
        self.clear_plot()
        self.plot()


    def clear_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("white")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("")
        ax.set_xlabel("")
        ax.set_ylabel("")
        self.canvas.draw_idle()

    def clear_graph(self):
        self.clear_plot()
        self.variable_names_button.clear()

    def plot(self):
        try:
            ax = self.figure.gca()
            ax.clear()
            if not self.datasetModel.dataFrame.empty:
                try:
                    data = self.datasetModel.dataFrame.iloc[:, self.variable_names_button.currentIndex()]
                    ax.plot(np.arange(len(data)), data)
                    ax.set_title(f"{self.datasetModel.title}")
                    ax.set_ylabel(f"{self.variable_names_button.currentText()}")
                except Exception:
                    pass
            else:
                ax.text(0.5, 0.5, 'No Data Available', fontsize=14, ha='center', va='center')
            self.canvas.draw()
        except Exception as e:
            print(f'Error doing update_plot(): {e}')