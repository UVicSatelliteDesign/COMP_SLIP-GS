import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from backend.receiver import ReceivedPacket
from backend.Binary_CSV_Handler import DataHandler


class BackendWorker(QObject):
    data_received = pyqtSignal(str)
    telemetry_updated = pyqtSignal(dict)
    image_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.data_handler = DataHandler()
        self.is_running = False
        self.packet_count = 0

    @pyqtSlot()
    def start_processing(self):
        self.is_running = True

    @pyqtSlot()
    def stop_processing(self):
        self.is_running = False

    @pyqtSlot(bytes)
    def process_satellite_data(self, packet_data):
        if not self.is_running:
            return

        try:
            received_packet = ReceivedPacket(packet_data)
            if received_packet.payload_type is not None:
                self.packet_count += 1
                self.data_handler.process_packet(packet_data)

                if received_packet.payload_type == 0b0011:
                    self.telemetry_updated.emit({
                        'packet_count': self.packet_count,
                        'sequence_number': received_packet.sequence_number,
                        'payload_type': 'Telemetry'
                    })
                elif received_packet.payload_type in [0b0100, 0b0101, 0b0110, 0b0111]:
                    self.image_received.emit(f"Camera data received - Seq: {received_packet.sequence_number}")

                self.data_received.emit(f"Packet {self.packet_count} processed successfully")
            else:
                self.error_occurred.emit("Invalid packet format")
        except Exception as e:
            self.error_occurred.emit(f"Error processing packet: {str(e)}")

    @pyqtSlot(str)
    def simulate_data_reception(self, data_type):
        try:
            if data_type == 'telemetry':
                test_packet = b"\x00\x00\x00\x10" + b"temp:25.5,alt:1500,lat:49.2827,lon:-123.1207"
                self.process_satellite_data(test_packet)
            elif data_type == 'camera':
                test_packet = b"\x00\x00\x00\x11" + b"CAM001\x00\x00" + b"fake_image_data" + b"\x00\x00\x00"
                self.process_satellite_data(test_packet)
        except Exception as e:
            self.error_occurred.emit(f"Simulation error: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ground Station")
        self.setGeometry(100, 100, 800, 600)

        self.backend_worker = BackendWorker()
        self.backend_thread = QThread()
        self.backend_worker.moveToThread(self.backend_thread)

        self.backend_thread.started.connect(self.backend_worker.start_processing)
        self.backend_thread.finished.connect(self.backend_worker.stop_processing)

        self.backend_worker.data_received.connect(self.log)
        self.backend_worker.telemetry_updated.connect(self.display_telemetry)
        self.backend_worker.image_received.connect(self.display_image)
        self.backend_worker.error_occurred.connect(self.log)

        self.backend_thread.start()

        # UI setup
        main_layout = QHBoxLayout()
        left_panel = QVBoxLayout()

        # Status
        status_label = QLabel("Status")
        self.status_value = QLabel("🔴 Not Running")
        left_panel.addWidget(status_label)
        left_panel.addWidget(self.status_value)

        # Telemetry Data
        telemetry_label = QLabel("Telemetry Data")
        left_panel.addWidget(telemetry_label)
        self.telemetry_fields = []
        for i in range(5):
            data_row = QHBoxLayout()
            label = QLabel(f"data_{i}")
            data_button = QPushButton("Placeholder")
            data_row.addWidget(label)
            data_row.addWidget(data_button)
            left_panel.addLayout(data_row)
            self.telemetry_fields.append(label)

        # Image Placeholder
        image_label = QLabel("Most Recent Image")
        left_panel.addWidget(image_label)
        self.image_placeholder = QLabel("No Image Received")
        left_panel.addWidget(self.image_placeholder)

        main_layout.addLayout(left_panel)

        # Right panel
        right_panel = QVBoxLayout()
        command_label = QLabel("Commands")
        right_panel.addWidget(command_label)

        self.command_dropdown = QComboBox()
        self.command_dropdown.addItems(["Simulate Telemetry", "Simulate Camera"])
        right_panel.addWidget(self.command_dropdown)

        command_button = QPushButton("Send Command")
        command_button.clicked.connect(self.send_command)
        right_panel.addWidget(command_button)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        right_panel.addWidget(self.console)

        main_layout.addLayout(right_panel)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def send_command(self):
        selected = self.command_dropdown.currentText()
        if "Telemetry" in selected:
            self.backend_worker.simulate_data_reception("telemetry")
        elif "Camera" in selected:
            self.backend_worker.simulate_data_reception("camera")

    def log(self, message):
        self.console.append(f"> {message}")

    def display_telemetry(self, data):
        self.status_value.setText("🟢 Running")
        self.telemetry_fields[0].setText(f"Packets: {data.get('packet_count', 'N/A')}")
        self.telemetry_fields[1].setText(f"Seq: {data.get('sequence_number', 'N/A')}")
        self.telemetry_fields[2].setText(f"Type: {data.get('payload_type', 'N/A')}")
        self.log("Telemetry data received.")

    def display_image(self, msg):
        self.image_placeholder.setText(msg)
        self.log("Image data received.")

    def closeEvent(self, event):
        self.backend_worker.stop_processing()
        self.backend_thread.quit()
        self.backend_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
