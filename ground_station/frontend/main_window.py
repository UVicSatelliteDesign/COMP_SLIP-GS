import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTextEdit, QPushButton, 
                             QGroupBox, QGridLayout, QStatusBar, QMessageBox)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QPixmap

# Import custom UI components
from graphs_display.graph_display_layout import GraphDisplayLayout
from backend.graph_plot import ExpandingGraph
from backend.Binary_CSV_Handler import DataHandler
from backend.receiver import ReceivedPacket


class BackendWorker(QObject):
    """
    Backend worker that runs in a separate thread to handle satellite data processing.
    """
    # Signals to communicate with main thread
    data_received = pyqtSignal(str)  # Signal when new data is received
    telemetry_updated = pyqtSignal(dict)  # Signal when telemetry data is updated
    image_received = pyqtSignal(str)  # Signal when new image is received
    status_updated = pyqtSignal(str)  # Signal for status updates
    error_occurred = pyqtSignal(str)  # Signal for error messages

    def __init__(self):
        super().__init__()
        self.data_handler = DataHandler()
        self.is_running = False
        self.packet_count = 0

    @pyqtSlot()
    def start_processing(self):
        """Start the backend data processing."""
        self.is_running = True
        self.status_updated.emit("Backend processing started")

    @pyqtSlot()
    def stop_processing(self):
        """Stop the backend data processing."""
        self.is_running = False
        self.status_updated.emit("Backend processing stopped")

    @pyqtSlot(bytes)
    def process_satellite_data(self, packet_data):
        """
        Process incoming satellite data packets.
        
        Args:
            packet_data (bytes): Raw packet data from satellite
        """
        try:
            if not self.is_running:
                return

            # Process packet using the existing receiver
            received_packet = ReceivedPacket(packet_data)
            
            if received_packet.payload_type is not None:
                self.packet_count += 1
                
                # Process through data handler
                self.data_handler.process_packet(packet_data)
                
                # Emit appropriate signals based on packet type
                if received_packet.payload_type == 0b0011:  # Telemetry
                    self.telemetry_updated.emit({
                        'packet_count': self.packet_count,
                        'sequence_number': received_packet.sequence_number,
                        'payload_type': 'Telemetry'
                    })
                elif received_packet.payload_type in [0b0100, 0b0101, 0b0110, 0b0111]:  # Camera
                    self.image_received.emit(f"Camera data received - Seq: {received_packet.sequence_number}")
                
                self.data_received.emit(f"Packet {self.packet_count} processed successfully")
            else:
                self.error_occurred.emit("Invalid packet format received")

        except Exception as e:
            self.error_occurred.emit(f"Error processing packet: {str(e)}")

    @pyqtSlot(str)
    def simulate_data_reception(self, data_type):
        """
        Simulate data reception for testing purposes.
        
        Args:
            data_type (str): Type of data to simulate ('telemetry' or 'camera')
        """
        try:
            if data_type == 'telemetry':
                # Simulate telemetry packet
                test_packet = b"\x00\x00\x00\x10" + b"temp:25.5,alt:1500,lat:49.2827,lon:-123.1207"
                self.process_satellite_data(test_packet)
            elif data_type == 'camera':
                # Simulate camera packet
                test_packet = b"\x00\x00\x00\x11" + b"CAM001\x00\x00" + b"fake_image_data" + b"\x00\x00\x00"
                self.process_satellite_data(test_packet)
        except Exception as e:
            self.error_occurred.emit(f"Simulation error: {str(e)}")


