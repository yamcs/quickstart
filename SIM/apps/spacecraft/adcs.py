import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG

class ADCSModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("ADCSModule")
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['adcs']
        
        # Initialize ADCS state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        self.mode = config['mode']
        self.status = config['status']
        
        # Attitude parameters
        self.quaternion = config['quaternion'].copy()
        self.angular_velocity = config['angular_velocity'].copy()
        
        # Orbital parameters
        self.position = config['position'].copy()
        self.eclipse = config['eclipse']
        
    def get_telemetry(self):
        """Package current ADCS state into telemetry format"""
        values = [
            self.state,                    # ADCS_state (uint8)
            int(self.temperature),         # ADCS_temperature (int8)
            int(self.heater_setpoint),     # ADCS_heater_setpoint (int8)
            self.power_draw,               # ADCS_power_draw (float)
            self.mode,                     # ADCS_mode (uint8)
            self.status,                   # ADCS_status (uint8)
            # Quaternion
            self.quaternion[0],            # ADCS_quaternion_q1 (float)
            self.quaternion[1],            # ADCS_quaternion_q2 (float)
            self.quaternion[2],            # ADCS_quaternion_q3 (float)
            self.quaternion[3],            # ADCS_quaternion_q4 (float)
            # Angular Velocity
            self.angular_velocity[0],      # ADCS_angular_velocity_x (float)
            self.angular_velocity[1],      # ADCS_angular_velocity_y (float)
            self.angular_velocity[2],      # ADCS_angular_velocity_z (float)
            # Position and Eclipse
            self.position[0],              # ADCS_earth_latitude (float)
            self.position[1],              # ADCS_earth_longitude (float)
            self.position[2],              # ADCS_earth_altitude (float)
            self.eclipse                   # ADCS_eclipse (uint8)
        ]
        
        return struct.pack(">BbBfBBffffffffffB", *values)
        
    def process_command(self, command_id, command_data):
        """Process ADCS commands (Command_ID range 30-39)"""
        self.logger.info(f"Processing ADCS command {command_id}: {command_data.hex()}")
        
        # Extract command parameters based on command ID
        try:
            if command_id == 30:    # ADCS_SET_STATE
                state = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting ADCS state to: {state}")
                self.state = state
                
            elif command_id == 31:   # ADCS_SET_HEATER
                heater = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting ADCS heater to: {heater}")
                self.heater_state = heater
                
            elif command_id == 32:   # ADCS_SET_HEATER_SETPOINT
                setpoint = struct.unpack(">f", command_data)[0]
                self.logger.info(f"Setting ADCS heater setpoint to: {setpoint}°C")
                self.heater_setpoint = setpoint
                
            elif command_id == 33:   # ADCS_SET_MODE
                mode = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting ADCS mode to: {mode}")
                self.mode = mode
                
            elif command_id == 34:   # ADCS_SET_QUATERNION
                q = struct.unpack(">ffff", command_data)
                self.logger.info(f"Setting ADCS quaternion to: {q}")
                self.quaternion = list(q)
                
            else:
                self.logger.warning(f"Unknown ADCS command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking ADCS command {command_id}: {e}")
