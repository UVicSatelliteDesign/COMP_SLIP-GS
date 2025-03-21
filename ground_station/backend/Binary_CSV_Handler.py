import os
import csv
import pickle

class DataHandler:
    def __init__(self, image_dir="images", telemetry_dir="telemetry"):
        self.image_dir = image_dir
        self.telemetry_dir = telemetry_dir
        self.recent_files = {}  # Tracks most recent files
        self.global_headers = set()  # Stores global headers for telemetry
        self.last_sequence_number = None  # Tracks sequence number for retransmissions
        self.data_saved = False  # Boolean flag for saving status

        # Ensure directories exist
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.telemetry_dir, exist_ok=True)

    def process_packet(self, packet):
        """Processes an incoming data packet and routes it accordingly."""
        data_type = packet[:4]  # First 4 bits determine the type
        payload = packet[4:]  # Remaining data

        match data_type:
            case b"\x00\x00\x00\x00":  # Ping
                self.handle_ping()
            case b"\x00\x00\x00\x01":  # Nominal
                self.handle_nominal()
            case b"\x00\x00\x00\x10":  # Low Power Telemetry
                self.handle_telemetry_data(payload)
            case b"\x00\x00\x00\x11":  # Camera-1 End
                self.handle_camera_data(payload, end=True)
            case b"\x00\x00\x01\x00":  # Camera-1 MF
                self.handle_camera_data(payload, end=False)
            case b"\x00\x00\x01\x01":  # Camera-2 End
                self.handle_camera_data(payload, end=True)
            case b"\x00\x00\x01\x10":  # Camera-2 MF
                self.handle_camera_data(payload, end=False)
            case b"\x10\x00\x00\x00":  # Retransmission
                self.handle_retransmission(payload)
            case b"\x10\x00\x00\x01":  # Error - CRC
                self.handle_error("CRC")
            case b"\x10\x00\x00\x10":  # Error - Duplicate
                self.handle_error("Duplicate")
            case b"\x10\x00\x00\x11":  # Error - Low Power
                self.handle_error("Low Power")
            case _:  # Unknown packet type
                print("Unknown packet type received!")

    def handle_camera_data(self, payload, end):
        """Handles and stores incoming camera data."""
        identifier, offset, mf_flag, image_data = self.parse_camera_payload(payload)
        file_path = os.path.join(self.image_dir, f"{identifier}_{offset}.pkl")

        # Store or append based on More Flag (MF)
        mode = "wb" if offset == 0 else "ab"
        with open(file_path, mode) as f:
            f.write(image_data)

        if not mf_flag or end:  # If last fragment, finalize
            self.recent_files[identifier] = file_path
            print(f"✅ Finalized image: {file_path}")

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

    def handle_retransmission(self, payload):
        """Handles retransmission logic based on sequence numbers."""
        sequence_number = int.from_bytes(payload[:2], 'big')
        
        if self.last_sequence_number is not None and sequence_number <= self.last_sequence_number:
            print("Retransmitted packet ignored due to outdated sequence number.")
            return
        
        self.last_sequence_number = sequence_number
        print(f"Retransmission handled for sequence number: {sequence_number}")

    def handle_error(self, error_type):
        """Handles error conditions."""
        print(f"Error detected: {error_type}")

    def parse_camera_payload(self, payload):
        """Parses camera payload to extract identifier, offset, MF flag, and image data."""
        identifier = payload[:8].decode()  # Extract identifier
        offset = int.from_bytes(payload[8:12], 'big')  # Extract offset
        mf_flag = bool(payload[12])  # Extract More Flag
        image_data = payload[13:]  # Extract actual image data
        return identifier, offset, mf_flag, image_data

    def parse_telemetry_payload(self, payload):
        """Parses telemetry payload and extracts data."""
        telemetry_dict = {}  # Placeholder for parsed telemetry data
        data_fields = payload.decode().split(",")  # Assuming CSV-like input
        for field in data_fields:
            key, value = field.split(":")
            telemetry_dict[key.strip()] = value.strip()
        return telemetry_dict
