import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG

class OBCModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("OBCModule")
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['obc']
        
        # Initialize OBC state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        self.mode = config['mode']
        
    def get_telemetry(self):
        """Package current OBC state into telemetry format"""
        values = [
            self.state,              # OBC_state (uint8)
            int(self.temperature),   # OBC_temperature (uint8)
            int(self.heater_setpoint), # OBC_heater_setpoint (uint8)
            self.power_draw,         # OBC_power_draw (float)
            self.mode                # OBC_mode (uint8)
        ]
        
        return struct.pack(">BBBfB", *values)
        
    def process_command(self, command_id, command_data):
        """Process OBC commands (Command_ID range 10-19)"""
        self.logger.info(f"Processing OBC command {command_id}: {command_data.hex()}")
        
        try:
            if command_id == 10:    # OBC_SET_STATE
                state = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting OBC state to: {state}")
                self.state = state
                
            elif command_id == 11:   # OBC_SET_HEATER
                heater = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting OBC heater to: {heater}")
                self.heater_state = heater
                
            elif command_id == 12:   # OBC_SET_HEATER_SETPOINT
                setpoint = struct.unpack(">f", command_data)[0]
                self.logger.info(f"Setting OBC heater setpoint to: {setpoint}°C")
                self.heater_setpoint = setpoint
                
            elif command_id == 13:   # OBC_SET_MODE
                mode = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting OBC mode to: {mode}")
                self.mode = mode
                
            elif command_id == 14:   # OBC_RESET
                self.logger.info("Resetting OBC")
                self.state = 0
                self.mode = 0
                self.heater_state = 0
                self.heater_setpoint = 0.0
                
            else:
                self.logger.warning(f"Unknown OBC command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking OBC command {command_id}: {e}")
