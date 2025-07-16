import os
import csv
import pytest
from dataclasses import dataclass

# Test data structures
@dataclass
class CameraPacket:
    payload_type: int  # 0x11 or 0x12
    identifier: str    # 'A', 'B', etc.
    data: bytes        # image data
    offset: int        # byte offset
    seq_num: int       # sequence number

@dataclass
class TelemetryPacket:
    payload_type: int  # 0x10
    data: str          # comma-separated values
    seq_num: int       # sequence number

@pytest.fixture
def data_handler(tmp_path):
    """Fixture that provides a DataHandler instance with temp directories"""
    image_dir = tmp_path / "images"
    telemetry_dir = tmp_path / "telemetry"
    db_dir = tmp_path / "database"
    handler = DataHandler(
        data_type="both",
        image_dir=str(image_dir),
        telemetry_dir=str(telemetry_dir)
    )
    return handler

def create_camera_payload(packet: CameraPacket) -> bytes:
    """Helper to create camera payload bytes"""
    return (
        packet.payload_type.to_bytes(1, 'big') +  # header byte
        packet.identifier.encode('ascii') +       # 1 byte identifier
        packet.data +                            # image data
        packet.offset.to_bytes(3, 'big') +       # offset
        packet.seq_num.to_bytes(2, 'big')        # sequence number
    )

def create_telemetry_payload(packet: TelemetryPacket) -> bytes:
    """Helper to create telemetry payload bytes"""
    return (
        packet.payload_type.to_bytes(1, 'big') +  # header byte
        packet.data.encode('ascii') +             # CSV data
        packet.seq_num.to_bytes(2, 'big')         # sequence number
    )

# ==============================================
# TELEMETRY TESTS (2-3 packets)
# ==============================================

def test_telemetry_storage(data_handler):
    """Test storing 3 telemetry packets in database"""
    packets = [
        TelemetryPacket(0x10, "23.5,42.1,1002", 1),
        TelemetryPacket(0x10, "24.0,41.9,1005", 2),
        TelemetryPacket(0x10, "22.8,42.3,1001", 3),
    ]

    # Process all packets
    for packet in packets:
        data_handler.process_packet(create_telemetry_payload(packet))

    # Verify combined telemetry file
    telemetry_file = os.path.join(data_handler.telemetry_dir, "telemetry.csv")
    with open(telemetry_file, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    assert len(rows) == 4  # header + 3 data rows
    assert rows[0] == ["Field_0", "Field_1", "Field_2"]
    assert rows[1] == ["23.5", "42.1", "1002"]
    assert rows[2] == ["24.0", "41.9", "1005"]
    assert rows[3] == ["22.8", "42.3", "1001"]

    # Verify individual field files
    for i, field in enumerate(["Field_0", "Field_1", "Field_2"]):
        field_file = os.path.join("database", f"{field}.csv")
        with open(field_file, 'r') as f:
            reader = csv.reader(f)
            field_rows = list(reader)
        
        assert len(field_rows) == 4  # header + 3 values
        assert field_rows[0] == [field]
        assert field_rows[1][0] == rows[1][i]
        assert field_rows[2][0] == rows[2][i]
        assert field_rows[3][0] == rows[3][i]

    assert TELEMETRY_SAVED is True

# ==============================================
# CAMERA TESTS (5 packets with Camera1-MF and Camera1-End)
# ==============================================

def test_camera_storage(data_handler):
    """Test storing 5 camera packets with mixed payload types"""
    packets = [
        CameraPacket(0x11, "A", b'\x01'*122, 0, 1),    # Camera1-MF
        CameraPacket(0x11, "A", b'\x02'*122, 122, 1),  # Camera1-MF
        CameraPacket(0x11, "A", b'\x03'*122, 244, 1),  # Camera1-MF
        CameraPacket(0x11, "A", b'\x04'*122, 366, 1),  # Camera1-MF
        CameraPacket(0x12, "A", b'\x05'*24, 488, 1),   # Camera1-End (24 bytes)
    ]

    # Process all packets
    for packet in packets:
        data_handler.process_packet(create_camera_payload(packet))

    # Verify the output file
    output_file = os.path.join(data_handler.image_dir, "A_1.bin")
    assert os.path.exists(output_file)
    
    # Check file content (should be concatenation of all data chunks)
    expected_data = b''.join([p.data for p in packets])
    with open(output_file, 'rb') as f:
        assert f.read() == expected_data

    # Verify the last packet was handled correctly
    assert data_handler.recent_files["A"] == output_file
    assert DATA_SAVED is True
    assert DataHandler.sequence_number == 2  # Next sequence number

# ==============================================
# EDGE CASE TESTS
# ==============================================

def test_camera_end_packet_short(data_handler, capsys):
    """Test Camera1-End packet with exactly 24 bytes"""
    packet = CameraPacket(0x12, "B", b'\xAA'*24, 0, 2)
    data_handler.process_packet(create_camera_payload(packet))
    
    output_file = os.path.join(data_handler.image_dir, "B_2.bin")
    assert os.path.exists(output_file)
    with open(output_file, 'rb') as f:
        assert f.read() == b'\xAA'*24
    
    captured = capsys.readouterr()
    assert "✅ Image saved" in captured.out
    assert "Camera processing error" not in captured.out

def test_mixed_packet_types(data_handler):
    """Test mixed telemetry and camera packets"""
    packets = [
        TelemetryPacket(0x10, "1.0,2.0", 1),
        CameraPacket(0x11, "C", b'\x01'*122, 0, 1),
        TelemetryPacket(0x10, "3.0,4.0", 2),
        CameraPacket(0x12, "C", b'\x02'*24, 122, 1),
    ]

    for packet in packets:
        data_handler.process_packet(
            create_telemetry_payload(packet) if packet.payload_type == 0x10 
            else create_camera_payload(packet)
        )

    # Verify both telemetry and camera data were saved
    assert os.path.exists(os.path.join(data_handler.telemetry_dir, "telemetry.csv"))
    assert os.path.exists(os.path.join(data_handler.image_dir, "C_1.bin"))
    assert DATA_SAVED is True
    assert TELEMETRY_SAVED is True
