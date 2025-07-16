import os
import csv
import pytest
from dataclasses import dataclass
import sys

# Make data_handler.py importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_handler import DataHandler, DATA_SAVED, TELEMETRY_SAVED

# ============================================================
# Test Data Structures Based on Actual Satellite Packet Format
# ============================================================

@dataclass
class CameraPacket:
    payload_type: int   # 0x11 (intermediate) or 0x12 (final)
    data: bytes         # Data field (up to 122 bytes)
    offset: int         # 3 bytes (24 bits)
    seq_num: int        # 2 bytes (16 bits)

@dataclass
class TelemetryPacket:
    payload_type: int   # 0x10
    data: str           # CSV-formatted string
    seq_num: int        # 2 bytes (16 bits)

# ====================================
# Pytest Fixture for Database Path
# ====================================

@pytest.fixture
def data_handler():
    # Use relative paths inside 'ground_station/database/'
    base_dir = os.path.join("ground_station", "database")
    image_dir = os.path.join(base_dir, "bin_images")
    telemetry_dir = os.path.join(base_dir, "telemetry")
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(telemetry_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "jpeg_images"), exist_ok=True)  # Optional for future JPEG support
    return DataHandler(data_type="both", image_dir=image_dir, telemetry_dir=telemetry_dir)

# ==========================
# Helper: Create Camera Bytes
# ==========================

def create_camera_payload(packet: CameraPacket) -> bytes:
    return (
        packet.payload_type.to_bytes(1, 'big') +
        packet.data.ljust(122, b'\x00')[:122] +
        packet.offset.to_bytes(3, 'big') +
        packet.seq_num.to_bytes(2, 'big')
    )

# =============================
# Helper: Create Telemetry Bytes
# =============================

def create_telemetry_payload(packet: TelemetryPacket) -> bytes:
    return (
        packet.payload_type.to_bytes(1, 'big') +
        packet.data.encode('ascii') +
        packet.seq_num.to_bytes(2, 'big')
    )

# ===========================
# TELEMETRY DATA TEST CASE
# ===========================

def test_telemetry_storage(data_handler):
    packets = [
        TelemetryPacket(0x10, "23.5,42.1,1002", 1),
        TelemetryPacket(0x10, "24.0,41.9,1005", 2),
        TelemetryPacket(0x10, "22.8,42.3,1001", 3),
    ]
    for p in packets:
        data_handler.process_packet(create_telemetry_payload(p))

    telemetry_file = os.path.join(data_handler.telemetry_dir, "telemetry.csv")
    assert os.path.exists(telemetry_file)

    with open(telemetry_file, newline='') as f:
        rows = list(csv.reader(f))

    assert len(rows) == 4  # 1 header + 3 data rows
    assert rows[0] == ["Field_0", "Field_1", "Field_2"]
    assert rows[1] == ["23.5", "42.1", "1002"]
    assert rows[3] == ["22.8", "42.3", "1001"]

    for i in range(3):
        field_file = os.path.join("database", f"Field_{i}.csv")
        assert os.path.exists(field_file)
        with open(field_file) as f:
            field_lines = f.readlines()
        assert len(field_lines) == 4  # header + 3 values

    assert TELEMETRY_SAVED is True

# ==========================
# CAMERA DATA TEST CASE
# ==========================

def test_camera_storage(data_handler):
    packets = [
        CameraPacket(0x11, b'\x01'*122, 0, 1),
        CameraPacket(0x11, b'\x02'*122, 122, 1),
        CameraPacket(0x11, b'\x03'*122, 244, 1),
        CameraPacket(0x11, b'\x04'*122, 366, 1),
        CameraPacket(0x12, b'\x05'*24, 488, 1),
    ]
    for p in packets:
        data_handler.process_packet(create_camera_payload(p))

    found = False
    for f in os.listdir(data_handler.image_dir):
        if f.endswith("_1.bin"):
            expected_file = os.path.join(data_handler.image_dir, f)
            found = True
            break

    assert found

    expected_data = (
        b'\x01'*122 + b'\x02'*122 + b'\x03'*122 + b'\x04'*122 + b'\x05'*24
    )
    with open(expected_file, 'rb') as f:
        content = f.read()
    assert content.startswith(b'\x01')
    assert content.endswith(b'\x05'*24)
    assert len(content) == 4*122 + 24
    assert DATA_SAVED is True

# ============================
# CAMERA EDGE CASE TEST
# ============================

def test_camera_final_24_byte_only(data_handler, capsys):
    packet = CameraPacket(0x12, b'\xAA'*24, 0, 2)
    data_handler.process_packet(create_camera_payload(packet))

    saved_file = None
    for f in os.listdir(data_handler.image_dir):
        if f.endswith("_2.bin"):
            saved_file = os.path.join(data_handler.image_dir, f)
            break

    assert saved_file and os.path.exists(saved_file)

    with open(saved_file, 'rb') as f:
        assert f.read() == b'\xAA'*24

    captured = capsys.readouterr()
    assert "✅ Image saved" in captured.out
    assert "error" not in captured.out.lower()

# =============================
# MIXED PAYLOAD TEST CASE
# =============================

def test_mixed_camera_and_telemetry(data_handler):
    packets = [
        TelemetryPacket(0x10, "11.1,22.2", 1),
        CameraPacket(0x11, b'\xAB'*122, 0, 1),
        TelemetryPacket(0x10, "33.3,44.4", 2),
        CameraPacket(0x12, b'\xCD'*24, 122, 1),
    ]
    for p in packets:
        if p.payload_type == 0x10:
            data_handler.process_packet(create_telemetry_payload(p))
        else:
            data_handler.process_packet(create_camera_payload(p))

    telemetry_file = os.path.join(data_handler.telemetry_dir, "telemetry.csv")
    assert os.path.exists(telemetry_file)

    image_found = any(f.endswith("_1.bin") for f in os.listdir(data_handler.image_dir))
    assert image_found
    assert TELEMETRY_SAVED is True
    assert DATA_SAVED is True
