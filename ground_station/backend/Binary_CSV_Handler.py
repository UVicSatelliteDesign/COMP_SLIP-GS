import os
import csv
import pickle

class DataHandler:
    def __init__(self, image_dir="images", telemetry_dir="telemetry"):
        self.image_dir = image_dir
        self.telemetry_dir = telemetry_dir
        self.recent_files = {}  # Tracks the most recent files for each identifier
        self.global_headers = set()  # Stores global headers for CSV telemetry data

        # Ensure directories exist
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.telemetry_dir, exist_ok=True)

    def process_packet(self, packet):
        """Processes an incoming data packet and directs it to the correct handler."""
        data_type = packet[:4]  # First 4 bits determine the type
        payload = packet[4:]  # Remaining data

        if data_type == b'CAMR':
            self.handle_camera_data(payload)
        elif data_type == b'TELM':
            self.handle_telemetry_data(payload)
        else:
            print("Unknown data type.")

    def handle_camera_data(self, payload):
        """Handles and stores incoming camera data."""
        identifier, offset, mf_flag, image_data = self.parse_camera_payload(payload)
        file_path = os.path.join(self.image_dir, f"{identifier}_{offset}.pkl")
        
        # Store or append based on More Flag (MF)
        mode = "wb" if offset == 0 else "ab"
        with open(file_path, mode) as f:
            f.write(image_data)

        if not mf_flag:  # If last fragment, finalize
            self.recent_files[identifier] = file_path
            print(f"✅ Finalized image: {file_path}")

    def handle_telemetry_data(self, payload):
        """Handles and stores incoming telemetry data in CSV."""
        identifier, telemetry_dict = self.parse_telemetry_payload(payload)
        csv_file = os.path.join(self.telemetry_dir, f"{identifier}.csv")

        # Store headers globally
        self.global_headers.update(telemetry_dict.keys())
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.global_headers))
            if not file_exists:
                writer.writeheader()
            writer.writerow(telemetry_dict)

        print(f"✅ Telemetry data saved: {csv_file}")

    def parse_camera_payload(self, payload):
        """Parses the camera payload to extract identifier, offset, MF flag, and image data."""
        identifier = payload[:8].decode()  # Extract identifier
        offset = int.from_bytes(payload[8:12], 'big')  # Extract offset
        mf_flag = bool(payload[12])  # Extract More Flag
        image_data = payload[13:]  # Extract actual image data
        return identifier, offset, mf_flag, image_data

    def parse_telemetry_payload(self, payload):
        """Parses telemetry payload and extracts identifier and data."""
        identifier = payload[:8].decode()
        telemetry_dict = {}  # Placeholder for parsed telemetry data
        return identifier, telemetry_dict
