import os
import csv
import pickle

# GLOBAL VARIABLES (as requested)
DATA_SAVED = False  # Global flag for camera data
TELEMETRY_SAVED = False  # Separate global flag for telemetry

class DataHandler:
    # Class variable for sequence number
    sequence_number = 0

    def __init__(self, image_dir="images", telemetry_dir="telemetry"):
        self.image_dir = image_dir
        self.telemetry_dir = telemetry_dir
        self.recent_files = {}  # Tracks most recent files
        self.global_headers = []  # Stores telemetry headers

        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.telemetry_dir, exist_ok=True)

    def process_packet(self, packet):
        """Processes incoming data packet with validation"""
        assert isinstance(packet, bytes), "Packet must be bytes"
        assert len(packet) >= 4, "Packet too short (needs 4+ bytes)"
        
        data_type = packet[:4]
        payload = packet[4:]

        if data_type == b"\x00\x00\x00\x10":  # Telemetry
            self.handle_telemetry_data(payload)
        elif data_type in [b"\x00\x00\x00\x11", b"\x00\x00\x01\x00"]:  # Camera
            self.handle_camera_data(payload)
        else:
            print(f"Unknown packet type: {data_type}")

    def handle_camera_data(self, payload):
        """Handles camera data with 17-bit offset"""
        global DATA_SAVED  # Using global variable
        assert len(payload) >= 11, f"Camera payload needs ≥11 bytes, got {len(payload)}"
        
        identifier, offset, image_data = self.parse_camera_payload(payload)
        file_path = os.path.join(self.image_dir, f"{identifier}_{DataHandler.sequence_number}.pkl")

        with open(file_path, "wb" if offset == 0 else "ab") as f:
            f.write(image_data)

        self.recent_files[identifier] = file_path
        DATA_SAVED = True  # Update global flag
        DataHandler.sequence_number += 1  # Update class variable

    def handle_telemetry_data(self, payload):
        """Handles telemetry data with direct writerow"""
        global TELEMETRY_SAVED  # Using separate global variable
        assert len(payload) > 0, "Telemetry payload empty"
        
        values = self.parse_telemetry_payload(payload)
        if not values:
            return

        csv_file = os.path.join(self.telemetry_dir, "telemetry.csv")

        # Initialize headers if first packet
        if not self.global_headers:
            self.global_headers = [f"Field_{i}" for i in range(len(values))]

        with open(csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            if os.stat(csv_file).st_size == 0:
                writer.writerow(self.global_headers)
            writer.writerow(values)  # Directly write values

        TELEMETRY_SAVED = True  # Update separate global flag

    def parse_camera_payload(self, payload):
        """Extracts: 8B identifier, image data, 17-bit offset (last 3B)"""
        identifier = payload[:8].decode('ascii', errors='replace').strip()
        
        # Extract last 17 bits from final 3 bytes
        offset_bytes = payload[-3:]
        offset = ((offset_bytes[0] & 0x1F) << 12) | (offset_bytes[1] << 4) | (offset_bytes[2] >> 4)
        
        return identifier, offset, payload[8:-3]

    def parse_telemetry_payload(self, payload):
        """Returns clean list of values (no keys)"""
        try:
            decoded = payload.decode('ascii', errors='replace').strip()
            return [x.strip() for x in decoded.split(",") if x.strip()]
        except Exception as e:
            print(f"Telemetry decode failed: {e}")
            return []
