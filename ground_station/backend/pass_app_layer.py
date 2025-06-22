# This file acts as a middleware to pass data to the handlers
import queue

GLOBAL_TX_QUEUE = queue.Queue()

def handle_ping(payload: bytes):
    # Send ping acknowledgement with ping data type.
    pass # TODO

def handle_nominal(payload: bytes):
    pass # TODO

def handle_low_power(payload: bytes):
    pass # TODO

def handle_telemetry(payload: bytes):
    pass # TODO

def handle_camera1_end(payload: bytes):
    pass # TODO

def handle_camera1_mf(payload: bytes):
    pass # TODO

def handle_camera2_end(payload: bytes):
    pass # TODO

def handle_camera2_mf(payload: bytes):
    pass # TODO

def handle_req_init_transmission(payload: bytes):
    pass # TODO

def handle_error_peripheral(payload: bytes):
    pass # TODO

def handle_error_dup(payload: bytes):
    pass # TODO

def handle_error_lp(payload: bytes):
    pass # TODO

def handle_ack_camera(payload: bytes):
    pass # TODO

def handle_ack_telemetry(payload: bytes):
    pass # TODO

def handle_ack_status(payload: bytes):
    pass # TODO

def handle_ack_error(payload: bytes):
    pass # TODO
