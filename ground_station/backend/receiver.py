#!/usr/bin/env python
import sys
import struct

class GroundStationReceiver():
    def __init__(self, data):
        '''
        Receives data from the physical link and parses it into the header, payload, and sequence number.
        The CRC check is assumed to be done at a lower layer (GNU Data Link).
        '''
        try:
            assert len(data) >= 4, "Insufficient data length for payload"

            self.length = struct.unpack('!B', data[:1])[0]  # 1 byte (length of payload)
            self.address = struct.unpack('!B', data[1:2])[0]  # 1 byte (address for payload routing)

            assert len(data) == self.length + 4, "Data length does not match payload length"

            self.payload = data[2:2+self.length]  # Payload data
            self.sequence_number = struct.unpack('!H', data[-2:])[0]  # Last 2 bytes as sequence number

        except AssertionError as e:
            print(f"Initialization error: {e}")
            self.length, self.address, self.payload, self.sequence_number = None, None, None, None
            # TODO: send a not ACK message to transmitter?

    def pass_to_application(self):
        '''
        Passes payload to the application layer according to the address field.
        '''
        if self.address is None or self.payload is None:
            print("Invalid packet data. Nothing to pass to application layer.")
            return

        if self.address == 0b0000:
            handle_ping(self.payload) # TODO:
        elif self.address == 0b0001:
            handle_nominal(self.payload) # TODO:
        elif self.address == 0b0010:
            handle_low_power(self.payload) # TODO:
        elif self.address == 0b0011:
            handle_telemetry(self.payload) # TODO:
        elif self.address == 0b0100:
            handle_camera1_end(self.payload) # TODO:
        elif self.address == 0b0101:
            handle_camera1_mf(self.payload) # TODO:
        elif self.address == 0b0110:
            handle_camera2_end(self.payload) # TODO:
        elif self.address == 0b0111:
            handle_camera2_mf(self.payload) # TODO:
        elif self.address == 0b1000:
            handle_retransmission(self.payload) # TODO:
        elif self.address == 0b1001:
            handle_error_crc(self.payload) # TODO:
        elif self.address == 0b1010:
            handle_error_dup(self.payload) # TODO:
        elif self.address == 0b1011:
            handle_erro_lp(self.payload) # TODO:
        elif self.address == 0b1100:
            handle_ack_camer(self.payload) # TODO:
        elif self.address == 0b1101:
            handle_ack_telemetry(self.payload) # TODO:
        elif self.address == 0b1110:
            handle_ack_status(self.payload) # TODO:
        elif self.address == 0b1111:
            handle_ack_error(self.payload) # TODO:
        else:
            print(f"Unknown address field: {self.address}. Payload not routed.")
