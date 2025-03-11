'''Imports'''
from zlib import crc32
import json

'''Global variables'''
PAYLOAD_TYPE_LIST = [b"POWER", b"PICTURE", b"RESET"] 
MAX_TRANSMISSION_LIMIT = 5 #dummy value small for testing



class GroundStationTransmitter():

    def __init__(self, payload, payload_type):
        self.payload = payload
        self.eof_bit = 0 
        self.payload_type = payload_type #Identifies the command type
        self.src_address = b"source address"
        self.dst_address = b"destination address"
    
    def construct_packet(self):
        # Ideal Payload structure BYTES(All other fields will have default values)

        #Acknowleadgement ACK -> Acknowledged, NACK -> Negative Acknowledgement

        #if command type - Power Command
        '''
        {
        "switch_power_mode" : NOMINAL/LOW/READY,
        "ackowledgement": ACK/NACK 
        }
        '''

        #if command type - Take Picture
        '''
        {
        "take_picture": True,
        "resolution-set": 720p/480p,
        "ackowledgement": ACK/NACK
        }
        '''
         #if command type - Reset or Change Transmission Frequency
        '''
        {
        "new_transmission_freq": <new frequency>,
        "reset_obc/subsystems": none
        "ackowledgement": ACK/NACK
        }
        '''
        # TODO check if payload_type is in the 3-bit list
        if self.payload_type not in PAYLOAD_TYPE_LIST:
            raise IncorrectPayloadTypeException
        
        payload_length = len(self.payload)

        #Construct packet header (Metadata)
        packet_header = 0XAA  #Preamble(denotes the starting of a packet)
        packet_header += self.payload_type
        packet_header += payload_length
        packet_header += self.src_address
        packet_header += self.dst_address

        #Calculate Checksum on the entire payload
        crc_check_sum = self.check_sum(self.payload_type + self.payload)

        #Construct packet
        packet = bytes([packet_header, self.payload, crc_check_sum, self.eof_bit])

        return packet

        
    def check_sum(self, data: bytes):
        '''
        Computes a 32-bit crc checksum for the given stream of bytes
        :return: A 32-bit integer representing the CRC32 checksum.
        '''

        return crc32(data)
    
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