class MainWindow(QMainWindow):
    """
    Main application window for the ground station control software.
    """
    # Signals to communicate with backend thread
    start_backend = pyqtSignal()
    stop_backend = pyqtSignal()
    process_data = pyqtSignal(bytes)
    simulate_data = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.backend_worker = None
        self.backend_thread = None
        self.graphs_layout = None
        
        self.init_ui()
        self.init_backend_thread()
        self.setup_status_timer()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Ground Station Control - Satellite Communication")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create left panel for controls and status
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)  # 1/4 of the width

        # Create right panel for graphs
        right_panel = self.create_graphs_panel()
        main_layout.addWidget(right_panel, 3)  # 3/4 of the width

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ground Station Ready")

    def create_control_panel(self):
        """Create the left control panel with status information and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("Ground Station Control")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Connection Status Group
        conn_group = QGroupBox("Connection Status")
        conn_layout = QGridLayout(conn_group)
        
        self.connection_status = QLabel("🔴 Disconnected")
        self.packets_received = QLabel("Packets: 0")
        self.last_contact = QLabel("Last Contact: Never")
        
        conn_layout.addWidget(QLabel("Status:"), 0, 0)
        conn_layout.addWidget(self.connection_status, 0, 1)
        conn_layout.addWidget(self.packets_received, 1, 0, 1, 2)
        conn_layout.addWidget(self.last_contact, 2, 0, 1, 2)
        
        layout.addWidget(conn_group)

        # Telemetry Status Group
        telem_group = QGroupBox("Telemetry Status")
        telem_layout = QGridLayout(telem_group)
        
        self.telemetry_status = QLabel("No Data")
        self.data_saved_status = QLabel("❌ Not Saved")
        
        telem_layout.addWidget(QLabel("Status:"), 0, 0)
        telem_layout.addWidget(self.telemetry_status, 0, 1)
        telem_layout.addWidget(QLabel("Data Saved:"), 1, 0)
        telem_layout.addWidget(self.data_saved_status, 1, 1)
        
        layout.addWidget(telem_group)

        # Control Buttons Group
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout(control_group)
        
        self.start_btn = QPushButton("Start Backend")
        self.start_btn.clicked.connect(self.start_backend_processing)
        
        self.stop_btn = QPushButton("Stop Backend")
        self.stop_btn.clicked.connect(self.stop_backend_processing)
        self.stop_btn.setEnabled(False)
        
        self.simulate_telem_btn = QPushButton("Simulate Telemetry")
        self.simulate_telem_btn.clicked.connect(lambda: self.simulate_data.emit('telemetry'))
        
        self.simulate_camera_btn = QPushButton("Simulate Camera")
        self.simulate_camera_btn.clicked.connect(lambda: self.simulate_data.emit('camera'))
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.simulate_telem_btn)
        control_layout.addWidget(self.simulate_camera_btn)
        
        layout.addWidget(control_group)

        # Activity Log
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(200)
        self.activity_log.setReadOnly(True)
        log_layout.addWidget(self.activity_log)
        
        layout.addWidget(log_group)

        layout.addStretch()  # Push everything to the top
        return panel

    def create_graphs_panel(self):
        """Create the right panel containing the graph display."""
        try:
            # Create sample graphs (replace with actual data sources)
            graphs = [
                ExpandingGraph("time.csv", "altitude.csv", "Time", "Altitude", "Altitude vs Time"),
                ExpandingGraph("longitude.csv", "latitude.csv", "Longitude", "Latitude", "Latitude vs Longitude"),
                ExpandingGraph("altitude.csv", "pressure.csv", "Altitude", "Pressure", "Pressure vs Altitude"),
                ExpandingGraph("altitude.csv", "temperature.csv", "Altitude", "Temperature", "Temperature vs Altitude"),
                ExpandingGraph("time.csv", "gyro.csv", "Time", "Gyro", "Gyro vs Time")
            ]
            
            # Create the graph display layout
            self.graphs_layout = GraphDisplayLayout(graphs, 1000, 700, 1000)
            return self.graphs_layout
            
        except Exception as e:
            # Fallback if graph creation fails
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"Graph initialization failed: {str(e)}")
            error_layout.addWidget(error_label)
            return error_widget

    def init_backend_thread(self):
        """Initialize the backend worker thread."""
        try:
            # Create backend worker and thread
            self.backend_worker = BackendWorker()
            self.backend_thread = QThread()

            # Move worker to thread
            self.backend_worker.moveToThread(self.backend_thread)

            # Connect signals from main thread to worker slots
            self.start_backend.connect(self.backend_worker.start_processing)
            self.stop_backend.connect(self.backend_worker.stop_processing)
            self.process_data.connect(self.backend_worker.process_satellite_data)
            self.simulate_data.connect(self.backend_worker.simulate_data_reception)

            # Connect worker signals to main thread slots
            self.backend_worker.data_received.connect(self.on_data_received)
            self.backend_worker.telemetry_updated.connect(self.on_telemetry_updated)
            self.backend_worker.image_received.connect(self.on_image_received)
            self.backend_worker.status_updated.connect(self.on_status_updated)
            self.backend_worker.error_occurred.connect(self.on_error_occurred)

            # Connect thread lifecycle
            self.backend_thread.started.connect(self.on_thread_started)
            self.backend_thread.finished.connect(self.on_thread_finished)

        except Exception as e:
            self.log_activity(f"Error initializing backend thread: {str(e)}")

    def setup_status_timer(self):
        """Setup a timer to periodically update status information."""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_display)
        self.status_timer.start(1000)  # Update every second

    # Backend control methods
    def start_backend_processing(self):
        """Start the backend processing thread."""
        try:
            if not self.backend_thread.isRunning():
                self.backend_thread.start()
            
            self.start_backend.emit()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.connection_status.setText("🟢 Connected")
            self.log_activity("Backend processing started")
            
        except Exception as e:
            self.log_activity(f"Error starting backend: {str(e)}")

    def stop_backend_processing(self):
        """Stop the backend processing thread."""
        try:
            self.stop_backend.emit()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.connection_status.setText("🔴 Disconnected")
            self.log_activity("Backend processing stopped")
            
        except Exception as e:
            self.log_activity(f"Error stopping backend: {str(e)}")

    # Slot methods for backend signals
    @pyqtSlot(str)
    def on_data_received(self, message):
        """Handle data received signal from backend."""
        self.log_activity(message)

    @pyqtSlot(dict)
    def on_telemetry_updated(self, telemetry_data):
        """Handle telemetry update signal from backend."""
        self.packets_received.setText(f"Packets: {telemetry_data.get('packet_count', 0)}")
        self.telemetry_status.setText("Data Received")
        self.data_saved_status.setText("✅ Saved")
        self.log_activity(f"Telemetry updated - Seq: {telemetry_data.get('sequence_number', 'N/A')}")

    @pyqtSlot(str)
    def on_image_received(self, message):
        """Handle image received signal from backend."""
        self.log_activity(f"Image: {message}")

    @pyqtSlot(str)
    def on_status_updated(self, status):
        """Handle status update signal from backend."""
        self.status_bar.showMessage(status)
        self.log_activity(f"Status: {status}")

    @pyqtSlot(str)
    def on_error_occurred(self, error_message):
        """Handle error signal from backend."""
        self.log_activity(f"ERROR: {error_message}")
        self.status_bar.showMessage(f"Error: {error_message}")

    @pyqtSlot()
    def on_thread_started(self):
        """Handle thread started signal."""
        self.log_activity("Backend thread started")

    @pyqtSlot()
    def on_thread_finished(self):
        """Handle thread finished signal."""
        self.log_activity("Backend thread finished")

    # Utility methods
    def log_activity(self, message):
        """Add message to activity log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.activity_log.append(formatted_message)
        
        # Keep log size reasonable
        if self.activity_log.document().blockCount() > 100:
            cursor = self.activity_log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()

    def update_status_display(self):
        """Update status display periodically."""
        from datetime import datetime
        # Update last contact time if backend is running
        if self.backend_thread and self.backend_thread.isRunning() and self.backend_worker.is_running:
            self.last_contact.setText(f"Last Contact: {datetime.now().strftime('%H:%M:%S')}")

    # Cleanup and shutdown methods
    def cleanup_backend(self):
        """Clean up backend thread and worker."""
        try:
            if self.backend_worker:
                self.stop_backend.emit()
            
            if self.backend_thread and self.backend_thread.isRunning():
                self.backend_thread.quit()
                if not self.backend_thread.wait(3000):  # Wait 3 seconds
                    self.backend_thread.terminate()
                    self.backend_thread.wait()
            
            self.log_activity("Backend cleanup completed")
            
        except Exception as e:
            print(f"Error during backend cleanup: {str(e)}")

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                'Confirm Exit', 
                'Are you sure you want to exit the Ground Station?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.log_activity("Shutting down Ground Station...")
                
                # Cleanup graphs
                if self.graphs_layout:
                    self.graphs_layout.close()
                
                # Cleanup backend
                self.cleanup_backend()
                
                # Stop status timer
                if hasattr(self, 'status_timer'):
                    self.status_timer.stop()
                
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            print(f"Error during shutdown: {str(e)}")
            event.accept()  # Force close on error


def main():
    """Main application entry point."""
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Ground Station Control")
        app.setApplicationVersion("1.0")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Critical error starting application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()