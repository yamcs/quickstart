import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG

class PowerModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("PowerModule")
        config = SPACECRAFT_CONFIG['initial_state']['power']
        
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
        
    def get_telemetry(self):
        """Package current POWER state into telemetry format"""
        values = [
            self.state,                    # POWER_state (uint8)
            int(self.temperature),         # POWER_temperature (uint8)
            int(self.heater_setpoint),     # POWER_heater_setpoint (uint8)
            self.power_draw,               # POWER_power_draw (float)
            self.battery_voltage,          # POWER_battery_voltage (float)
            self.battery_current,          # POWER_battery_current (float)
            self.battery_charge,           # POWER_battery_charge (float)
            self.power_balance,            # POWER_total_power_balance (float)
            self.solar_total_generation,   # POWER_solar_total_generation (float)
            # Solar Panel Generation
            self.solar_panel_generation['pX'],  # POWER_solar_panel_generation_pX (float)
            self.solar_panel_generation['nX'],  # POWER_solar_panel_generation_nX (float)
            self.solar_panel_generation['pY'],  # POWER_solar_panel_generation_pY (float)
            self.solar_panel_generation['nY']   # POWER_solar_panel_generation_nY (float)
        ]
        
        return struct.pack(">BbBffffffffff", *values)
        
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
