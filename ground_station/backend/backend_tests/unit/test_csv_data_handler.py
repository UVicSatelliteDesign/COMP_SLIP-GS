import os
import csv
import pytest
from dataclasses import dataclass
import sys
import struct

# Make data_handler.py importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ground_station.backend.Binary_CSV_Handler import (
    DataHandler,
    DATA_SAVED,
    TELEMETRY_SAVED,
    BatteryData,
    SensorsData,
)
# ============================================================
# Test Data Structures
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
    batteries: list     # 3 BatteryData tuples
    sensors: SensorsData
    gps: str           # 11-byte ASCII string

# ====================================
# Pytest Fixture
# ====================================

@pytest.fixture
def data_handler():
    # Use temporary directories for testing
    base_dir = "test_database"
    image_dir = os.path.join(base_dir, "bin_images")
    telemetry_dir = os.path.join(base_dir, "telemetry")
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(telemetry_dir, exist_ok=True)
    yield DataHandler(data_type="both", image_dir=image_dir, telemetry_dir=telemetry_dir)
    
    # Cleanup after tests
    import shutil
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)

# ==========================
# Helper Functions
# ==========================

def create_camera_payload(packet: CameraPacket) -> bytes:
    """Same as original camera payload creator"""
    return (
        packet.payload_type.to_bytes(1, 'big') +
        packet.data.ljust(122, b'\x00')[:122] +
        packet.offset.to_bytes(3, 'big') +
        packet.seq_num.to_bytes(2, 'big')
    )

def create_telemetry_payload(packet: TelemetryPacket) -> bytes:
    """New telemetry payload creator for binary format"""
    payload = bytearray()
    
    # Pack all battery data (3 batteries * 5 floats)
    for bat in packet.batteries:
        payload.extend(struct.pack('>5f', *bat))
    
    # Pack sensor data (10 floats)
    payload.extend(struct.pack('>10f', *packet.sensors))
    
    # Add GPS string (11 bytes)
    payload.extend(packet.gps.ljust(11, '\x00').encode('ascii')[:11])
    
    return packet.payload_type.to_bytes(1, 'big') + payload

# ===========================
# TEST CASES
# ===========================

def test_telemetry_storage(data_handler):
    """Test new binary telemetry format"""
    test_packet = TelemetryPacket(
        payload_type=0x10,
        batteries=[
            BatteryData(3.7, 1.2, 95.5, 4.44, 120.0),
            BatteryData(3.6, 1.1, 90.0, 3.96, 110.5),
            BatteryData(3.8, 1.3, 92.3, 4.94, 115.2)
        ],
        sensors=SensorsData(
            25.5, 26.1, 24.8,  # temps
            0.1, -0.2, 0.05,   # gyro
            0.01, 0.02, -0.98,  # accel
            152.3               # altitude
        ),
        gps="GPGGA,123"
    )
    
    data_handler.process_packet(create_telemetry_payload(test_packet))
    
    # Verify CSV output
    telemetry_file = os.path.join(data_handler.telemetry_dir, "telemetry.csv")
    assert os.path.exists(telemetry_file)
    
    with open(telemetry_file, newline='') as f:
        rows = list(csv.reader(f))
    
    assert len(rows) == 2  # header + data
    assert rows[0] == data_handler.global_headers
    
    # Check first 5 values (Battery1)
    assert float(rows[1][0]) == pytest.approx(3.7)   # bat1_voltage
    assert float(rows[1][1]) == pytest.approx(1.2)   # bat1_current
    assert float(rows[1][4]) == pytest.approx(120.0) # bat1_life
    
    # Check sensor values
    assert float(rows[1][15]) == pytest.approx(25.5) # temp_obc
    assert float(rows[1][24]) == pytest.approx(152.3) # altitude
    
    # Check GPS
    assert rows[1][25] == "GPGGA,123"
    
    assert TELEMETRY_SAVED is True

