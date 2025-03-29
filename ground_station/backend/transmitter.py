import struct

PAYLOAD_TYPE_LIST = [
    "0000",  # Ping
    "0001",  # Nominal
    "0010",  # Low Power
    "0011",  # Telemetry
    "0100",  # Camera-1-End
    "0101",  # Camera-1-MF
    "0110",  # Camera-2-End
    "0111",  # Camera-2-MF
    "1000",  # Request Retransmission
    "1001",  # Error - CRC
    "1010",  # Error - Duplication
    "1011",  # Error - Low Power
    "1100",  # Ack. Rec. Camera
    "1101",  # Ack. Rec. Telemetry
    "1110",  # Ack. Rec. Status
    "1111",  # Ack. Rec. Error
]
MAX_TRANSMISSION_LIMIT = 5 #dummy value small for testing


class GroundStationTransmitter():

    def __init__(self, payload, payload_type):
        self.payload = payload
        self.payload_type = payload_type #Identifies the command type
        #Example 2-bit source and destination addresses.
        self.src_address = b"\x00\x01"    
        self.dst_address = b"\x01\x00"
        self.preamble = 0XAA

    
    def construct_packet(self):
        if self.payload_type not in PAYLOAD_TYPE_LIST:
            raise IncorrectPayloadTypeException(f"Invalid payload type: {self.payload_type}")

        payload_length = len(self.payload)

        # # Use struct to pack the fixed fields
        header = struct.pack(
            ">BBBH2s2s",  # Big-endian format: preamble, type, length, reserved, src, dst
            self.preamble,
            self.payload_type,
            payload_length,
            0x00,               # Reserved bits (optional)
            self.src_address,
            self.dst_address
        )

        # # Final packet: header + payload + footer
        packet = header + self.payload

        return packet

    def transmit_packet(self, transmit_func):
        '''
        Transit the constructed packet by calling the transmit function
        
        transmit_func accepts a bytes object
        '''
        packet = self.construct_packet()
        try:
            transmit_func(packet)
        except MaxTransmissionReachedException as e:
            print(f"Transmission failed after maximum attempts: {e}")
        except IncorrectPayloadTypeException as e:
            print(f"Incorrect payload type {e}")


def transmit_func(data: bytes):
    packet_tx_attempts = 0
    while True:
        if packet_tx_attempts <= MAX_TRANSMISSION_LIMIT:
            try:
                # TODO Transmit packet to GNU radio -- raises an Exception
                break
            except Exception as e:
                print(f"Transmission failed: {e}")
                packet_tx_attempts+=1
                continue
        else:
            raise MaxTransmissionReachedException
        

class IncorrectPayloadTypeException(Exception):
    '''Raised when the payload is not of the correct type'''
    pass

class MaxTransmissionReachedException(Exception):
    '''Raised when packet transmission limit is exceeded'''
    pass