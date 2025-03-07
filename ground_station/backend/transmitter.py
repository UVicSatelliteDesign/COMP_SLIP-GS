'''Imports'''
import zlib

'''Global variables'''
PAYLOAD_TYPE_LIST = ['POWER', 'PICTURE', 'RESET'] 
SENDER_ADDRESS = ""
DESTINATION_ADDRESS = ""
MAX_TRANSMISSION_LIMIT = 30 #dummy value



class GroundStationTransmitter():

    def __init__(self, payload, payload_type):
        self.payload = payload
        self.payload_type = payload_type #Identifies the command type



    
    def construct_packet(self):

        # TODO check if payload_type is in the 3-bit list
        if self.payload_type not in PAYLOAD_TYPE_LIST:
            raise IncorrectPayloadTypeException

        # Ideal Payload structure(All other fields will have default values)

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

        payload_length = len(self.payload)

        #Contains metadata about the payload
        payload_header = self.payload["header"]

        #Calculate Checksum
        crc_value = self.payload["r_bits"]
        crc_check_sum = self.check_sum(crc_value)

        #Construct packet
        packet = bytes([self.header, self.payload_type, payload_length, crc_check_sum, self.payload])

        return packet

        
    def check_sum(self, data: bytes):
        '''
        Computes a 32-bit crc checksum for the given stream of bytes
        :return: A 32-bit integer representing the CRC32 checksum.
        '''

        return zlib.crc32(data)
    
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