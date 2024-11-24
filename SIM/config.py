from datetime import datetime

# Simulator Configuration
SIM_CONFIG = {
    'mission_start_time': datetime(2025, 1, 1, 0, 0, 0),  # Mission start time
    'time_step': 1.0,                                     # Simulation time step in seconds
    'time_factor': 1.0                                    # Time factor (e.g. 1.0 = real time, 2.0 = 2x speed, etc.)
}

# Spacecraft Configuration
SPACECRAFT_CONFIG = {
    'spacecraft': {
        'comms': {
            'host': 'localhost',
            'tc_port': 10025,  # Telecommand reception port
            'tm_port': 10015   # Telemetry transmission port
        },
        'initial_state': {
            # OBC Initial State
            'obc': {
                'state': 2,          # SubsystemState_Type (uint8): 0=OFF, 1=IDLE, 2=ACTIVE, 3=ERROR
                'temperature': 20,    # int8_degC: Operating temperature in degrees Celsius
                'heater_setpoint': 25,# int8_degC: Temperature setpoint for heater control
                'power_draw': 2.5,    # float_W: Power consumption in Watts
                'mode': 1            # OBCMode_Type (uint8): 0=SAFE, 1=NOMINAL, 2=PAYLOAD
            },

            # CDH Initial State
            'cdh': {
                'state': 2,          # SubsystemState_Type (uint8): 0=OFF, 1=IDLE, 2=ACTIVE, 3=ERROR
                'temperature': 20,    # int8_degC: Operating temperature in degrees Celsius
                'heater_setpoint': 25,# int8_degC: Temperature setpoint for heater control
                'power_draw': 2.0,    # float_W: Power consumption in Watts
                'mode': 0            # OBCMode_Type (uint8): 0=SAFE, 1=NOMINAL, 2=PAYLOAD
            },

            # POWER Initial State
            'power': {
                'state': 2,          # SubsystemState_Type (uint8): 0=OFF, 1=IDLE, 2=ACTIVE, 3=ERROR
                'temperature': 20,    # int8_degC: Operating temperature in degrees Celsius
                'heater_setpoint': 25,# int8_degC: Temperature setpoint for heater control
                'power_draw': 1.0,    # float_W: Power consumption in Watts
                'battery_voltage': 7.4,# float_V: Battery voltage in Volts
                'battery_current': 0.0,# float_A: Battery current in Amperes
                'battery_charge': 100.0,# float_percent: Battery charge percentage
                'power_balance': 0,   # PowerBalance_Type (uint8): 0=BALANCED, 1=POSITIVE, 2=NEGATIVE
                'solar_total_generation': 0.0,  # float_W: Total solar power generation in Watts
                'solar_panel_generation': {     # float_W: Per-panel solar generation in Watts
                    'pX': 0.0,       # +X panel power generation
                    'nX': 0.0,       # -X panel power generation
                    'pY': 0.0,       # +Y panel power generation
                    'nY': 0.0        # -Y panel power generation
                }
            },

            # ADCS Initial State
            'adcs': {
                'state': 2,          # SubsystemState_Type (uint8): 0=OFF, 1=IDLE, 2=ACTIVE, 3=ERROR
                'temperature': 20,    # int8_degC: Operating temperature in degrees Celsius
                'heater_setpoint': 25,# int8_degC: Temperature setpoint for heater control
                'power_draw': 5.0,    # float_W: Power consumption in Watts
                'mode': 0,           # ADCSMode_Type (uint8): 0=OFF, 1=LOCK, 2=SUNPOINTING, 3=NADIR, 4=DOWNLOAD
                'status': 0,         # ADCSStatus_Type (uint8): 0=UNCONTROLLED, 1=SLEWING, 2=POINTING
                'quaternion': [0.707, 0.0, 0.0, 0.707],  # float[4]: Attitude quaternion [q1,q2,q3,q4]
                'angular_velocity': [0.0, 0.0, 0.0],     # float_deg_s[3]: Angular rates [x,y,z] in deg/s
                'position': [0.0, 0.0, 400.0],           # [float_deg,float_deg,float_km]: [lat,lon,alt]
                'eclipse': 0         # Eclipse_Type (uint8): 0=DAY, 1=NIGHT
            },

            # COMMS Initial State
            'comms': {
                'state': 2,          # SubsystemState_Type (uint8): 0=OFF, 1=IDLE, 2=ACTIVE, 3=ERROR
                'temperature': 20,    # int8_degC: Operating temperature in degrees Celsius
                'heater_setpoint': 25,# int8_degC: Temperature setpoint for heater control
                'power_draw': 3.0,    # float_W: Power consumption in Watts
                'mode': 0,           # CommsMode_Type (uint8): 0=OFF, 1=RX, 2=TXRX
                'uplink_bitrate': 9600,   # uint32_bps: Uplink data rate in bits per second
                'downlink_bitrate': 9600  # uint32_bps: Downlink data rate in bits per second
            },

            # PAYLOAD Initial State
            'payload': {
                'state': 0,          # SubsystemState_Type (uint8): 0=OFF, 1=IDLE, 2=ACTIVE, 3=ERROR
                'temperature': 20,    # int8_degC: Operating temperature in degrees Celsius
                'heater_setpoint': 25,# int8_degC: Temperature setpoint for heater control
                'power_draw': 2.0,    # float_W: Power consumption in Watts
                'status': 0          # PayloadStatus_Type (uint8): 0=READY, 1=BUSY
            },

            # DATASTORE Initial State
            'datastore': {
                'state': 2,          # SubsystemState_Type (uint8): 0=OFF, 1=IDLE, 2=ACTIVE, 3=ERROR
                'temperature': 20,    # int8_degC: Operating temperature in degrees Celsius
                'heater_setpoint': 25,# int8_degC: Temperature setpoint for heater control
                'power_draw': 1.5,    # float_W: Power consumption in Watts
                'storage_total': 1024 * 1024 * 1024  # uint32: Total storage in bytes (1GB)
            }
        }
    }   
}

# Universe Configuration
UNIVERSE_CONFIG = {
    'perturbations': {
        'gravity': True,        # N-body gravitational forces
        'drag': True,          # Atmospheric drag
        'srp': True,           # Solar radiation pressure
        'magnetic': True       # Magnetic torques
    },
    'space_weather': {
        'F107': 150.0,              # Solar F10.7 radio flux (solar radio flux at 10.7 cm wavelength)
        'F107A': 150.0,             # 81-day average of F10.7
        'magnetic_index': 4.0,      # Geomagnetic AP index (0-400, measure of magnetic field disturbance)
        'solar_cycle_phase': 0.5    # 0-1, current phase of solar cycle
    },
    'max_altitude_for_drag': 1000.0  # km, altitude above which to ignore atmospheric drag
}

# Orbit Configuration
ORBIT_CONFIG = {
    'spacecraft': {  # Matches spacecraft name in SPACECRAFT_CONFIG
        'epoch': SIM_CONFIG['mission_start_time'],
        'elements': {
            'semi_major_axis': 6778.0,    # km (400km altitude + Earth radius)
            'eccentricity': 0.0001,       # Nearly circular
            'inclination': 51.6,          # degrees
            'raan': 0.0,                  # degrees (Right Ascension of Ascending Node)
            'arg_perigee': 0.0,           # degrees (Argument of Perigee)
            'true_anomaly': 0.0           # degrees (True Anomaly at epoch)
        }
    }
}
