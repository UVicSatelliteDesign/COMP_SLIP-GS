import sys

sys.path
sys.executable
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
    QSizePolicy,
)

#import graph class
#import backend

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ground Station")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QHBoxLayout()

        # Left Panel
        left_panel = QVBoxLayout()

        # Group status and data closely in a sub-layout
        top_info_layout = QVBoxLayout()

        # Status
        status_label = QLabel("Status")
        status_value = QLabel("receive power level")
        top_info_layout.addWidget(status_label)
        top_info_layout.addWidget(status_value)

        # Data Section
        data_label = QLabel("Data")
        top_info_layout.addWidget(data_label)

        for _ in range(5):
            data_row = QHBoxLayout()
            data_name = QLabel("data_name")
            data_button = QPushButton("Data Ex")
            data_row.addWidget(data_name)
            data_row.addWidget(data_button)
            top_info_layout.addLayout(data_row)

        left_panel.addLayout(top_info_layout)

        # Add stretch to give more space to image section
        #left_panel.addStretch()

        # Image Section
        image_label = QLabel("Most Recent Image")
        left_panel.addWidget(image_label)

        image_placeholder = QLabel("Image placeholder (replace with actual image)")
        image_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        image_placeholder.setStyleSheet("border: 1px solid gray;")  # visual border
        left_panel.addWidget(image_placeholder)

        # Right Panel
        right_panel = QVBoxLayout()
        tabs_label = QLabel("Tabs Section (Placeholder)")
        right_panel.addWidget(tabs_label)

        command_label = QLabel("Commands")
        right_panel.addWidget(command_label)

        command_dropdown = QComboBox()
        command_dropdown.addItems(["Command 1", "Command 2", "Command 3"])
        right_panel.addWidget(command_dropdown)

        command_button = QPushButton("Send Command")
        command_button.clicked.connect(
            lambda: self.send_command(command_dropdown.currentText())
        )
        right_panel.addWidget(command_button)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        right_panel.addWidget(self.console)

        # Assemble Layouts
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=2)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def send_command(self, cmd):
        ack = f"Acknowledged: {cmd}"  # Temporary mock response
        self.console.append(ack)


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())    