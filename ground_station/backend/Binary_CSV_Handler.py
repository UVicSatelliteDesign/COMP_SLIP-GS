import os
import csv
import pickle

# ==============================================
# GLOBAL VARIABLES
# ==============================================
DATA_SAVED = False       # Tracks whether camera data was successfully saved
TELEMETRY_SAVED = False  # Tracks whether telemetry data was successfully saved

class DataHandler:
    """Main class for handling satellite data packets including both camera images and telemetry data"""
    
    # Class-level variable shared across all instances
    sequence_number = 0  # Tracks the sequence number of packets for ordering

    def __init__(self, data_type, payload=None, image_dir="images", telemetry_dir="telemetry"):
        """
        Initialize the data handler with storage directories
        
        Args:
            image_dir (str): Directory to store camera images
            telemetry_dir (str): Directory to store telemetry CSV files
        """
        # Initialize instance variables
        self.image_dir = image_dir         # Directory for image storage
        self.telemetry_dir = telemetry_dir # Directory for telemetry data
        self.data_type = data_type
        self.payload = payload
        self.recent_files = {}             # Dictionary to track most recent files by identifier
        self.global_headers = []           # List to store CSV column headers for telemetry data
        
        # Create directories if they don't exist, with error handling
        try:
            os.makedirs(self.image_dir, exist_ok=True)      # -p flag equivalent (no error if exists)
            os.makedirs(self.telemetry_dir, exist_ok=True)  # Create telemetry directory
        except OSError as e:
            print(f"Directory creation failed: {e}")
            raise  # Re-raise exception to notify calling code

    def process_packet(self):
        """
        Main packet processing router that validates and directs packets to appropriate handlers
        
        Args:
            packet (bytes): Raw binary packet data received from satellite
        """
        try:
            # Development-time validation checks (can be disabled with Python -O flag)
            # assert isinstance(packet, bytes), "Packet must be in bytes format"
            # assert len(packet) >= 4, "Packet must contain at least 4 bytes (header)"
            
            # Extract packet type from first 4 bytes
            # data_type = packet[:4]  # Packet type identifier
            # payload = packet[4:]    # Actual payload data


            # Route to appropriate handler based on packet type
            if self.data_type == b"\x00\x00\x00\x10":  # Telemetry packet identifier
                self.handle_telemetry_data(self.payload)
            elif self.data_type in [b"\x00\x00\x00\x11", b"\x00\x00\x01\x00"]:  # Camera packet identifiers
                self.handle_camera_data(self.payload)
            else:
                print(f"Unknown packet type: {self.payload}")  # Unrecognized packet type

        except AssertionError as e:
            # Handle failed validation assertions
            print(f"Invalid packet format: {e}")
        except Exception as e:
            # Catch-all for other processing errors
            print(f"Packet processing failed: {e}")

    def handle_camera_data(self, payload):
        """
        Processes camera data payload including image data and offset information
        
        Args:
            payload (bytes): Camera-specific payload data
        """
        global DATA_SAVED  # Access the global camera data saved flag
        
        try:
            # Validate payload meets minimum size requirements
            assert len(payload) >= 11, f"Camera payload requires at least 11 bytes, got {len(payload)}"
            
            # Parse the payload into its components
            identifier, offset, image_data = self.parse_camera_payload(payload)
            
            # Generate filename using identifier and sequence number
            file_path = os.path.join(
                self.image_dir,
                f"{identifier}_{DataHandler.sequence_number}.pkl"  # Using pickle format
            )

            # Write image data to file with error handling
            try:
                # 'wb' mode if offset=0 (new file), 'ab' if offset>0 (append to existing)
                with open(file_path, "wb" if offset == 0 else "ab") as f:
                    f.write(image_data)  # Write binary image data
            except IOError as e:
                print(f"Failed to write image: {e}")
                return  # Abort on file write failure

            # Update tracking information
            self.recent_files[identifier] = file_path  # Track most recent file
            DATA_SAVED = True                         # Update global flag
            DataHandler.sequence_number += 1           # Increment class sequence counter

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
        global TELEMETRY_SAVED  # Access the global telemetry saved flag
        
        try:
            # Validate payload contains data
            assert len(payload) > 0, "Telemetry payload cannot be empty"
            
            # Parse the raw payload into a list of values
            values = self.parse_telemetry_payload(payload)
            if not values:  # Skip if parsing failed
                return

            # Set up CSV file path
            csv_file = os.path.join(self.telemetry_dir, "telemetry.csv")

            # Initialize headers on first packet if needed
            if not self.global_headers:
                # Create default headers (Field_0, Field_1, etc.) matching value count
                self.global_headers = [f"Field_{i}" for i in range(len(values))]

            # Write to CSV file with error handling
            try:
                with open(csv_file, "a", newline="") as f:  # 'a' for append mode
                    writer = csv.writer(f)
                    
                    # Write header only if file is empty/new
                    if os.stat(csv_file).st_size == 0:
                        writer.writerow(self.global_headers)
                    
                    # Write the current values row
                    writer.writerow(values)
            except IOError as e:
                print(f"Failed to write telemetry: {e}")
                return  # Abort on file write failure

            TELEMETRY_SAVED = True  # Update global flag

        except AssertionError as e:
            print(f"Invalid telemetry: {e}")
        except Exception as e:
            print(f"Telemetry processing error: {e}")

    def parse_camera_payload(self, payload):
        """
        Decodes camera payload into its components using specific binary format
        
        Args:
            payload (bytes): Raw camera payload data
            
        Returns:
            tuple: (identifier, offset, image_data)
            
        Format:
            - First 8 bytes: ASCII identifier
            - Last 3 bytes: 17-bit offset (bits distributed across 3 bytes)
            - Middle: Image data
        """
        try:
            # Extract 8-byte identifier and decode to ASCII
            identifier = payload[:8].decode('ascii', errors='replace').strip()
            
            # Extract last 3 bytes for offset calculation
            offset_bytes = payload[-3:]
            
            # Calculate 17-bit offset from the 3 bytes:
            # - First byte: Take 5 bits (mask with 0x1F) and shift left 12
            # - Second byte: Take all 8 bits and shift left 4
            # - Third byte: Take upper 4 bits (shift right 4)
            offset = ((offset_bytes[0] & 0x1F) << 12) | \
                     (offset_bytes[1] << 4) | \
                     (offset_bytes[2] >> 4)
            
            # Return components (identifier, calculated offset, image data)
            return identifier, offset, payload[8:-3]
            
        except Exception as e:
            print(f"Camera payload parsing failed: {e}")
            raise  # Re-raise as this is a critical failure

    def parse_telemetry_payload(self, payload):
        """
        Converts telemetry payload from bytes to a list of string values
        
        Args:
            payload (bytes): Raw telemetry data
            
        Returns:
            list: Cleaned values extracted from payload
        """
        try:
            # Decode bytes to ASCII, with error replacement for invalid chars
            decoded = payload.decode('ascii', errors='replace').strip()
            
            # Split by commas, strip whitespace, and filter empty strings
            return [x.strip() for x in decoded.split(",") if x.strip()]
            
        except Exception as e:
            print(f"Telemetry parsing failed: {e}")
            return []  # Return empty list on failure
