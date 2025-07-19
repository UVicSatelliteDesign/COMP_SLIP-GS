import socket
import os
from queue import Queue, Empty
from PyQt6.QtCore import QObject, pyqtSignal
import asyncio


from ground_station.backend.transmitter import GroundStationTransmitter, PAYLOAD_TYPE_DICT
from ground_station.backend.receiver import ReceivedPacket
from ground_station.backend.Binary_CSV_Handler import DataHandler
from ground_station.backend.bin_to_jpeg import BinToJPEG
from ground_station.backend.exceptions import MaxTransmissionReachedException, IncorrectCommandTypeException, IncorrectPayloadTypeException
from ground_station.backend.command_queue_state import command_queue

# TODO: socket connection for establishing connection to GNU.
# TODO: Able to change GNU configs through main file.
# TODO: Add global vars when socket open -> FREQ, SAMPLE_RATE.

class BackendWorkerMain(QObject):
  ping_ack_ok = pyqtSignal(str)
  error_occured = pyqtSignal(str)
  packet_recieved = pyqtSignal(str, bytes)
  rec_telemetry_data = pyqtSignal(str, bytes)
  rec_camera_data = pyqtSignal(str, bytes)

  def __init__(self, host='127.0.0.1', port=9999):
    super().__init__()
    self._running = True
    self.max_transmission_limit = 3
    self.host_ip = host
    self.port = port
    # Init the socket connection
    self.gnu_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.gs_rx = None
    self.ping_ack_received = False

    # Data handlers
    self.data_handler = None
    self.bin_to_jpeg = None

    # Some empty variables in case we need them later
    self.freq = None
    self.sample_rate = None
    self.rx_gain = None
    self.crc_poly = None
    self.mod_dev = None
    self.tcp_port = None
    self.sync_handler = None
    self.payload_len = None
    self.preamble_byte = None
    self.frame_len = None



  def stop(self):
    self._running = False

  
  def run(self):
    try:
        self.gnu_socket.connect((f"{self.host_ip}", self.port))  # will need to add actual HOST and PORT
    except Exception as e:
        self.error_occured.emit(f"Connection to server failed! {str(e)}")
        return # Connection failed return.
    self.gnu_socket.settimeout(3)
    while self._running:
      # Check for ping acknowledgement
      while not self.ping_ack_received:
          try:
            # send packet to gnu
            ping_packet = GroundStationTransmitter().ping()
            self.gnu_socket.send(ping_packet)

            # wait for ping
            data = self.gnu_socket.recv(1024)
            if not data:
              self.error_occured.emit("data from the server(ping_ack) is empty")
              continue
            self.gs_rx = ReceivedPacket(data)
            if self.gs_rx.payload_type == PAYLOAD_TYPE_DICT['Ping']:
              self.ping_ack_received = True # Transition to idle state
              self.ping_ack_ok.emit("ping ack received")
            else:
              self.error_occured.emit("Incorrect payload type for ping")
              continue
          except socket.timeout:
            self.error_occured.emit("Error: socket timeout out! in ping ack")
            continue
          except Exception as e:
            self.error_occured.emit(f"Unexpected socket error: {str(e)}")
            continue

      # Start receiving data
      try:
        data = self.gnu_socket.recv(1024)
        if not data:
          self.error_occured.emit("data from the server is empty")
          continue
      except socket.timeout:
        self.error_occured.emit("Error: socket timeout out! in idle state")
        continue
      except Exception as e:
        self.error_occured.emit(f"Unexpected socket error: {str(e)}")
        continue
      
      self.packet_recieved.emit("Packet recieved", data)

      # Send ack
      self.gs_rx = ReceivedPacket(data)
      #Parsed packet info
      payload_type = self.gs_rx.payload_type
      payload_data = self.gs_rx.payload
      payload_length = self.gs_rx.payload_length
      sequence_num = self.gs_rx.sequence_number
      offset = None
      if self.gs_rx.offset:
        self.rec_camera_data.emit("Incoming Camera data", self.gs_rx.payload)
        offset = self.gs_rx.offset
      else:
        self.rec_telemetry_data.emit("Incoming Telemetry data", self.gs_rx.payload)
      
      #Construct ack packet if correct payload type and send data to the server
      try:
        ack_packet = GroundStationTransmitter(payload_type, payload_data, payload_length, sequence_num, offset).ack()
        self.gnu_socket.send(ack_packet)
      except IncorrectPayloadTypeException as e:
        self.error_occured.emit(f"Error: unknown payload type {payload_type}: {e}")
        continue

      # DATA HANDLING
      if payload_type in [PAYLOAD_TYPE_DICT['Telemetry'],
                            PAYLOAD_TYPE_DICT['Camera-1-End'],
                            PAYLOAD_TYPE_DICT['Camera-1-MF'],
                            PAYLOAD_TYPE_DICT['Camera-2-End'],
                            PAYLOAD_TYPE_DICT['Camera-2-MF']]:
        
        self.data_handler = DataHandler(payload_type, payload_data)
        self.data_handler.process_packet() # backend process, will create some directories and files

        jpeg_filename = ""
        # Check if images directory exists and is not empty
        if os.path.isdir('images') and os.listdir('images'):
          self.bin_to_jpeg = BinToJPEG()
          self.bin_to_jpeg.extract_jpg_image(jpeg_filename)

      if not command_queue.empty():
        command = command_queue.get()
        try:
          command_packet = GroundStationTransmitter().command(command)
        except IncorrectCommandTypeException as e:
          self.error_occured.emit(f"Error: unknown command type {command}: {e}")
          continue

        times_retransmitted = 0
        # send command packet
        self.gnu_socket.send(command_packet)
        # Check for acknowledgement recieved and retransmit data if not recieved.
        while True:
          if times_retransmitted == self.max_transmission_limit:
            self.error_occured.emit(f"Retransmission limit reached: {str(times_retransmitted)}")
            self.ping_ack_received = False
            break
          try:
            data = self.gnu_socket.recv(1024)
            if not data:
              self.error_occured.emit(f"Ack not received for command {str(command)}")
              continue
            else:
              self.gs_rx = ReceivedPacket(data)
              if self.gs_rx.payload_type == PAYLOAD_TYPE_DICT['Ack Rec Status']:
                self.packet_recieved.emit(f"Received ack for {command}", data)
                times_retransmitted = 0
                break
          except socket.timeout:
            self.error_occured.emit(f"Socket timed out(command ack) for command {command}, retransmitting {command_packet}")
            times_retransmitted+=1
            continue
          except Exception as e:
            self.error_occured.emit(f"Unexpected socket error: {str(e)}")
            continue
      
      # self.gnu_socket.settimeout(0) # Set the socket timeout to zero again
    
    self.gnu_socket.close()

