import socket
import os
from queue import Queue, Empty
from PyQt6.QtCore import QObject, pyqtSignal
import asyncio


from ground_station.backend.transmitter import GroundStationTransmitter, PAYLOAD_TYPE_DICT
from ground_station.backend.receiver import ReceivedPacket
from ground_station.backend.Binary_CSV_Handler import DataHandler
from ground_station.backend.bin_to_jpeg import BinToJPEG
from ground_station.backend.graph_plot import ExpandingGraph
from ground_station.backend.exceptions import MaxTransmissionReachedException, IncorrectCommandTypeException, IncorrectPayloadTypeException
from ground_station.backend.command_queue_state import command_queue

# TODO: socket connection for establishing connection to GNU.
# TODO: Able to change GNU configs through main file.
# TODO: Add global vars when socket open -> FREQ, SAMPLE_RATE.

class BackendWorkerMain(QObject):
  ping_ack_received = pyqtSignal()
  error_occured = pyqtSignal(str)
  packet_recieved = pyqtSignal(str)

  def __init__(self):
    super().__init__()
    self._running = True
    self.max_transmission_limit = 3
    # Init the socket connection
    self.gnu_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.gnu_socket.connect(("127.0.0.1", 9999))  # will need to add actual HOST and PORT

    self.gs_tx = GroundStationTransmitter()
    self.gs_rx = None
    self.ping_ack_recieve = False

    # Packet info parsed
    self.payload_type = None
    self.payload_data = None
    self.payload_length = None
    self.seq_num = None
    self.offset = None

    # Data handlers
    self.data_handler = None
    self.self.bin_to_jpeg = None
    self.graph_plot = None

    # Some empty variables in case we need them later
    self.freq = None
    self.sample_rate = None


  def stop(self):
    self._running = False

  
  def run(self):
    while self._running:
      # Check for ping acknowledgement
      while not self.ping_ack_received:
          try:
            # send packet to gnu
            ping_packet = self.gs_tx.ping()
            self.gnu_socket.send(ping_packet)

            # wait for ping
            data = self.gnu_socket.recv(1024)
            if not data:
              continue
            gs_rx = ReceivedPacket(data)
            if gs_rx.payload_type == 0b0000:
              self.ping_ack_received = True # Transition to idle state
            else:
              continue
          except socket.timeout():
            continue


      data = self.gnu_socket.recv(1024)
      if not data:
        continue

      # Send ack
      self.gs_rx = ReceivedPacket(data)

      self.gs_tx.payload_type = self.gs_rx.payload_type
      self.gs_tx.payload_data = self.gs_rx.payload
      self.gs_tx.payload_length = self.gs_rx.payload_length
      self.gs_tx.sequence_number = self.gs_rx.sequence_number
      
      if self.gs_rx.offset:
        self.gs_tx.offset = self.gs_rx.offset

      ack_packet = self.gs_tx.ack()
      self.gnu_socket.send(ack_packet)

      # DATA HANDLING
      self.payload_type = self.gs_rx.payload_type
      self.payload_data = self.gs_rx.payload
      self.payload_length = self.gs_rx.payload_length
      self.seq_num = self.gs_rx.sequence_number
      
      if self.gs_rx.offset:
        self.offset = self.gs_rx.offset

      if self.payload_type in [PAYLOAD_TYPE_DICT['Telemetry'],
                            PAYLOAD_TYPE_DICT['Camera-1-End'],
                            PAYLOAD_TYPE_DICT['Camera-1-MF'],
                            PAYLOAD_TYPE_DICT['Camera-2-End'],
                            PAYLOAD_TYPE_DICT['Camera-2-MF']]:
        
        self.data_handler = DataHandler(self.payload_type)
        self.data_handler.process_packet() # backend process, will create some directories and files

        jpeg_filename = ""
        # Check if images directory exists and is not empty
        if os.path.isdir('images') and os.listdir('images'):
          self.bin_to_jpeg = BinToJPEG()
          self.bin_to_jpeg.extract_jpg_image(jpeg_filename)
        
        # Stubs according to the init for graph_plot def __init__(self, x_file, y_file, x_label, y_label, title):
          x_file = ""
          y_file = ""
          x_label = ""
          y_label = ""
          # Check if telemetry directory exists and is not empty
          if os.path.isdir('telemetry') and os.listdir('telemetry'):
            graph_plot = ExpandingGraph(x_file, y_file, x_label, y_label)

      if not command_queue.empty():
        command = command_queue.get()
        command_packet = self.gs_tx.command(command)
        # send command packet
        self.gnu_socket.send(command_packet)
        # Check for acknowledgement recieved and retransmit data if not recieved.
        while True:
          self.gnu_socket.settimeout(5)
          if self.max_transmission_limit == 3:
            self.ping_ack_received = False
            break
          try:
            data = self.gnu_socket.recv(1024)
            if not data:
              continue
            else:
              self.max_transmission_limit = 0
          except self.gnu_socket.timeout:
            self.max_transmission_limit+=1
            continue
      
      self.gnu_socket.settimeout(0) # Set the socket timeout to zero again
    
