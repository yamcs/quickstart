import struct
from logger import SimLogger
from apps.spacecraft.adcs import ADCSModule
from apps.spacecraft.obc import OBCModule
from apps.spacecraft.power import PowerModule
from apps.spacecraft.payload import PayloadModule
from apps.spacecraft.datastore import DatastoreModule
from apps.spacecraft.comms import CommsModule
from config import SPACECRAFT_CONFIG, SIM_CONFIG
import numpy as np
from datetime import datetime

class CDHModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("CDHModule")
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['cdh']
        self.simulator = None  # Will be set by simulator
        self.epoch = SIM_CONFIG['epoch']
        
        # Initialize CDH state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        
        # Initialize sequence counter for CCSDS packets
        self.sequence_count = 0
        
        # Initialize subsystems
        self.adcs = ADCSModule()
        self.obc = OBCModule()
        self.power = PowerModule()
        self.payload = PayloadModule(self.adcs)
        self.datastore = DatastoreModule()
        self.comms = CommsModule(self)  # Pass self reference for command routing
        
    def set_simulator(self, simulator):
        """Set reference to simulator instance"""
        self.simulator = simulator

    def get_telemetry(self):
        """Package CDH state into telemetry format"""
        values = [
            np.uint8(self.state),              # SubsystemState_Type (8 bits)
            np.int8(self.temperature),         # int8_degC (8 bits)
            np.int8(self.heater_setpoint),     # int8_degC (8 bits)
            np.float32(self.power_draw)        # float_W (32 bits)
        ]
        
        return struct.pack(">Bbbf", *values)

    def create_tm_packet(self, current_sim_time):
        """Create a CCSDS telemetry packet"""
        # CCSDS Primary Header
        version = 0
        packet_type = 0  # TM
        sec_hdr_flag = 1  # Enable secondary header
        apid = 100  # Housekeeping
        sequence_flags = 3  # Standalone packet
        packet_sequence_count = self.sequence_count & 0x3FFF
    
        first_word = (version << 13) | (packet_type << 12) | (sec_hdr_flag << 11) | apid
        second_word = (sequence_flags << 14) | packet_sequence_count
        
        # Calculate elapsed time in milliseconds since mission start
        self.logger.debug(f"Current sim time: {current_sim_time}")
        self.logger.debug(f"Epoch: {self.epoch}")
        elapsed_seconds = (current_sim_time - self.epoch).total_seconds()
        self.logger.debug(f"Elapsed seconds: {elapsed_seconds}")
        timestamp = int(elapsed_seconds)  # not converting to milliseconds due to 4Byte
        self.logger.debug(f"Timestamp: {timestamp}") 
        
        # Pack as 4-byte unsigned int
        secondary_header = struct.pack(">I", timestamp & 0xFFFFFFFF)
        
        # Get telemetry from all subsystems in correct order
        obc_tm = self.obc.get_telemetry()
        cdh_tm = self.get_telemetry()
        power_tm = self.power.get_telemetry()
        adcs_tm = self.adcs.get_telemetry()
        comms_tm = self.comms.get_telemetry()
        payload_tm = self.payload.get_telemetry()
        datastore_tm = self.datastore.get_telemetry()
        
        # Combine all telemetry
        data = obc_tm + cdh_tm + power_tm + adcs_tm + comms_tm + payload_tm + datastore_tm
        
        # Calculate packet length (minus 1 per CCSDS standard)
        packet_length = len(secondary_header) + len(data) - 1
        
        # Create the complete packet
        packet = struct.pack(">HHH", first_word, second_word, packet_length) + secondary_header + data
        
        self.sequence_count += 1
        return packet

    def process_command(self, command_id, command_data):
        """Process incoming telecommands"""
        try:            
            self.logger.info(f"Received command ID: {command_id}")
            
            # Route commands to appropriate subsystem
            if 10 <= command_id <= 19:
                self.obc.process_command(command_id, command_data)
            elif 20 <= command_id <= 29:
                self.power.process_command(command_id, command_data)
            elif 30 <= command_id <= 39:
                self.adcs.process_command(command_id, command_data)
            elif 40 <= command_id <= 49:
                self.comms.process_command(command_id, command_data)
            elif 50 <= command_id <= 59:
                self.payload.process_command(command_id, command_data)
            elif 60 <= command_id <= 69:
                self.datastore.process_command(command_id, command_data)
            else:
                self.logger.warning(f"Unhandled command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error processing command: {e}")
