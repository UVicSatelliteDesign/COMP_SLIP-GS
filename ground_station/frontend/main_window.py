import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
)
#from PyQt5.QtGui import QPixmap

#import graph class
#import backend

class MainWindow(QMainWindow):
    def __init__(self):
            super().__init__()

            self.setWindowTitle("Ground Station")
            self.setGeometry(100, 100, 800, 600) #x,y,width,height

            #self.receive = Backend()
            #self.send = Backend()

            # Main layout
            main_layout = QHBoxLayout()

            # Left Panel
            left_panel = QVBoxLayout()

            # Status Section
            status_label = QLabel("Status")
            status_value = QLabel("recieve power level")
            left_panel.addWidget(status_label)
            left_panel.addWidget(status_value)

            # Data Section
            data_label = QLabel("Data")
            left_panel.addWidget(data_label)

            #for data_name, data_value in self.receive.data():
            for x in range(5):
                data_row = QHBoxLayout()
                data_name=QLabel("data_name") #(QLabel(data_name))
                data_row.addWidget(data_name)
                data_row.addWidget(QPushButton("Data Ex"))
                left_panel.addLayout(data_row)

            # Most Recent Image Section
            image_label = QLabel("Most Recent Image")
            left_panel.addWidget(image_label)

            # Placeholder for image (replace with actual image handling)
            image_placeholder = QLabel("Image placeholder (replace with actual image)")
            left_panel.addWidget(image_placeholder)

            # Add left panel to main layout
            main_layout.addLayout(left_panel)

            # Right Panel
            right_panel = QVBoxLayout()

            # Tabs Section (Placeholder)
            tabs_label = QLabel("Tabs Section (Placeholder)")
            right_panel.addWidget(tabs_label)

            # Command Section
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

            # Console for acknowledgements
            self.console = QTextEdit()
            self.console.setReadOnly(True)
            right_panel.addWidget(self.console)

            # Add right panel to main layout
            main_layout.addLayout(right_panel)

            # Set main layout
            central_widget = QWidget()
            central_widget.setLayout(main_layout)
            self.setCentralWidget(central_widget)

    def send_command(self, cmd):
            # Placeholder for sending a command and displaying acknowledgment
            ack = self.send.command(cmd)
            self.console.append(ack)


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())    