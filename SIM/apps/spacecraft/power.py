import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG
import numpy as np

class PowerModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("PowerModule")
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['power']
        
        # Initialize POWER state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        
        # Battery state
        self.battery_voltage = config['battery_voltage']
        self.battery_current = config['battery_current']
        self.battery_charge = config['battery_charge']
        
        # Power balance
        self.power_balance = config['power_balance']
        self.solar_total_generation = config['solar_total_generation']
        self.solar_panel_generation = config['solar_panel_generation'].copy()
        self.solar_panel_generation_pX = self.solar_panel_generation['pX']
        self.solar_panel_generation_nX = self.solar_panel_generation['nX']
        self.solar_panel_generation_pY = self.solar_panel_generation['pY']
        self.solar_panel_generation_nY = self.solar_panel_generation['nY']
        
    def get_telemetry(self):
        """Package current POWER state into telemetry format"""
        values = [
            np.uint8(self.state),                    # SubsystemState_Type (8 bits)
            np.int8(self.temperature),               # int8_degC (8 bits)
            np.int8(self.heater_setpoint),           # int8_degC (8 bits)
            np.float32(self.power_draw),             # float_W (32 bits)
            np.float32(self.battery_voltage),        # float_V (32 bits)
            np.float32(self.battery_current),        # float_A (32 bits)
            np.float32(self.battery_charge),         # float_percent (32 bits)
            np.uint8(self.power_balance),            # PowerBalance_Type (8 bits)
            np.float32(self.solar_total_generation), # float_W (32 bits)
            np.float32(self.solar_panel_generation_pX), # float_W (32 bits)
            np.float32(self.solar_panel_generation_nX), # float_W (32 bits)
            np.float32(self.solar_panel_generation_pY), # float_W (32 bits)
            np.float32(self.solar_panel_generation_nY)  # float_W (32 bits)
        ]
        
        return struct.pack(">BbbffffBfffff", *values)
        
    def process_command(self, command_id, command_data):
        """Process POWER commands (Command_ID range 20-29)"""
        self.logger.info(f"Processing POWER command {command_id}: {command_data.hex()}")
        
        try:
            if command_id == 20:    # POWER_SET_STATE
                state = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting POWER state to: {state}")
                self.state = state
                
            elif command_id == 21:   # POWER_SET_HEATER
                heater = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting POWER heater to: {heater}")
                self.heater_state = heater
                
            elif command_id == 22:   # POWER_SET_HEATER_SETPOINT
                setpoint = struct.unpack(">f", command_data)[0]
                self.logger.info(f"Setting POWER heater setpoint to: {setpoint}°C")
                self.heater_setpoint = setpoint
                
            else:
                self.logger.warning(f"Unknown POWER command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking POWER command {command_id}: {e}")
