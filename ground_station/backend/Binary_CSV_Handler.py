import os
import csv

# ==============================================
# GLOBAL VARIABLES
# ==============================================
DATA_SAVED = False       # Tracks whether camera data was successfully saved
TELEMETRY_SAVED = False  # Tracks whether telemetry data was successfully saved

class DataHandler:
    """Main class for handling satellite data packets including both camera images and telemetry data"""
    
    # Class-level variable shared across all instances
    sequence_number = 0  # Tracks the sequence number of packets for ordering

    def __init__(self, image_dir="images", telemetry_dir="telemetry"):
        """
        Initialize the data handler with storage directories
        
        Args:
            image_dir (str): Directory to store camera images
            telemetry_dir (str): Directory to store telemetry CSV files
        """
        # Initialize instance variables
        self.image_dir = image_dir         # Directory for image storage
        self.telemetry_dir = telemetry_dir # Directory for telemetry data
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
            identifier, seq_num, offset, image_data = self.parse_camera_payload(payload)
            
            # Generate filename using identifier and sequence number
            file_path = os.path.join(
                self.image_dir, 
                f"{identifier}_{seq_num}.bin"  # Using .bin format
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
            self.recent_files[identifier] = file_path
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
            assert len(payload) >= 3, "Telemetry payload must be at least 3 bytes"
            
            # Parse the raw payload into a list of values
            values = self.parse_telemetry_payload(payload)
            if not values:
                return

            # Set up CSV file path
            csv_file = os.path.join(self.telemetry_dir, "telemetry.csv")

            # Initialize headers on first packet if needed
            if not self.global_headers:
                self.global_headers = [f"Field_{i}" for i in range(len(values))]

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
        Decodes camera payload into its components using new binary format
        
        Args:
            payload (bytes): Raw camera payload data
            
        Returns:
            tuple: (identifier, sequence_number, offset, image_data)
            
        Format:
            - First 1 byte: ASCII identifier
            - Next 122 bytes: Image data
            - Next 2 bytes: Sequence number (big-endian)
            - Next 3 bytes: Offset 
        """
        try:
            identifier = chr(payload[0])                        # 1-byte identifier
            image_data = payload[1:123]                         # 122 bytes of image data
            seq_num = int.from_bytes(payload[123:125], 'big')  # 2-byte sequence number
            offset = int.from_bytes(payload[125:128], 'big')   # 3-byte offset
            return identifier, seq_num, offset, image_data
            
        except Exception as e:
            print(f"Camera payload parsing failed: {e}")
            raise

    def parse_telemetry_payload(self, payload):
        """
        Converts telemetry payload from bytes to a list of string values
        
        Args:
            payload (bytes): Raw telemetry data
            
        Returns:
            list: Cleaned values extracted from payload
        
        Format:
            - ASCII-encoded CSV values
            - Last 2 bytes: Sequence number (excluded from output)
        """
        try:
            # Strip off the last 2 bytes (sequence number)
            csv_part = payload[:-2]
            decoded = csv_part.decode('ascii', errors='replace').strip()
            return [x.strip() for x in decoded.split(",") if x.strip()]
            
        except Exception as e:
            print(f"Telemetry parsing failed: {e}")
            return []
