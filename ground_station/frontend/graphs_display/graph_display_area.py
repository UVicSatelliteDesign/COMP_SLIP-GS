from PyQt6.QtWidgets import QWidget, QStackedLayout, QLabel
from PyQt6.QtCore import Qt
from concurrent.futures import ThreadPoolExecutor

from graph_wrapper_class import GraphWrapperClass


class GraphDisplayArea(QWidget):
    def __init__(self,
                 w: int,
                 h: int,
                 parent: QWidget | None = None):
        """
        Display area for graphs.

        :param w: Width of display area.
        :param h: Height of display area.
        :param parent: Parent of graph display area (optional). Default is `None`.
        """
        super().__init__(parent)

        self.setFixedSize(w,h)

        self.current_graph_id = 0  # ID of graph being displayed
        self.graphs = []    # To store all graphs displayed
        self.background_threads = ThreadPoolExecutor()

        self.stackedLayout = QStackedLayout()

        default = DefaultDisplay()
        self.stackedLayout.addWidget(default)

        self.setLayout(self.stackedLayout)
        

    def change_active_graph(self,
                            id: int):
        """
        Changes the active graph to the one which has the same ID as given in the parameter.

        :param id: ID of graph that is to be displayed.
        """
        self.current_graph_id = id
        self.stackedLayout.setCurrentIndex(id)
    

    def start_thread(self,
                     graph: GraphWrapperClass):
        """
        Starts a thread which continuously updates the graph in the parameter.

        :param graph: Graph to be continuously updated.
        """
        try:
            self.background_threads.submit(self.auto_update, graph)
        except Exception as e:
            print(f"Unexpected exception {e} occured.")
    

    def stop_threads(self):
        """
        Stops the threads running in the background which are parallelly updating graphs. 
        """
        try:
            self.background_threads.shutdown(wait = True)   # Wait for all threads to finish
            self.background_threads = ThreadPoolExecutor()  # Reset background_threads for reuse
        except Exception as e:
            print(f"Unexpected exception {e} occured.")


    def add_graph(self,
                  graph: GraphWrapperClass):
        """
        Adds graphs to the stack layout of the display area.

        :param graph: Graph to be added.
        """
        self.graphs.append(graph)
        self.stackedLayout.addWidget(graph)
        self.start_thread(graph)
    

    def auto_update(self,
                    graph: GraphWrapperClass):
        """
        Keeps updating the graph in the background.

        :param graph: Graph which are to be continuously updated.
        """
        graph.auto_update_graph()


class DefaultDisplay(QWidget):
    def __init__(self):
        """
        Default display when no graph is selected.
        """
        super().__init__()

        layout = QStackedLayout()

        label = QLabel("NO GRAPH SELECTED", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: black")

        layout.addWidget(label)
        self.setLayout(layout)

        self.setStyleSheet("background-color: white")