import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG
import numpy as np
from ..universe.orbit import OrbitPropagator
from ..universe.environment import Environment

class PowerModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("PowerModule")
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['power']
        
        # Initialize orbit propagator and environment
        self.orbit_propagator = OrbitPropagator()
        self.environment = Environment()
        
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

    def update(self, current_time, adcs_module):
        """Update power state based on current conditions"""
        try:
            # Get hardware config
            power_config = SPACECRAFT_CONFIG['spacecraft']['hardware']['power']
            
            # Get orbit state
            orbit_state = self.orbit_propagator.propagate(current_time)
            
            # Reset total generation
            self.solar_total_generation = 0.0
            self.solar_panel_generation = {
                'pX': 0.0,
                'nX': 0.0,
                'pY': 0.0,
                'nY': 0.0
            }
            
            # If in eclipse, no solar generation
            if orbit_state['eclipse']:
                self.solar_panel_generation = {
                    'pX': 0.0,
                    'nX': 0.0,
                    'pY': 0.0,
                    'nY': 0.0
                }
            else:
                # Get sun position and calculate panel angles using ADCS quaternion
                sun_pos = self.orbit_propagator.sun.get_position_at_time(current_time)
                panel_angles = self.environment.solar_illumination(
                    orbit_state['position'],
                    sun_pos,
                    adcs_module.quaternion
                )
                
                # Calculate generation for each panel
                for panel in ['pX', 'nX', 'pY', 'nY']:
                    # Convert angle to cosine factor (angle is in degrees)
                    angle = panel_angles[panel]
                    # Only generate power if angle is less than 90 degrees
                    if angle < 90:
                        angle_factor = np.cos(np.radians(angle))
                    else:
                        angle_factor = 0.0
                        
                    power = (power_config['solar_flux'] * 
                            power_config['solar_efficiency'] * 
                            power_config['solar_panels'][panel]['area'] * 
                            angle_factor)
                    
                    self.solar_panel_generation[panel] = power
                    self.logger.debug(f"Panel {panel}: angle_factor={angle_factor:.3f}, power={power:.2f}W")
                    
            # Update individual panel values
            self.solar_panel_generation_pX = self.solar_panel_generation['pX']
            self.solar_panel_generation_nX = self.solar_panel_generation['nX']
            self.solar_panel_generation_pY = self.solar_panel_generation['pY']
            self.solar_panel_generation_nY = self.solar_panel_generation['nY']

            self.logger.debug(f"Solar panel generation: {self.solar_panel_generation}")
            
            # Calculate total generation
            self.solar_total_generation = sum(self.solar_panel_generation.values())

            self.logger.debug(f"Solar total generation: {self.solar_total_generation} W")
            
            # Simple power balance calculation
            if self.solar_total_generation > self.power_draw:
                self.power_balance = 1  # POSITIVE
                self.battery_charge = min(100.0, self.battery_charge + 0.1)  # Very simple charging
            elif self.solar_total_generation < self.power_draw:
                self.power_balance = 2  # NEGATIVE
                self.battery_charge = max(0.0, self.battery_charge - 0.1)  # Very simple discharging
            else:
                self.power_balance = 0  # BALANCED
                
        except Exception as e:
            self.logger.error(f"Error updating power state: {str(e)}")
