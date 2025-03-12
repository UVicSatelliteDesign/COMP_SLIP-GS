from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from utils import is_valid_command, string_to_bits, add_to_buffer, show_acknowledgment

class CommandPrompt(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Command Input')
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.label = QLabel('Enter a command:', self)
        layout.addWidget(self.label)

        self.command_input = QLineEdit(self)
        layout.addWidget(self.command_input)

        self.submit_button = QPushButton('Submit', self)
        self.submit_button.clicked.connect(self.process_command)
        layout.addWidget(self.submit_button)

        self.result_label = QLabel('', self)
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def process_command(self):
        command = self.command_input.text().strip()

        if is_valid_command(command):
            # Convert the string to bits and add to buffer
            bits = string_to_bits(command)
            add_to_buffer(bits)
            show_acknowledgment()
            self.result_label.setText("Command processed and moved to buffer.")
        else:
            self.result_label.setText("Invalid command.")
