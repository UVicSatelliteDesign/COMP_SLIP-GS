from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class GraphWrapperClass(QWidget):
    def __init__(self, 
                 graph: ExpandingGraph,
                 id: int,
                 update_interval: int = 1000,
                 parent: QWidget | None = None):
        """
        Wrapper class to wrap graph as a QWidget so that it can be displayed.

        :param graph: `ExpandingGraph` object which plots the graph.
        :param id: ID of the graph.
        :param update_interval: ms after which graph auto-updates (optional). Default is `1000`ms.
        :param parent: Parent of the widget (optional). Default is `None`.
        """
        super().__init__(parent)

        self.id = id
        self.graph = graph
        self.update_interval = update_interval

        layout = QVBoxLayout()
        canvas = FigureCanvas(graph.fig)

        layout.addWidget(canvas)

        self.setLayout(layout)


    def auto_update_graph(self):
        """
        Updates values on graph.
        """
        self.graph.start_animation(self.update_interval)


    def get_title(self) -> str:
        """
        Returns title of graph.
        """
        return self.graph.get_title()
    

    def get_id(self) -> int:
        """
        Returns ID of graph.
        """
        return self.id