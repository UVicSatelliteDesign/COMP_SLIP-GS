




class GroundStationTransmitter():

    def __init__(self, payload, payload_type):
        self.payload = payload
        self.payload_type = payload_type



    '''packet structure -> 
    -> Sender address, 
    -> destination address, 
    -> data type(inject data type - Talk to Liam),
    -> payload,
    -> R bits
    '''

    #GNU radio.
    #sending a bunch of bits