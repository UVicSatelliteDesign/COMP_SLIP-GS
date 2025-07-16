#!/usr/bin/env python
from ground_station.backend.pass_app_layer import (
    handle_ping,
    handle_nominal,
    handle_low_power,
    handle_telemetry,
    handle_camera1_end,
    handle_camera1_mf,
    handle_camera2_end,
    handle_camera2_mf,
    handle_req_init_transmission,
    handle_error_peripheral,
    handle_error_dup,
    handle_error_lp,
    handle_ack_camera,
    handle_ack_telemetry,
    handle_ack_status,
    handle_ack_error
)

class ReceivedPacket():
    def __init__(self, data: bytes):
        '''
        Parses received binary data according to the following format:
        - First 4 bits: payload_type
        - Next bits (variable length): payload
        - Next 17 bits: offset (only for specific types)
        - Last 15 bits: sequence number
        '''
        self.payload_type = None
        self.payload = None
        self.offset = None
        self.sequence_number = None
        self.payload_length = 0

        try:
            # Total bits in data
            total_bits = len(data) * 8
            payload_bytes_length = 0

            # Ensure data length is valid (at least 4 bits payload_type + 15 bits sequence number)
            assert total_bits > 19, "Data too short for defined format"

            # Extract payload_type (first 4 bits)
            first_byte = data[0]
            self.payload_type = first_byte >> 4

            if self.payload_type in [0b0100, 0b0101, 0b0110, 0b0111]:
                # Calculate payload length in bits and bytes
                payload_bits_length = total_bits - 36  # 4 bits type + 17 offset + 15 seq
                payload_bytes_length = (payload_bits_length + 7) // 8

                if payload_bytes_length > 0:
                    payload_bits = int.from_bytes(data, 'big')
                    payload_bits >>= 32  # Strip 17 offset + 15 seq
                    payload_bits &= (1 << payload_bits_length) - 1
                    self.payload = payload_bits.to_bytes(payload_bytes_length, 'big')
                else:
                    self.payload = b''

                # Extract offset (17 bits before sequence number)
                last_four_bytes = int.from_bytes(data[-4:], 'big')
                self.offset = (last_four_bytes >> 15) & 0x1FFFF  # 17 bits

            else:
                # Only 4 bits (type) and 15 bits (seq); the rest is payload
                payload_bits_length = total_bits - 19  # 4 bits type + 15 bits seq
                payload_bytes_length = (payload_bits_length + 7) // 8

                if payload_bytes_length > 0:
                    payload_bits = int.from_bytes(data, 'big')
                    payload_bits >>= 15  # Strip 15-bit sequence number
                    payload_bits &= (1 << payload_bits_length) - 1
                    self.payload = payload_bits.to_bytes(payload_bytes_length, 'big')
                else:
                    self.payload = b''

                self.offset = None  # Offset does not exist for these types

            self.payload_length = payload_bytes_length
            # Extract sequence_number (last 15 bits)
            last_two_bytes = int.from_bytes(data[-2:], 'big')
            self.sequence_number = last_two_bytes & 0x7FFF  # Mask 15 bits

        except (AssertionError, ValueError, IndexError) as e:
            print(f"Initialization error: {e}")
            self.payload_type = None
            self.payload = None
            self.offset = None
            self.sequence_number = None

        # Should we append the payload_type, offset and sequence number directly to the TX_queue?

    def __repr__(self):
        return (f"ReceivedPacket(payload_type={self.payload_type}, length={self.payload_length}, offset={self.offset}, sequence_number={self.sequence_number}")
