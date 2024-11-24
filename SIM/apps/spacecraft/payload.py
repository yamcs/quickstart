import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG

class PayloadModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("PayloadModule")
        config = SPACECRAFT_CONFIG['initial_state']['payload']
        
        # Initialize PAYLOAD state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        self.status = config['status']
        
        # Payload specific parameters
        self.data_rate = 0      # bps
        self.data_collected = 0 # bytes
        self.storage_used = 0   # bytes
        self.storage_total = 1024 * 1024  # 1MB total storage
        
    def get_telemetry(self):
        """Package current PAYLOAD state into telemetry format"""
        values = [
            self.state,              # PAYLOAD_state (uint8)
            int(self.temperature),   # PAYLOAD_temperature (uint8)
            int(self.heater_setpoint), # PAYLOAD_heater_setpoint (uint8)
            self.power_draw,         # PAYLOAD_power_draw (float)
            self.status              # PAYLOAD_status (uint8)
        ]
        
        return struct.pack(">BBBfB", *values)
        
    def process_command(self, command_id, command_data):
        """Process PAYLOAD commands (Command_ID range 50-59)"""
        self.logger.info(f"Processing PAYLOAD command {command_id}: {command_data.hex()}")
        
        try:
            if command_id == 50:    # PAYLOAD_SET_STATE
                state = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting PAYLOAD state to: {state}")
                self.state = state
                
            elif command_id == 51:   # PAYLOAD_SET_HEATER
                heater = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting PAYLOAD heater to: {heater}")
                self.heater_state = heater
                
            elif command_id == 52:   # PAYLOAD_SET_HEATER_SETPOINT
                setpoint = struct.unpack(">f", command_data)[0]
                self.logger.info(f"Setting PAYLOAD heater setpoint to: {setpoint}°C")
                self.heater_setpoint = setpoint
                
            elif command_id == 53:   # PAYLOAD_SET_MODE
                mode = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting PAYLOAD mode to: {mode}")
                self.mode = mode
                
            elif command_id == 54:   # PAYLOAD_START_COLLECTION
                self.logger.info("Starting data collection")
                if self.state == 1:  # Only if powered ON
                    self.mode = 1    # COLLECTING
                    self.data_rate = 1024  # 1 kbps
                
            elif command_id == 55:   # PAYLOAD_STOP_COLLECTION
                self.logger.info("Stopping data collection")
                self.mode = 0    # IDLE
                self.data_rate = 0
                
            elif command_id == 56:   # PAYLOAD_CLEAR_DATA
                self.logger.info("Clearing collected data")
                self.data_collected = 0
                self.storage_used = 0
                
            else:
                self.logger.warning(f"Unknown PAYLOAD command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking PAYLOAD command {command_id}: {e}")