def test_camera_storage(data_handler):
    """Original camera test should still pass"""
    packets = [
        CameraPacket(0x11, b'\x01'*122, 0, 1),
        CameraPacket(0x11, b'\x02'*122, 122, 1),
        CameraPacket(0x12, b'\x03'*24, 244, 1)
    ]
    
    for p in packets:
        data_handler.process_packet(create_camera_payload(p))
    
    # Verify file was created and contains correct data
    expected_file = os.path.join(data_handler.image_dir, "camera_1.bin")
    assert os.path.exists(expected_file)
    
    with open(expected_file, 'rb') as f:
        content = f.read()
    
    assert len(content) == 2*122 + 24
    assert content.startswith(b'\x01'*122)
    assert content.endswith(b'\x03'*24)
    assert DATA_SAVED is True

def test_mixed_packets(data_handler):
    """Test handling both telemetry and camera packets together"""
    # Create telemetry packet
    telemetry_packet = TelemetryPacket(
        payload_type=0x10,
        batteries=[BatteryData(3.7, 0, 0, 0, 0)]*3,
        sensors=SensorsData(*([0]*10)),
        gps="TESTGPS"
    )
    
    # Create camera packet
    camera_packet = CameraPacket(0x11, b'\xFF'*122, 0, 42)
    
    # Process both
    data_handler.process_packet(create_telemetry_payload(telemetry_packet))
    data_handler.process_packet(create_camera_payload(camera_packet))
    
    # Verify both were saved
    assert os.path.exists(os.path.join(data_handler.telemetry_dir, "telemetry.csv"))
    assert os.path.exists(os.path.join(data_handler.image_dir, "camera_42.bin"))
    assert TELEMETRY_SAVED is True
    assert DATA_SAVED is True

def test_invalid_telemetry_length(data_handler, capsys):
    """Test handling of malformed telemetry packets"""
    short_payload = b'\x10' + b'\x00'*100  # 101 bytes required
    
    data_handler.process_packet(short_payload)
    
    captured = capsys.readouterr()
    assert "Expected 101 bytes" in captured.out
    assert not TELEMETRY_SAVED

def test_telemetry_csv_headers(data_handler):
    """Verify CSV headers match the new format"""
    test_packet = TelemetryPacket(
        payload_type=0x10,
        batteries=[BatteryData(0,0,0,0,0)]*3,
        sensors=SensorsData(*([0]*10)),
        gps=""
    )
    
    data_handler.process_packet(create_telemetry_payload(test_packet))
    
    with open(os.path.join(data_handler.telemetry_dir, "telemetry.csv")) as f:
        header = next(csv.reader(f))
    
    assert header == data_handler.global_headers
    assert len(header) == 26  # 25 numbers + 1 GPS string

def test_multiple_telemetry_packets(data_handler):
    """Test that multiple telemetry packets append to the same CSV"""
    packet1 = TelemetryPacket(
        payload_type=0x10,
        batteries=[BatteryData(1.0, 2.0, 3.0, 4.0, 5.0)]*3,
        sensors=SensorsData(*([1.0]*10)),
        gps="FIRST"
    )
    
    packet2 = TelemetryPacket(
        payload_type=0x10,
        batteries=[BatteryData(6.0, 7.0, 8.0, 9.0, 10.0)]*3,
        sensors=SensorsData(*([2.0]*10)),
        gps="SECOND"
    )
    
    data_handler.process_packet(create_telemetry_payload(packet1))
    data_handler.process_packet(create_telemetry_payload(packet2))
    
    telemetry_file = os.path.join(data_handler.telemetry_dir, "telemetry.csv")
    with open(telemetry_file, newline='') as f:
        rows = list(csv.reader(f))
    
    assert len(rows) == 3  # header + 2 data rows
    assert rows[1][0] == '1.0'  # First packet, first value
    assert rows[2][0] == '6.0'  # Second packet, first value
    assert rows[1][25] == 'FIRST'
    assert rows[2][25] == 'SECOND'
