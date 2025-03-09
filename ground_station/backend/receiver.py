#!/usr/bin/env python
import sys
import struct
# Import zlib

"""
TODO: Define what type of data is being sent {Ack, Status}
TODO: Ensure proper testing 
TODO: Add a couple of asserts (try catch blocks)
TODO: Implement CRC (Data integrity), 
TODO: If packet is received, either send acknowledge or send error, 
"""

# Global Variables
ACK_FLAG=0 # 2: No packet received, 1: Acknowledge packet, 0: Incorrect packet
PAYLOAD_TYPE_LIST = ['POWER', 'PICTURE', 'RESET']  # Data type in the payload  
G = 1001 # G(x)= X^3 + 1 Generator for CRC parity checking 

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
        Process data; raise errors if something wrong, if not then set flag to indicate 
        that acknowledgment should be sent.
        '''
        # Extract header.
        header = PackageHeader.unpack(packet)
        # Extract payload.
        payload = packet[PackageHeader.HEADER_SIZE:]
        if len(payload) != header.length:
            raise ValueError("Payload length mismatch")
        return header, payload

    # TODO: Remove this routine
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
    HEADER_FORMAT = '!BHI'  # flag (B), type_id (H), length (I) (ALways do big endian)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    # TODO: put flag at the end 
    def __init__(self, flag=0, type_id=0, length=0):
        self.flag = flag
        self.type_id = type_id
        self.length = length

    # TODO: Remove this 
    def pack(self):
        # Pack the header fields into bytes.
        # TODO: make flag at the end of package header
        return struct.pack(PackageHeader.HEADER_FORMAT, self.type_id, self.length, self.flag)

    @classmethod
    def unpack(cls, data):
        # Converts raw bytes into a structured object, and enforced data integrity.
        if len(data) < cls.HEADER_SIZE:
            raise ValueError("Data too short for header")
        flag, type_id, length = struct.unpack(cls.HEADER_FORMAT, data[:cls.HEADER_SIZE])
        return cls(flag, type_id, length)

# TODO: Remove main, receive function
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
