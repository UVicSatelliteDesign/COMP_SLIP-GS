import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import QThread, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt

# Import all UI components
from ground_station.frontend.command_prompt import CommandPrompt
from ground_station.frontend.graphs_display.graph_display_layout import GraphDisplayLayout
from ground_station.frontend.data_api import DataAPI, ImageAPI
from ground_station.backend.graph_plot import ExpandingGraph, create_example_graphs
from ground_station.backend.Binary_CSV_Handler import DataHandler, DATA_SAVED, TELEMETRY_SAVED
from main import BackendWorkerMain


class GroundStationMainWindow(QMainWindow):
    """Main application window for Ground Station"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setWindowTitle("Ground Station - Satellite Communication System")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Initialize APIs
        self.data_api = DataAPI(Path("telemetry/telemetry.csv"))
        self.image_api = ImageAPI(Path("images"))
        
        # Initialize backend worker and thread
        self.backend_thread = QThread()
        self.backend_worker = BackendWorkerMain()
        self.backend_worker.moveToThread(self.backend_thread)
        
        # Setup backend connections
        self.setup_backend_connections()
        
        # Create expanding graphs (13 graphs as requested)
        self.expanding_graphs = self.create_expanding_graphs()
        
        # Initialize UI components
        self.init_ui()
        
        # Setup auto-update timers
        self.setup_timers()
        
        # Start backend thread
        self.backend_thread.started.connect(self.backend_worker.run)
        self.backend_thread.start()
        
    def create_expanding_graphs(self):
        """Create 13 expanding graphs for different telemetry data"""
        graphs = []
        
        # Define graph configuration
        graph_configs = [
            ("Field_0", "Field_1", "Time", "Temperature", "Temperature vs Time"),
            ("Field_0", "Field_2", "Time", "Pressure", "Pressure vs Time"),
            ("Field_0", "Field_3", "Time", "Altitude", "Altitude vs Time"),
            ("Field_0", "Field_4", "Time", "Gyroscope X", "Gyroscope X vs Time"),
            ("Field_0", "Field_5", "Time", "Gyroscope Y", "Gyroscope Y vs Time"),
            ("Field_0", "Field_6", "Time", "Gyroscope Z", "Gyroscope Z vs Time"),
            ("Field_0", "Field_7", "Time", "Accelerometer X", "Accelerometer X vs Time"),
            ("Field_0", "Field_8", "Time", "Accelerometer Y", "Accelerometer Y vs Time"),
            ("Field_0", "Field_9", "Time", "Accelerometer Z", "Accelerometer Z vs Time"),
            ("Field_0", "Field_10", "Time", "Battery Voltage", "Battery Voltage vs Time"),
            ("Field_0", "Field_11", "Time", "Solar Panel Current", "Solar Panel Current vs Time"),
            ("Field_1", "Field_2", "Temperature", "Pressure", "Pressure vs Temperature"),
            ("Field_3", "Field_10", "Altitude", "Battery Voltage", "Battery vs Altitude")
        ]
        
        # Create graphs
        for x_field, y_field, x_label, y_label, title in graph_configs:
            graph = ExpandingGraph(x_field, y_field, x_label, y_label, title)
            graphs.append(graph)
            
        return graphs
    
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left panel - Image display
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel)
        
        # Right panel - Command prompt and graphs
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel)
        
        central_widget.setLayout(main_layout)
        
    def create_left_panel(self):
        """Create the left panel with image display and telemetry data"""
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.Shape.Box)
        left_frame.setFixedWidth(600)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Latest Satellite Image")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid gray; background-color: lightgray;")
        self.image_label.setFixedSize(580, 400)
        self.image_label.setText("No image available")
        layout.addWidget(self.image_label)
        
        # Telemetry data table
        telemetry_frame = self.create_telemetry_display()
        layout.addWidget(telemetry_frame)
        
        left_frame.setLayout(layout)
        return left_frame
    
    def create_telemetry_display(self):
        """Create telemetry data display with 13 placeholders"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Real-time Telemetry Data")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Scroll area for telemetry data
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Create 13 data placeholders
        self.telemetry_labels = {}
        telemetry_fields = [
            "GPS", "Temperature", "Pressure", "Altitude", "Gyroscope X",
            "Gyroscope Y", "Gyroscope Z", "Accelerometer X", "Accelerometer Y",
            "Accelerometer Z", "Battery Voltage", "Solar Panel Current", "Signal Strength"
        ]
        
        for i, field in enumerate(telemetry_fields):
            data_layout = QHBoxLayout()
            
            name_label = QLabel(f"{field}:")
            name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            name_label.setFixedWidth(150)
            
            value_label = QLabel("-- N/A --")
            value_label.setStyleSheet("color: blue; font-weight: bold;")
            
            data_layout.addWidget(name_label)
            data_layout.addWidget(value_label)
            data_layout.addStretch()
            
            scroll_layout.addLayout(data_layout)
            self.telemetry_labels[f"Field_{i}"] = value_label
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        frame.setLayout(layout)
        
        return frame
    
    def create_right_panel(self):
        """Create the right panel with command prompt and graphs"""
        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.Shape.Box)
        
        layout = QVBoxLayout()
        
        # Command prompt at the top
        command_frame = QFrame()
        command_frame.setFrameStyle(QFrame.Shape.Box)
        command_frame.setFixedHeight(150)
        
        command_layout = QVBoxLayout()
        command_title = QLabel("Command Control")
        command_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        command_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        command_layout.addWidget(command_title)
        
        self.command_prompt = CommandPrompt()
        command_layout.addWidget(self.command_prompt)
        command_frame.setLayout(command_layout)
        
        layout.addWidget(command_frame)
        
        # Graph display area
        graph_frame = QFrame()
        graph_frame.setFrameStyle(QFrame.Shape.Box)
        
        graph_layout = QVBoxLayout()
        graph_title = QLabel("Telemetry Graphs")
        graph_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        graph_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        graph_layout.addWidget(graph_title)
        
        # Create graph display with all expanding graphs
        self.graph_display = GraphDisplayLayout(
            self.expanding_graphs,
            w=900,
            h=600,
            update_interval=1000
        )
        graph_layout.addWidget(self.graph_display)
        graph_frame.setLayout(graph_layout)
        
        layout.addWidget(graph_frame)
        right_frame.setLayout(layout)
        
        return right_frame
    
    def setup_backend_connections(self):
        """Setup connections between backend signals and GUI slots"""
        # Connect backend worker signals directly to UI methods
        self.backend_worker.error_occured.connect(self.show_error)
        self.backend_worker.packet_recieved.connect(self.update_packet)
        self.backend_worker.rec_telemetry_data.connect(self.update_telemetry)
        self.backend_worker.rec_camera_data.connect(self.update_image)
        self.backend_worker.ping_ack_ok.connect(self.on_ping_ack_received)
    
    def setup_timers(self):
        """Setup timers for auto-updating UI components"""
        # Timer for updating image display
        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self.update_image_display)
        self.image_timer.start(30000)  # Update every 30 seconds
        
        # Timer for updating telemetry display
        self.telemetry_timer = QTimer()
        self.telemetry_timer.timeout.connect(self.update_telemetry_display)
        self.telemetry_timer.start(5000)  # Update every 5 seconds
    
    def update_image_display(self):
        """Update the image display with the latest image"""
        try:
            latest_image_path = self.image_api.get_latest_image_path()
            if latest_image_path and os.path.exists(latest_image_path):
                pixmap = QPixmap(str(latest_image_path))
                if not pixmap.isNull():
                    # Scale the image to fit the label
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                else:
                    self.image_label.setText("Error loading image")
            else:
                self.image_label.setText("No image available")
        except Exception as e:
            print(f"Error updating image display: {e}")
            self.image_label.setText("Error loading image")
    
    def update_telemetry_display(self):
        """Update the telemetry display with latest data"""
        try:
            latest_row = self.data_api.get_latest_row_tuple()
            if latest_row:
                # Update each field with the latest data
                for i, value in enumerate(latest_row):
                    field_key = f"Field_{i}"
                    if field_key in self.telemetry_labels:
                        self.telemetry_labels[field_key].setText(str(value))
                        self.telemetry_labels[field_key].setStyleSheet("color: green; font-weight: bold;")
            else:
                # Set all fields to N/A if no data
                for label in self.telemetry_labels.values():
                    label.setText("-- N/A --")
                    label.setStyleSheet("color: blue; font-weight: bold;")
        except Exception as e:
            print(f"Error updating telemetry display: {e}")
    
    # Backend signal handlers
    def show_error(self, error_message):
        """Handle error occurred signal"""
        print(f"Backend error: {error_message}")
        # You can add error display UI here (status bar, message box, etc.)
    
    def update_packet(self, packet_info, packet_data):
        """Handle packet received signal"""
        print(f"Packet received: {packet_info}")
        # Force update of displays when packet is processed
        self.update_telemetry_display()
    
    def update_telemetry(self, telemetry_info, telemetry_data):
        """Handle telemetry data received signal"""
        print(f"Telemetry data received: {telemetry_info}")
        # Force immediate update of telemetry display
        self.update_telemetry_display()
    
    def update_image(self, image_info, image_data):
        """Handle camera data received signal"""
        print(f"Camera data received: {image_info}")
        # Force immediate update of image display
        self.update_image_display()
    
    def on_ping_ack_received(self, message):
        """Handle ping acknowledgment received"""
        print(f"Ping ACK received: {message}")
        # You can update UI status indicators here
    
    def closeEvent(self, event):
        """Handle application close event gracefully"""
        print("Closing Ground Station application...")
        
        # Stop backend worker
        self.backend_worker.stop()
        
        # Stop and wait for backend thread
        self.backend_thread.quit()
        self.backend_thread.wait()
        
        # Stop timers
        self.image_timer.stop()
        self.telemetry_timer.stop()
        
        # Close graph display properly
        self.graph_display.close()
        
        print("Application closed successfully")
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Ground Station")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = GroundStationMainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()