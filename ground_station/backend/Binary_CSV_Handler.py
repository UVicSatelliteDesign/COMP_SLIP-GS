import os
import csv
import struct
from collections import namedtuple

# ==============================================
# GLOBAL VARIABLES
# ==============================================
DATA_SAVED = False       # Tracks whether camera data was successfully saved
TELEMETRY_SAVED = False  # Tracks whether telemetry data was successfully saved

# ==============================================
# TELEMETRY DATA STRUCTURES
# ==============================================
BatteryData = namedtuple('BatteryData', [
    'voltage', 
    'current', 
    'state_of_charge', 
    'power_usage', 
    'estimated_life'
])

SensorsData = namedtuple('SensorsData', [
    'temperature_obc',
    'temperature_ttc',
    'temperature_bms',
    'gyroscope_axis_1',
    'gyroscope_axis_2',
    'gyroscope_axis_3',
    'acceleration_x',
    'acceleration_y',
    'acceleration_z',
    'altitude'
])

# ==============================================
# HELPER FUNCTIONS
# ==============================================
def unpack_floats(data, count, pos):
    """Unpacks multiple big-endian floats from binary data"""
    fmt = f'>{count}f'  # big-endian floats
    values = struct.unpack_from(fmt, data, pos)
    return values, pos + count*4

