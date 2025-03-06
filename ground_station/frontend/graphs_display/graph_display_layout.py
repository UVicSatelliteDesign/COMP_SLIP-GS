from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication

from graph_display_button import GraphDisplayButton
from graph_display_area import GraphDisplayArea
from graph_wrapper_class import GraphWrapperClass


class GraphDisplayLayout(QWidget):
    def __init__(self,
                 graphs: tuple,
                 w: int,
                 h: int,
                 frame_rate: int = 30,
                 parent: QWidget | None = None):
        """
        Graph display layout consisting of buttons to toggle between different graphs, and a 
        common graph display area which switches the graph displayed depending on which button is 
        pressed.
        
        :param graphs: Tuple containing graph objects.
        :param w: Width of graph area.
        :param h: Height of graph area.
        :param frame_rate: Frame rate of updating graphs (optional). Default is 30 FPS
        :param parent: Parent of graph display layout (optional).
        """
        super().__init__(parent)

        self.graphs = self.make_compatible(graphs)
        self.graphs_display = GraphDisplayArea(w, h, frame_rate)

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
            button = GraphDisplayButton(graph.get_title(),
                                        self.graphs_display, graph.get_id(), self)
            layout.addWidget(button)

        return layout
    

    def make_compatible(self,
                        graphs: tuple) -> tuple[GraphWrapperClass]:
        """
        Converts graph to a widget so it can be displayed.

        :param graphs: Tuple containing graph objects to be converted.
        """

        compatible_graphs = []

        for i in range(0, len(graphs)):
            compatible_graph = GraphWrapperClass(graphs[i], i+1)
            compatible_graphs.append(compatible_graph)
        
        return tuple(compatible_graphs)