#!/usr/bin/env python
import sys
import struct
import zlib

# Global Variables
ACK_FLAG = 0  # 2: No packet received, 1: Acknowledge packet, 0: Incorrect packet
PAYLOAD_TYPE_LIST = ['POWER', 'PICTURE', 'RESET']  # Data type of the payload (4-bit number representation in packet header)
HEADER_FORMAT = '!BHI'  # flag (B), type_id (H), length (I) (Always big endian)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
G = 0b1001  # G(x)= X^3 + 1 Generator for CRC parity checking

class GroundStationReceiver():
    def __init__(self, data):
        '''
        Segment of data is taken from the physical link and passed up to the 
        GroundStationReceiver class. This segment of data (PackageHeader,Payload)
        is then parsed and stored within this class. Furthermore, the use of flags
        allows for the state of the received packet to be shared globaly. Finally, a 
        CRC parity checker is used to ensure data integrity.
        '''
        try:
            assert len(data) >= HEADER_SIZE, "Insufficient data length for header"
            self.package_header = PackageHeader.unpack(data[:HEADER_SIZE])
            assert len(data[HEADER_SIZE:]) == self.package_header.length, "Payload length mismatch"
            self.payload = data[HEADER_SIZE:]
        except AssertionError as e:
            print(f"Error initializing GroundStationReceiver: {e}")
            self.package_header = None
            self.payload = None

    def check_parity(self):
        '''
        This function parses through the data in the packet and ensures that parity 
        checking is being computed correctly. Additionally, if it is, the function will send 
        a message to the transmitter class asking it to send an acknowledge. Otherwise, this 
        function does not ask the transmitter class to acknowledge.
        '''
        if not self.payload or not self.package_header:
            print("No valid payload or header available.")
            return False

        crc_from_payload = struct.unpack('!I', self.payload[-4:])[0]  # Last 4 bytes are CRC
        data_without_crc = self.payload[:-4]

        computed_crc = zlib.crc32(data_without_crc)

        try:
            assert crc_from_payload == computed_crc, "CRC mismatch!"
            global ACK_FLAG
            ACK_FLAG = 1  # TODO: Pass ACK to transmitter class
            return True
        except AssertionError as e:
            print(f"CRC check failed: {e}")
            ACK_FLAG = 0  # TODO: Pass Error to transmitter class
            return False

class PackageHeader():
    def __init__(self, flag=0, type_id=0, length=0):
        try:
            assert 0 <= type_id < len(PAYLOAD_TYPE_LIST), "Invalid type_id!"
            assert length >= 0, "Length must be non-negative"
        except AssertionError as e:
            print(f"PackageHeader initialization error: {e}")
            self.type_id = None
            self.length = None
            self.flag = None
            return

        self.type_id = PAYLOAD_TYPE_LIST[type_id]  # Type id may range from 0 to len(PAYLOAD_TYPE_LIST)-1 inclusive
        self.length = length
        self.flag = flag

    @classmethod
    def unpack(cls, data):
        # Converts raw bytes into a structured object, and enforces data integrity.
        try:
            if len(data) < HEADER_SIZE:
                raise ValueError("Data too short for header")
            flag, type_id, length = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
            return cls(flag, type_id, length)
        except struct.error as e:
            print(f"Struct unpacking error: {e}")
            return cls()
