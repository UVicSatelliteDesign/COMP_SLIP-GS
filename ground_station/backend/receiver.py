#!/usr/bin/env python
import sys
import struct

"""
TODO: Define what type of data is being sent {Ack, Status}
TODO: Ensure proper testing 
"""

class GroundStationReceiver():
    def __init__(self, args):
        self.args = args
        self.package_header = PackageHeader()

    # TODO: Listen for bytes(packets)
    def recieve_payload(self):
        '''
        Establish connection -> Recieve data, identify type of payload
        '''
        # For demonstration, simulate receiving a packet.
        dummy_payload = b"This is a test payload"
        header = PackageHeader(flag=0x01, type_id=0x0001, length=len(dummy_payload))
        # Return full packet as header + payload.
        return header.pack() + dummy_payload

    def parse_packet(self, packet):
        '''
        Process data; raise errors if something wrong
        '''
        # Extract header.
        header = PackageHeader.unpack(packet)
        # Extract payload.
        payload = packet[PackageHeader.HEADER_SIZE:]
        if len(payload) != header.length:
            raise ValueError("Payload length mismatch")
        return header, payload

    def send(self, response_payload):
        '''
        Flags, acknowledgement, other stuff...
        '''
        # Create response header.
        header = PackageHeader(flag=0x02, type_id=0x0002, length=len(response_payload))
        packet = header.pack() + response_payload
        # In a full implementation, the packet would be transmitted.
        return packet

class PackageHeader():
    HEADER_FORMAT = '!BHI'  # flag (B), type_id (H), length (I)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, flag=0, type_id=0, length=0):
        self.flag = flag
        self.type_id = type_id
        self.length = length

    def pack(self):
        # Pack the header fields into bytes.
        return struct.pack(PackageHeader.HEADER_FORMAT, self.flag, self.type_id, self.length)

    @classmethod
    def unpack(cls, data):
        # Converts raw bytes into a structured object, and enforced data integrity.
        if len(data) < cls.HEADER_SIZE:
            raise ValueError("Data too short for header")
        flag, type_id, length = struct.unpack(cls.HEADER_FORMAT, data[:cls.HEADER_SIZE])
        return cls(flag, type_id, length)

def acknowledgement():
    # Return an acknowledgement payload.
    return b"ACK"

def main():
    """
    This is the main function for the ReceiverClass module.
    """
    args = sys.argv[1:]
    receiver = GroundStationReceiver(args)
    
    # Simulate receiving a packet.
    packet = receiver.recieve_payload()
    
    try:
        header, payload = receiver.parse_packet(packet)
        print("Received payload:", payload)
    except Exception as e:
        print("Error parsing packet:", e)
    
    # Generate and send an acknowledgement.
    ack_payload = acknowledgement()
    ack_packet = receiver.send(ack_payload)
    print("Acknowledgement packet sent:", ack_packet)
