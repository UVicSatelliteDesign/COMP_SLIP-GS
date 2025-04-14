import struct

PAYLOAD_TYPE_LIST = [
    0b0000,  # Ping
    0b0001,  # Nominal
    0b0010,  # Low Power
    0b0011,  # Telemetry
    0b0100,  # Camera-1-End
    0b0101,  # Camera-1-MF
    0b0110,  # Camera-2-End
    0b0111,  # Camera-2-MF
    0b1000,  # Request Retransmission
    0b1001,  # Error - CRC
    0b1010,  # Error - Duplication
    0b1011,  # Error - Low Power
    0b1100,  # Ack. Rec. Camera
    0b1101,  # Ack. Rec. Telemetry
    0b1110,  # Ack. Rec. Status
    0b1111,  # Ack. Rec. Error
]

MAX_TRANSMISSION_LIMIT = 3 #dummy value small for testing


class GroundStationTransmitter():
    sequence_number = 0

    def __init__(self, payload_type, payload_data=None, offset=None, command=None):
        self.payload_type = payload_type
        self.payload_data = payload_data
        self.offset = offset
        self.command = command
        self.__class__.sequence_number+=1
    

    def construct_packet(self):
        if self.payload_type not in PAYLOAD_TYPE_LIST:
            raise IncorrectPayloadTypeException(f"Invalid payload type: {self.payload_type}")
        
        #initialize byte array
        packet = bytearray()

        packet.extend(self.payload_type)

        #TODO add try-assert blocks
        try:
            if self.payload_data:
                #sending acknowledgement
                #attach payload_data to packet
                assert len(self.payload_type) > 0, "Payload length zero, does not exist!"
                packet.extend(self.payload)
                if self.offset:
                    assert len(self.offset) > 0, "Offset length zero, does not exists"
                    #Camera Acknowledgement
                    packet.extend(self.offset)
            
            if not self.payload_data and self.cmd:
                #Sending command no payload_data
                packet.extend(self.command)
        except AssertionError as e:
            print(f"Assertion error {e}")
        except Exception as e:
            print(f"Error occured {e}")
        
        # Add sequence number at the end

        #first we need to calculate the number of bytes the sequence number will take in binary representation
        num_bytes = ((self.sequence_number.bit_length()) + 7) // 8  
        seq_num_bytes = self.sequence_number.to_bytes(num_bytes, byteorder='big')

        packet.append(seq_num_bytes)

        return packet


    def transmit_packet(self, transmit_func):
        '''
        Transit the constructed packet by calling the transmit function
        
        transmit_func accepts a bytes object (nned transmit_func from GNU class)
        '''
        try:
            packet = self.construct_packet()
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
    print('packet tranmitted')

# ================================================  testing code
def test_groundstation():
    gstx = GroundStationTransmitter(0b0001)
    print(f'Sequence number {gstx.sequence_number}')
    gstx.construct_packet() #shows TypeError
    gstx.transmit_packet()

# prints out sequence numbers till ten
for i in range(10):
    test_groundstation()
    i+=1

class IncorrectPayloadTypeException(Exception):
    '''Raised when the payload is not of the correct type'''
    pass

class MaxTransmissionReachedException(Exception):
    '''Raised when packet transmission limit is exceeded'''
    pass