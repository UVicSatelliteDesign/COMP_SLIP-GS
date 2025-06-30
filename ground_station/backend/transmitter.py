import json

from exceptions import MaxTransmissionReachedException, IncorrectPayloadTypeException, IncorrectCommandTypeException

PAYLOAD_TYPES = [
    ('Ping',                0b0000),
    ('Nominal',             0b0001),
    ('Low Power',           0b0010),
    ('Telemetry',           0b0011),
    ('Camera-1-End',        0b0100),
    ('Camera-1-MF',         0b0101),
    ('Camera-2-End',        0b0110),
    ('Camera-2-MF',         0b0111),
    ('Request Retransmittion',  0b1000),
    ('Error-CRC',           0b1001),
    ('Error-Duplication',   0b1010),
    ('Error-Low Power',     0b1011),
    ('Ack Rec Camera',      0b1100),
    ('Ack Rec Telemetry',   0b1101),
    ('Ack Rec Status',      0b1110),
    ('Ack Rec Error',       0b1111),
]

# Dictionary to store the type codes in binary
PAYLOAD_TYPE_DICT = {}
for type, code in PAYLOAD_TYPES:
    PAYLOAD_TYPE_DICT[type] = code.to_bytes(1, 'big')

MAX_TRANSMISSION_LIMIT = 3 #dummy value small for testing

#This class is used to send acknowledgements to the TTC.
class GroundStationTransmitter():
    gs_sequence_number = 0

    def __init__(self, seq_num=None, payload_type=None, payload_data=None, offset=None):
        self.payload_type = payload_type
        self.payload_data = payload_data
        self.offset = offset
        self.sequence_number = seq_num
        self.packet_sendonly_command = False

    def construct_packet(self, packet):
        if self.payload_type not in PAYLOAD_TYPE_DICT.values():
            raise IncorrectPayloadTypeException(f"Invalid payload type: {[type for type, code in PAYLOAD_TYPE_DICT.items() if code == self.payload_type]}")
        
        try:
            # Check if packet is a command? if yes then only add the payload sequence number and our sequence number
            if not self.packet_sendonly_command:
                assert len(self.payload_type) > 0, "Payload length zero, does not exist!"

                if(self.payload_type):
                    packet.append(self.payload_type)

                if self.offset:
                    # Handling camera data
                    # TODO add a payload with the number 1 or 2 based 
                    # on which type of camera packet the gs has received (camera 1 mf/end or camera 2 mf/end)?
                    if(self.payload_type == PAYLOAD_TYPE_DICT["Camera-1-End"]):
                        packet.append(b'1End')
                    if(self.payload_type == PAYLOAD_TYPE_DICT["Camera-1-MF"]):
                        packet.append(b'1MF')
                    if(self.payload_type == PAYLOAD_TYPE_DICT["Camera-2-End"]):
                        packet.append(b'2End')
                    if(self.payload_type == PAYLOAD_TYPE_DICT["Camera-2-MF"]):
                        packet.append(b'2MF')

                    assert len(self.offset) > 0, "Offset length zero, does not exists"
                    
                    #Camera Acknowledgement
                    payload_length = len(self.payload_data)
                    payload_len_byte = payload_length.to_bytes(1, byteorder='big')
                    packet.append(self.offset + payload_len_byte)
        
            # Add payload sequence number
            if(self.sequence_number):
                packet.append(self.sequence_number)

            # Finally add the GS sequence number
            gs_seq_num = GroundStationTransmitter.gs_sequence_number
            gs_seq_num_bytes = gs_seq_num.to_bytes(1, byteorder='big')
            packet.append(gs_seq_num_bytes)
            GroundStationTransmitter.gs_sequence_number += 1

        except AssertionError as e:
            print(f"Assertion error {e}")
        except Exception as e:
            print(f"Error occured {e}")

        return packet
    
    def ping(self):
        # initialize the ping packet
        packet = bytearray()
        packet.append(PAYLOAD_TYPE_DICT['Ping'])

        ping_packet = self.construct_packet(packet)

        self.transmit_func(ping_packet)

    # Check the commands queue in the main file for any incoming commands, if yes then send that command data type.
    def command(self, command):
        # command should be found in the PAYLOAD_TYPE_DICT
        if command not in PAYLOAD_TYPE_DICT.keys():
            raise IncorrectCommandTypeException(f'Invalid command type: {command}')
        
        self.packet_sendonly_command = True
        packet = bytearray()
        packet.append(PAYLOAD_TYPE_DICT[command])

        command_packet = self.construct_packet(packet)

        self.transmit_func(command_packet)

    def ack(self):
        # TODO construct an ACK packet
        pass

    def N_ack(self):
        # TODO construct an Negative ACK packet, is it needed?
        pass


    def transmit_func(self, data: bytearray):
        #TODO refactor retransmission should be able to check for break in communication
        packet_tx_attempts = 0
        while True:
            if packet_tx_attempts <= MAX_TRANSMISSION_LIMIT:
                try:
                    print(f'Packet {data} transmitted')
                    # TODO Transmit packet to GNU radio
                    break
                except Exception as e:  #TODO Communication broken re-establish connection and transmit packets again
                    print(f"Transmission failed: {e}")
                    packet_tx_attempts+=1
                    continue
            else:
                raise MaxTransmissionReachedException(f'Max tranmission limit reached: {packet_tx_attempts}')
