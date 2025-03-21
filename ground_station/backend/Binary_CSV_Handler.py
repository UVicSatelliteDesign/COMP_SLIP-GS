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
        identifier, sequence_number, offset, image_data = self.parse_camera_payload(payload)
        file_path = os.path.join(self.image_dir, f"{identifier}_{sequence_number}.pkl")

        mode = "wb" if offset == 0 else "ab"
        with open(file_path, mode) as f:
            f.write(image_data)

        self.recent_files[identifier] = file_path
        self.data_saved = True  # Mark data as saved

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
        """Parses camera payload to extract identifier, sequence number, offset, and image data."""
        identifier = payload[:8].decode()  # Extract identifier
        sequence_number = int.from_bytes(payload[8:12], 'big')  # Extract sequence number
        offset = int.from_bytes(payload[-4:], 'big')  # Extract offset (from second last position)
        image_data = payload[12:-4]  # Extract actual image data
        return identifier, sequence_number, offset, image_data

    def parse_telemetry_payload(self, payload):
        """Parses telemetry payload and extracts data."""
        telemetry_dict = {}  # Placeholder for parsed telemetry data
        data_fields = payload.decode().split(",")  # Assuming CSV-like input
        for field in data_fields:
            key, value = field.split(":")
            telemetry_dict[key.strip()] = value.strip()
        return telemetry_dict
