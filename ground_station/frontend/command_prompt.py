# command_prompt.py

#imports first
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QLabel 
from .utils import is_valid_command, get_binary_from_dict, add_to_queue, show_acknowledgment

class CommandPrompt(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Command Input')
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.label = QLabel('Select a command:', self)
        layout.addWidget(self.label)

        # Command selection dropdown
        self.command_dropdown = QComboBox(self)
        self.command_dropdown.addItems([
            "ping", "nominal", "low power", "telemetry",
            "Camera-1-End", "Camera-2-End", "Req Retransmission"
        ])
        layout.addWidget(self.command_dropdown)

        self.submit_button = QPushButton('Submit', self)
        self.submit_button.clicked.connect(self.process_command)
        layout.addWidget(self.submit_button)

        self.result_label = QLabel('', self)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def process_command(self):
        # Get the selected command
        command = self.command_dropdown.currentText().strip()

        if is_valid_command(command):
            # Convert and enqueue
            bits = get_binary_from_dict(command)
            add_to_queue(bits)
            show_acknowledgment()
            self.result_label.setText("Command processed and moved to queue.")
        else:
            self.result_label.setText("Invalid command.")
