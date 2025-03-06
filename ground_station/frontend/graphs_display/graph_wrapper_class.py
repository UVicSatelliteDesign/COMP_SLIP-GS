from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class GraphWrapperClass(QWidget):
    def __init__(self, 
                 graph,
                 id: int,
                 parent: QWidget | None = None):
        """
        Wrapper class to wrap graph as a QWidget so that it can be displayed.
        """
        super().__init__(parent)

        self.id = id
        self.placeholder()  # Placeholder display till class plotting graphs is defined
        #TODO: Implement once class plotting graphs is defined


    def update_graph(self):
        """
        Updates values on graph
        """
        #TODO: Implement once class plotting graphs is defined
        print("update_graph() function called") #Placeholder till  class plotting graphs is defined


    def get_title(self):
        """
        Returns title of graph
        """
        #TODO: Implement once class plotting graphs is defined
        return f"Graph {self.id}"
    

    def get_id(self):
        """
        Returns ID of graph.
        """
        return self.id
    

    def placeholder(self):
        """
        Placeholder display till class plotting graphs is defined
        """
        layout = QVBoxLayout()

        label = QLabel(f"Graph {self.id}", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: black")

        layout.addWidget(label)
        self.setLayout(layout)

        self.setStyleSheet("background-color: white")