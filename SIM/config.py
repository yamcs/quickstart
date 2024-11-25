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
        },
        'hardware': {
            'adcs': {
                'magnetorquers': {
                    'x': {'max_moment': 0.2},     # A⋅m² (magnetic dipole moment)
                    'y': {'max_moment': 0.2},
                    'z': {'max_moment': 0.2}
                },
                'reaction_wheels': {
                    'x': {
                        'max_torque': 0.001,      # N⋅m
                        'max_momentum': 0.05,      # N⋅m⋅s
                        'moment_of_inertia': 0.001 # kg⋅m²
                    },
                    'y': {
                        'max_torque': 0.001,
                        'max_momentum': 0.05,
                        'moment_of_inertia': 0.001
                    },
                    'z': {
                        'max_torque': 0.001,
                        'max_momentum': 0.05,
                        'moment_of_inertia': 0.001
                    }
                },
                'pointing_requirements': {
                    'accuracy_threshold': 2.0,     # degrees, threshold between SLEWING and POINTING
                    'stability_duration': 0,    # seconds, duration pointing must be maintained
                    'max_slew_rate': 3.0,         # degrees/second, maximum allowed slew rate
                    'nominal_slew_rate': 2.0      # degrees/second, target slew rate during maneuvers
                }
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
            'semi_major_axis': 6878.0,    # km (500km altitude + Earth radius 6378km)
            'eccentricity': 0.0001,       # Nearly circular (0.0001 is close enough)    
            'inclination': 97.4,          # degrees (SSO inclination for 500km)
            'raan': 22.5,                 # degrees (typically chosen for LTAN)
            'arg_perigee': 0.0,           # degrees (0° is prograde, 90° is prograde circular)
            'true_anomaly': 0.0           # degrees (0° is perigee, 180° is apogee) 
        }
    }
}
