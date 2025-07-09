#!usr/bin/env python3
import sys
import os
import threading
from queue import Queue, Empty


from ground_station.backend.transmitter import GroundStationTransmitter, PAYLOAD_TYPE_DICT
from ground_station.backend.receiver import ReceivedPacket
from ground_station.backend.Binary_CSV_Handler import DataHandler
from ground_station.backend.bin_to_jpeg import BinToJPEG
from ground_station.backend.graph_plot import ExpandingGraph

ST_IDLE = 1
ST_LOST = 0
ST_RETRANSMISSION = 2

CURRENT_STATE = ST_LOST

# Initializing the TX and RX queues 
TX_queue = Queue()
RX_queue = Queue()

gs_tx = None
gs_rx = None
ping_ack_recieved = False

# variables which keep on changing per packet.
payload_type = None
payload_data = None
payload_length = None
seq_num = None
offset = None
data_handler = None
bin_to_jpeg = None
graph_plot = None

# TODO: Websocket for establishing connection to GNU.
# TODO: Will need multithreading, concurrent tasks (recieve, send, process)
# TODO: Able to change GNU configs through main file.
# TODO: Add global vars when socket open -> FREQ, SAMPLE_RATE.

def main():
  # Start by pinging the satellite until the satellite gives us an Acknowledgement
  while(True):
    if CURRENT_STATE == 0:
      # ping the satellite
      gs_tx.ping()
      #ACK should be added to the Receiver Queue by now
      try:
        data = RX_queue.get(timeout=3) # Wait for 3 seconds before raising a Empty exception, data might becoming in
        gs_rx = ReceivedPacket(data)
        if(gs_rx.payload_type == PAYLOAD_TYPE_DICT['Ping']):
          ping_ack_recieved = True
          print("Got Ping acknowledgement")
          break
      except Empty:
        print("Queue empty")
      CURRENT_STATE = ST_IDLE
    
    # Assuming that the connection is correctly established.
    if CURRENT_STATE == 1:
      # Logic for transmitting data
      data = RX_queue.get(timeout=3)
      # Packet has been received and parsed
      gs_rx = ReceivedPacket(data)
      payload_type = gs_rx.payload_type
      payload_data = gs_rx.payload
      payload_length = gs_rx.payload_length or 0
      seq_num = gs_rx.sequence_number
      offset = gs_rx.offset

      # Init transmitter
      gs_tx = GroundStationTransmitter(payload_type, payload_data, payload_length, seq_num, offset)

      # Data handling
      if(payload_type in [PAYLOAD_TYPE_DICT['Telemetry'],
                          PAYLOAD_TYPE_DICT['Camera-1-End'],
                          PAYLOAD_TYPE_DICT['Camera-1-MF'],
                          PAYLOAD_TYPE_DICT['Camera-2-End'],
                          PAYLOAD_TYPE_DICT['Camera-2-MF']]):
        # We have recieved telemetry/image data here pass it to the handler
        data_handler = DataHandler(payload_type, payload_data)
        
        # process data and create .pkl and .csv files.
        data_handler.process_packet()

      # Check if images directory exists and is not empty
      if os.path.isdir('images') and os.listdir('images'):
        bin_to_jpeg = BinToJPEG()
      
      # Stubs accroding to the init for graph_plot def __init__(self, x_file, y_file, x_label, y_label, title):
      x_file = ""
      y_file = ""
      x_label = ""
      y_label = ""
      # Check if telemetry directory exists and is not empty
      if os.path.isdir('telemetry') and os.listdir('telemetry'):
        graph_plot = ExpandingGraph(x_file, y_file, x_label, y_label)

  return 0

if __name__=="__main__":
  exit(main())