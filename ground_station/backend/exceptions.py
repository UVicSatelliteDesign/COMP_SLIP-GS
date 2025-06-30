class IncorrectPayloadTypeException(Exception):
    '''Raised when the payload is not of the correct type'''
    pass

class MaxTransmissionReachedException(Exception):
    '''Raised when packet transmission limit is exceeded'''
    pass

class IncorrectCommandTypeException(Exception):
    '''Raised when an invalid command is attempted for transmittion'''
    pass