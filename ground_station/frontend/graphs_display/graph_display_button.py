from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout

from graph_display_area import GraphDisplayArea


class GraphDisplayButton(QWidget):
    def __init__(self,
                 text: str,
                 graph_disp_object: GraphDisplayArea,
                 id: int,
                 parent: QWidget | None = None):
        """
        Button that toggles visibility of graph.

        :param text: Text on button.
        :param graph_disp_object: Object containing and displaying the graphs.
        :param id: ID of graph button is linked to.
        :param parent: Parent widget (optional).
        """
        super().__init__(parent)

        self.graph_disp_object = graph_disp_object
        self.id = id

        layout = QHBoxLayout()
        
        self.button = QPushButton(text, self)
        self.button.clicked.connect(self.on_click)

        layout.addWidget(self.button)
        self.setLayout(layout)
               
    
    
    def on_click(self):
        """
        On click function to execute events when button is pressed.
        """
        self.graph_disp_object.change_active_graph(self.id)