# ==============================================
# MAIN DATA HANDLER CLASS
# ==============================================
class DataHandler:
    """Main class for handling satellite data packets including both camera images and telemetry data"""
    
    # Class-level variable shared across all instances
    sequence_number = 0  # Tracks the sequence number of packets for ordering

    def __init__(self, data_type, payload_type=None, image_dir="images", telemetry_dir="telemetry"):
        """
        Initialize the data handler with storage directories
        
        Args:
            data_type (str): Type of data this handler is responsible for ("camera" or "telemetry")
            payload_type (int, optional): Specific payload type identifier (if applicable)
            image_dir (str): Directory to store camera images
            telemetry_dir (str): Directory to store telemetry CSV files
        """
        # Initialize instance variables
        self.image_dir = image_dir         # Directory for image storage
        self.telemetry_dir = telemetry_dir  # Directory for telemetry data
        self.recent_files = {}             # Dictionary to track most recent files by identifier
        self.global_headers = []           # List to store CSV column headers for telemetry data
        
        # Create directories if they don't exist, with error handling
        try:
            os.makedirs(self.image_dir, exist_ok=True)
            os.makedirs(self.telemetry_dir, exist_ok=True)
        except OSError as e:
            print(f"Directory creation failed: {e}")
            raise

    def process_packet(self, packet):
        """
        Main packet processing router that validates and directs packets to appropriate handlers
        
        Args:
            packet (bytes): Raw binary packet data received from satellite
        """
        try:
            # Development-time validation checks
            assert isinstance(packet, bytes), "Packet must be in bytes format"
            assert len(packet) >= 5, "Packet must contain at least 5 bytes (1 byte type + 4 byte header)"
            
            # Extract payload type from first byte
            payload_type = packet[0]  # 1 byte payload type identifier
            payload = packet[1:]       # Actual payload data

            # Route to appropriate handler based on payload type
            if payload_type == 0x10:  # Telemetry packet identifier
                self.handle_telemetry_data(payload)
            elif payload_type in [0x11, 0x12]:  # Camera packet identifiers
                self.handle_camera_data(payload)
            else:
                print(f"Unknown payload type: {payload_type}")

        except AssertionError as e:
            print(f"Invalid packet format: {e}")
        except Exception as e:
            print(f"Packet processing failed: {e}")

    def handle_camera_data(self, payload):
        """
        Processes camera data payload including image data and offset information
        
        Args:
            payload (bytes): Camera-specific payload data
        """
        global DATA_SAVED
        
        try:
            # Validate payload meets minimum size requirements (1B ID + 122B data + 2B seq + 3B offset)
            assert len(payload) >= 128, f"Camera payload requires at least 128 bytes, got {len(payload)}"
            
            # Parse the payload into its components
            seq_num, offset, image_data = self.parse_camera_payload(payload)
            
            # Generate filename using identifier and sequence number
            file_path = os.path.join(
                self.image_dir, 
                f"camera_{seq_num}.bin"  # Using .bin format
            )

            # Write image data to file with error handling
            try:
                # 'wb' mode if offset=0 (new file), 'ab' if offset>0 (append to existing)
                with open(file_path, "wb" if offset == 0 else "ab") as f:
                    f.write(image_data)
            except IOError as e:
                print(f"Failed to write image: {e}")
                return

            # Update tracking information
            self.recent_files[seq_num] = file_path
            DATA_SAVED = True
            # Update class sequence number to last received + 1
            DataHandler.sequence_number = (seq_num + 1) & 0xFFFF  # Ensure 16-bit wrap-around

        except AssertionError as e:
            print(f"Invalid camera data: {e}")
        except Exception as e:
            print(f"Camera processing error: {e}")

    def handle_telemetry_data(self, payload):
        """
        Processes telemetry data payload and stores it in CSV format
        
        Args:
            payload (bytes): Telemetry-specific payload data
        """
        global TELEMETRY_SAVED
        
        try:
            # Validate payload contains data
            assert len(payload) >= 101, "Telemetry payload must be at least 101 bytes"
            
            # Parse the raw payload into a list of values
            values = self.parse_telemetry_payload(payload)
            if not values:
                return

            # Set up CSV file path
            csv_file = os.path.join(self.telemetry_dir, "telemetry.csv")

            # Initialize headers on first packet if needed
            if not self.global_headers:
                self.global_headers = [
                    # Battery 1
                    'bat1_voltage', 'bat1_current', 'bat1_soc', 'bat1_power', 'bat1_life',
                    # Battery 2
                    'bat2_voltage', 'bat2_current', 'bat2_soc', 'bat2_power', 'bat2_life',
                    # Battery 3
                    'bat3_voltage', 'bat3_current', 'bat3_soc', 'bat3_power', 'bat3_life',
                    # Sensors
                    'temp_obc', 'temp_ttc', 'temp_bms',
                    'gyro_x', 'gyro_y', 'gyro_z',
                    'accel_x', 'accel_y', 'accel_z',
                    'altitude',
                    # GPS
                    'gps'
                ]

            # Write to CSV file with error handling
            try:
                with open(csv_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    
                    if os.stat(csv_file).st_size == 0:
                        writer.writerow(self.global_headers)
                    
                    writer.writerow(values)
            except IOError as e:
                print(f"Failed to write telemetry: {e}")
                return

            TELEMETRY_SAVED = True

        except AssertionError as e:
            print(f"Invalid telemetry: {e}")
        except Exception as e:
            print(f"Telemetry processing error: {e}")

    def parse_camera_payload(self, payload):
        """
        Decodes camera payload into its components (updated as per team lead's request)
        
        Args:
            payload (bytes): Raw camera payload data
            
        Returns:
            tuple: (sequence_number, offset, image_data)
        """
        try:
            image_data = payload[1:123]                         # 122 bytes of image data
            seq_num = int.from_bytes(payload[123:125], 'big')  # 2-byte sequence number
            offset = int.from_bytes(payload[125:128], 'big')   # 3-byte offset
            return seq_num, offset, image_data
            
        except Exception as e:
            print(f"Camera payload parsing failed: {e}")
            raise

    def decode_telemetry(self, payload):
        """
        Decodes binary telemetry data into structured format
        
        Args:
            payload (bytes): Raw telemetry data including all subsystems
            
        Returns:
            tuple: (battery1, battery2, battery3, sensors, gps)
        """
        try:
            # Verify payload length (3 batteries * 5 floats * 4 bytes + 
            # sensors 10 floats * 4 bytes + GPS 11 bytes = 101 bytes)
            expected_length = 101
            if len(payload) != expected_length:
                raise ValueError(f"Expected {expected_length} bytes, got {len(payload)}")

            offset = 0
            
            # Decode Battery 1 (5 floats)
            bat1_vals, offset = unpack_floats(payload, 5, offset)
            battery1 = BatteryData(*bat1_vals)
            
            # Decode Battery 2 (5 floats)
            bat2_vals, offset = unpack_floats(payload, 5, offset)
            battery2 = BatteryData(*bat2_vals)
            
            # Decode Battery 3 (5 floats)
            bat3_vals, offset = unpack_floats(payload, 5, offset)
            battery3 = BatteryData(*bat3_vals)
            
            # Decode Sensors (10 floats)
            sensors_vals, offset = unpack_floats(payload, 10, offset)
            sensors = SensorsData(*sensors_vals)
            
            # Decode GPS (11 bytes ASCII)
            gps = payload[offset:offset+11].decode('ascii', errors='replace')
            
            return battery1, battery2, battery3, sensors, gps
            
        except Exception as e:
            print(f"Telemetry decoding failed: {e}")
            raise

    def parse_telemetry_payload(self, payload):
        """
        Parse telemetry payload while preserving numerical values for graphing
        
        Args:
            payload (bytes): Raw telemetry data
            
        Returns:
            list: Raw numerical values (no string conversion)
        """
        try:
            # First decode the structured data
            battery1, battery2, battery3, sensors, gps = self.decode_telemetry(payload)
            
            # Return numerical values in this exact order:
            return [
                *battery1,  # 5 battery1 metrics (floats)
                *battery2,  # 5 battery2 metrics (floats)
                *battery3,  # 5 battery3 metrics (floats)
                *sensors,   # 10 sensor metrics (floats)
                gps         # 1 GPS string
            ]
            
        except Exception as e:
            print(f"Telemetry parsing failed: {e}")
            return []
