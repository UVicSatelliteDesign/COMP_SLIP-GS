from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from graph_display_button import GraphDisplayButton
from graph_display_area import GraphDisplayArea
from graph_wrapper_class import GraphWrapperClass
from backend.graph_plot import ExpandingGraph


class GraphDisplayLayout(QWidget):
    def __init__(self,
                 graphs: list[ExpandingGraph],
                 w: int = 1200,
                 h: int = 800,
                 update_interval: int = 1000,
                 parent: QWidget | None = None):
        """
        Graph display layout consisting of buttons to toggle between different graphs, and a 
        common graph display area which switches the graph displayed depending on which button is 
        pressed.
        
        :param graphs: List containing `ExpandingGraph` objects.
        :param w: Width of display area (optional). Default is `1200`px.
        :param h: Height of display area (optional). Default is `800`px.
        :param update_interval: ms after which graph auto-updates (optional). Default is `1000`ms.
        :param parent: Parent of graph display layout (optional). Default is `None`
        """
        super().__init__(parent)

        self.update_interval = update_interval
        self.graphs = self.make_compatible(graphs)
        self.graphs_display = GraphDisplayArea(w, h, self)

        layout = QVBoxLayout()

        layout.addLayout(self.buttons_ui())
        layout.addWidget(self.graphs_display)
        self.setLayout(layout)
    

    def buttons_ui(self) -> QHBoxLayout:
        """
        Horizontally lays out the buttons which are used to toggle between graphs, and also adds 
        the graphs to the graph display area.
        """
        layout = QHBoxLayout()

        for graph in self.graphs:
            self.graphs_display.add_graph(graph)
            button = GraphDisplayButton(graph.get_title().replace(" ","\n"),
                                        self.graphs_display, graph.get_id(), self)
            layout.addWidget(button)

        return layout
    

    def make_compatible(self,
                        graphs: list[ExpandingGraph]) -> tuple[GraphWrapperClass]:
        """
        Converts graph to a widget so it can be displayed.

        :param graphs: Tuple containing graph objects to be converted.
        """

        compatible_graphs = []

        for i in range(0, len(graphs)):
            compatible_graph = GraphWrapperClass(graphs[i], i+1, self.update_interval)
            compatible_graphs.append(compatible_graph)
        
        return tuple(compatible_graphs)
    

    def closeEvent(self, event):
        """
        Steps to complete before closing.
        """
        self.graphs_display.stop_threads()
        return super().closeEvent(event)