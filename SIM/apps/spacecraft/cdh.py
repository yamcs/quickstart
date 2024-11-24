import struct
from logger import SimLogger
from apps.spacecraft.adcs import ADCSModule
from apps.spacecraft.obc import OBCModule
from apps.spacecraft.power import PowerModule
from apps.spacecraft.payload import PayloadModule
from apps.spacecraft.datastore import DatastoreModule
from apps.spacecraft.comms import CommsModule
from config import SPACECRAFT_CONFIG

class CDHModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("CDHModule")
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['cdh']
        
        # Initialize CDH state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        self.mode = config['mode']
        
        # Initialize sequence counter for CCSDS packets
        self.sequence_count = 0
        
        # Initialize subsystems
        self.adcs = ADCSModule()
        self.obc = OBCModule()
        self.power = PowerModule()
        self.payload = PayloadModule()
        self.datastore = DatastoreModule()
        self.comms = CommsModule(self)  # Pass self reference for command routing
        
    def get_telemetry(self):
        """Package CDH state into telemetry format"""
        values = [
            self.state,              # CDH_state (uint8)
            int(self.temperature),   # CDH_temperature (uint8)
            int(self.heater_setpoint), # CDH_heater_setpoint (uint8)
            self.power_draw,         # CDH_power_draw (float)
            self.mode                # CDH_mode (uint8)
        ]
        
        return struct.pack(">BBBfB", *values)

    def create_tm_packet(self):
        """Create a CCSDS telemetry packet"""
        # CCSDS Primary Header
        version = 0
        packet_type = 0  # TM
        sec_hdr_flag = 0
        apid = 100  # Housekeeping
        sequence_flags = 3  # Standalone packet
        packet_sequence_count = self.sequence_count & 0x3FFF
        
        first_word = (version << 13) | (packet_type << 12) | (sec_hdr_flag << 11) | apid
        second_word = (sequence_flags << 14) | packet_sequence_count
        
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
        packet_length = len(data) - 1
        
        # Create the complete packet
        packet = struct.pack(">HHH", first_word, second_word, packet_length) + data
        
        self.sequence_count += 1
        return packet

    def process_command(self, command_data):
        """Process incoming telecommands"""
        try:
            command_id = struct.unpack(">H", command_data[6:8])[0]
            command_payload = command_data[8:]
            
            self.logger.info(f"Received command ID: {command_id}")
            
            # Route commands to appropriate subsystem
            if 10 <= command_id <= 19:
                self.obc.process_command(command_id, command_payload)
            elif 20 <= command_id <= 29:
                self.power.process_command(command_id, command_payload)
            elif 30 <= command_id <= 39:
                self.adcs.process_command(command_id, command_payload)
            elif 40 <= command_id <= 49:
                self.comms.process_command(command_id, command_payload)
            elif 50 <= command_id <= 59:
                self.payload.process_command(command_id, command_payload)
            elif 60 <= command_id <= 69:
                self.datastore.process_command(command_id, command_payload)
            else:
                self.logger.warning(f"Unhandled command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error processing command: {e}")
