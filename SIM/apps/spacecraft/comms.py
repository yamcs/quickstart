import struct
import socket
import threading
from logger import SimLogger
from config import SPACECRAFT_CONFIG
import numpy as np

class CommsModule:
    def __init__(self, cdh):
        self.logger = SimLogger.get_logger("CommsModule")
        self.cdh = cdh
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['comms']
        comms_config = SPACECRAFT_CONFIG['spacecraft']['comms']
        
        # Initialize COMMS state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        self.mode = config['mode']
        
        # Communication parameters
        self.packets_sent = 0
        self.packets_received = 0
        self.uplink_bitrate = config['uplink_bitrate']
        self.downlink_bitrate = config['downlink_bitrate']
        
        # Socket configuration
        self.tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.TC_PORT = comms_config['tc_port']
        self.TM_PORT = comms_config['tm_port']
        self.HOST = comms_config['host']
        
        self.running = False
        
    def get_telemetry(self):
        """Package current COMMS state into telemetry format"""
        values = [
            np.uint8(self.state),              # SubsystemState_Type (8 bits)
            np.int8(self.temperature),         # int8_degC (8 bits)
            np.int8(self.heater_setpoint),     # int8_degC (8 bits)
            np.float32(self.power_draw),       # float_W (32 bits)
            np.uint8(self.mode),               # CommsMode_Type (8 bits)
            np.uint32(self.downlink_bitrate),        # uint32_bps (32 bits)
            np.uint32(self.uplink_bitrate)         # uint32_bps (32 bits)
        ]
        
        return struct.pack(">BbbfBII", *values)
        
    def process_command(self, command_id, command_data):
        """Process COMMS commands (Command_ID range 40-49)"""
        self.logger.info(f"Processing COMMS command {command_id}: {command_data.hex()}")
        
        try:
            if command_id == 40:    # COMMS_SET_STATE
                state = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting COMMS state to: {state}")
                self.state = state
                
            elif command_id == 41:   # COMMS_SET_HEATER
                heater = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting COMMS heater to: {heater}")
                self.heater_state = heater
                
            elif command_id == 42:   # COMMS_SET_HEATER_SETPOINT
                setpoint = struct.unpack(">f", command_data)[0]
                self.logger.info(f"Setting COMMS heater setpoint to: {setpoint}°C")
                self.heater_setpoint = setpoint
                
            elif command_id == 43:   # COMMS_SET_MODE
                mode = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting COMMS mode to: {mode}")
                self.mode = mode
                
            elif command_id == 44:   # COMMS_SET_BITRATE
                bitrate = struct.unpack(">I", command_data)[0]
                self.logger.info(f"Setting COMMS bitrate to: {bitrate} bps")
                self.downlink_bitrate = bitrate
                
            else:
                self.logger.warning(f"Unknown COMMS command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking COMMS command {command_id}: {e}")
            
    def start(self):
        """Start the communications module"""
        self.running = True
        self.tc_socket.bind((self.HOST, self.TC_PORT))
        
        # Start TC listener thread
        self.tc_thread = threading.Thread(target=self._tc_listener)
        self.tc_thread.daemon = True
        self.tc_thread.start()
        
        self.logger.info(f"CommsModule started - Listening for telecommands on port {self.TC_PORT}")
        
    def stop(self):
        """Stop the communications module"""
        self.running = False
        self.tc_socket.close()
        self.tm_socket.close()
        self.logger.info("CommsModule stopped")
        
    def send_tm_packet(self, packet):
        """Send telemetry packet"""
        try:
            self.tm_socket.sendto(packet, (self.HOST, self.TM_PORT))
            self.packets_sent += 1
            self.logger.debug(f"Sent TM packet: {packet.hex()}")
        except socket.error as e:
            self.logger.error(f"Socket error while sending TM: {e}")
            
    def _tc_listener(self):
        """Listen for incoming telecommands"""
        while self.running:
            try:
                data, addr = self.tc_socket.recvfrom(1024)
                self.packets_received += 1
                self.logger.info(f"Received TC from {addr}")
                
                # Parse CCSDS packet
                try:
                    # Skip CCSDS header (6 bytes) and timestamp (4 bytes)
                    command_id = struct.unpack(">H", data[10:12])[0]  # 16-bit command ID
                    command_data = data[12:]  # Rest is command data
                    
                    self.logger.debug(f"Parsed command ID: {command_id}, data: {command_data.hex()}")
                    
                    # Forward command to CDH for processing
                    self.cdh.process_command(command_id, command_data)
                    
                except struct.error as e:
                    self.logger.error(f"Error parsing telecommand: {e}")
                    
            except socket.error as e:
                if self.running:
                    self.logger.error(f"Socket error: {e}")
                break
