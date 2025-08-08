import os
import csv

# ==============================================
# GLOBAL FLAGS
# ==============================================
DATA_SAVED = False       # Tracks whether camera data was successfully saved
TELEMETRY_SAVED = False  # Tracks whether telemetry data was successfully saved

class DataHandler:
    """Handles camera and telemetry data packets from satellite and stores them appropriately."""

    sequence_number = 0  # Class-level sequence number (for tracking)

    def __init__(self, data_type, payload_type=None, image_dir="images", telemetry_dir="telemetry"):
        """
        Initializes handler for storing data from packets.

        Args:
            data_type (str): "camera" or "telemetry"
            payload_type (int, optional): Packet type identifier (0x10, 0x11, etc.)
            image_dir (str): Directory to store binary image files
            telemetry_dir (str): Directory to store telemetry CSV files
        """
        self.data_type = data_type
        self.payload_type = payload_type
        self.image_dir = image_dir
        self.telemetry_dir = telemetry_dir
        self.recent_files = {}
        self.global_headers = []

        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.telemetry_dir, exist_ok=True)
        os.makedirs("database", exist_ok=True)  # For ExpandingGraph compatibility

    def process_packet(self, packet):
        """
        Routes incoming packet to appropriate handler.

        Args:
            packet (bytes): Raw packet (first byte is payload type)
        """
        try:
            assert isinstance(packet, bytes), "Packet must be in bytes"
            assert len(packet) >= 5, "Packet too short"

            payload_type = packet[0]
            payload = packet[1:]

            if payload_type == 0x10:
                self.handle_telemetry_data(payload)
            elif payload_type in [0x11, 0x12]:
                self.handle_camera_data(payload)
            else:
                print(f"⚠️ Unknown payload type: {payload_type}")

        except Exception as e:
            print(f"❌ Packet processing failed: {e}")

    def handle_camera_data(self, payload):
        """
        Stores binary camera image payload into .bin files.

        Format:
        - Byte 0: Identifier (1 byte)
        - Byte 1-122: Image data (122 bytes)
        - Byte 123-125: Offset (3 bytes)
        - Byte 126-127: Sequence number (2 bytes)

        Args:
            payload (bytes): Camera payload
        """
        global DATA_SAVED

        try:
            assert len(payload) <= 128, "Invalid camera payload size"
            assert len(payload) >=3, "Invalid camera Payload size too small"

            identifier = chr(payload[0])  # 1-byte ASCII
            image_data = payload[1:123]   # 122 bytes of data
            offset = int.from_bytes(payload[123:126], 'big')
            seq_num = int.from_bytes(payload[126:128], 'big')

            file_path = os.path.join(self.image_dir, f"{identifier}_{seq_num}.bin")

            with open(file_path, "wb" if offset == 0 else "ab") as f:
                f.write(image_data)

            self.recent_files[identifier] = file_path
            DataHandler.sequence_number = (seq_num + 1) & 0xFFFF
            DATA_SAVED = True
            print(f"✅ Image saved: {file_path}")

        except Exception as e:
            print(f"❌ Camera processing error: {e}")

    def handle_telemetry_data(self, payload):
        """
        Stores telemetry data in both combined and individual CSVs.

        Format:
        - Byte 0 to N-3: Comma-separated ASCII telemetry data
        - Byte N-2 to N-1: 2-byte sequence number (big-endian)

        Args:
            payload (bytes): Telemetry payload
        """
        global TELEMETRY_SAVED

        try:
            assert len(payload) > 2, "Telemetry payload too short"

            data_bytes = payload[:-2]
            values = self.parse_telemetry_payload(data_bytes)
            if not values:
                return

            telemetry_csv = os.path.join(self.telemetry_dir, "telemetry.csv")

            if not self.global_headers:
                self.global_headers = [f"Field_{i}" for i in range(len(values))]

            # Write full row to telemetry.csv
            with open(telemetry_csv, "a", newline="") as f:
                writer = csv.writer(f)
                if os.stat(telemetry_csv).st_size == 0:
                    writer.writerow(self.global_headers)
                writer.writerow(values)

            # Write each field to separate database/Field_X.csv
            for i, val in enumerate(values):
                field_file = os.path.join("database", f"{self.global_headers[i]}.csv")
                file_exists = os.path.exists(field_file)
                with open(field_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow([self.global_headers[i]])
                    writer.writerow([val])

            TELEMETRY_SAVED = True
            print("✅ Telemetry saved successfully")

        except Exception as e:
            print(f"❌ Telemetry processing error: {e}")

    def parse_camera_payload(self, payload):
        """
        Legacy support (not used in new binary format).
        """
        pass  # Not required in final version

    def parse_telemetry_payload(self, payload):
        """
        Converts ASCII CSV telemetry payload to list of values.

        Args:
            payload (bytes): e.g. b"12.5, 1023, 89.1"

        Returns:
            list[str]: Cleaned list of telemetry fields
        """
        try:
            decoded = payload.decode('ascii', errors='replace').strip()
            return [x.strip() for x in decoded.split(",") if x.strip()]
        except Exception as e:
            print(f"❌ Telemetry parsing failed: {e}")
            return []
