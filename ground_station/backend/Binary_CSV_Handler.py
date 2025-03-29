import os
import csv
import pickle

class DataHandler:
    def __init__(self, image_dir="images", telemetry_dir="telemetry"):
        self.image_dir = image_dir
        self.telemetry_dir = telemetry_dir
        self.recent_files = {}  # Tracks most recent files
        self.global_headers = set()  # Stores global headers for telemetry
        self.data_saved = False  # Global flag for saving status
        self.sequence_number = 0  # Global sequence number variable

        # Ensure directories exist
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.telemetry_dir, exist_ok=True)

    def process_packet(self, packet):
        """Processes an incoming data packet and routes it accordingly."""
        data_type = packet[:4]  # First 4 bits determine the type
        payload = packet[4:]  # Remaining data

        if data_type == b"\x00\x00\x00\x10":  # Telemetry
            self.handle_telemetry_data(payload)
        elif data_type in [b"\x00\x00\x00\x11", b"\x00\x00\x01\x00"]:  # Camera
            self.handle_camera_data(payload)
        else:
            print("Unknown packet type received!")

    def handle_camera_data(self, payload):
        """Handles and stores incoming camera data."""
        identifier, offset, image_data = self.parse_camera_payload(payload)
        file_path = os.path.join(self.image_dir, f"{identifier}_{self.sequence_number}.pkl")

        mode = "wb" if offset == 0 else "ab"
        with open(file_path, mode) as f:
            f.write(image_data)

        self.recent_files[identifier] = file_path
        self.data_saved = True  # Mark data as saved
        self.sequence_number += 1  # Increment global sequence number

    def handle_telemetry_data(self, payload):
        """Handles and stores telemetry data in CSV."""
        telemetry_dict = self.parse_telemetry_payload(payload)
        csv_file = os.path.join(self.telemetry_dir, "telemetry.csv")

        # Store headers globally
        self.global_headers.update(telemetry_dict.keys())

        with open(csv_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.global_headers))
            if os.stat(csv_file).st_size == 0:
                writer.writeheader()
            writer.writerow(telemetry_dict)

        self.data_saved = True  # Mark data as saved

    def parse_camera_payload(self, payload):
        """Parses camera payload to extract identifier, offset, and image data.
        Now uses last 16 bits for offset as per the image specification."""
        identifier = payload[:8].decode()  # Extract identifier
        offset = int.from_bytes(payload[-2:], 'big')  # Extract offset from last 16 bits
        image_data = payload[8:-2]  # Extract actual image data (between identifier and offset)
        return identifier, offset, image_data

    def parse_telemetry_payload(self, payload):
        """Parses telemetry payload and extracts data."""
        telemetry_dict = {}  # Placeholder for parsed telemetry data
        data_fields = payload.decode().split(",")  # Assuming CSV-like input
        for field in data_fields:
            key, value = field.split(":")
            telemetry_dict[key.strip()] = value.strip()
        return telemetry_dict
