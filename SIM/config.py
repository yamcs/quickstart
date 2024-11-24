from datetime import datetime

# Simulator Configuration
SIM_CONFIG = {
    'mission_start_time': datetime(2025, 1, 1, 0, 0, 0),  # Mission start time
    'time_step': 1.0,                                     # Simulation time step in seconds
    'time_factor': 1.0                                    # Time factor (e.g. 1.0 = real time, 2.0 = 2x speed, etc.)
}

# Spacecraft Configuration
SPACECRAFT_CONFIG = {
    # Communication parameters
    'comms': {
        'tc_port': 10025,                                 # Telecommand port
        'tm_port': 10015,                                 # Telemetry port
        'host': 'localhost'                               # Network host
    },
    
    # Initial spacecraft state
    'initial_state': {
        'adcs_temperature': -10,                          # Initial ADCS temperature
        # Add more initial states as needed
    },

    # Orbital parameters (Keplerian elements)
    'orbit': {
        'semi_major_axis': 6778.0,                       # km (altitude + Earth radius)
        'eccentricity': 0.0001,                          # Nearly circular
        'inclination': 51.6,                             # degrees
        'raan': 0.0,                                     # Right Ascension of Ascending Node (degrees)
        'arg_perigee': 0.0,                              # Argument of Perigee (degrees)
        'true_anomaly': 0.0,                             # True Anomaly (degrees)
    }
}

# Universe Configuration
UNIVERSE_CONFIG = {
    # Space environment
    'environment': {
        'solar_flux': 1361.0,                            # Solar flux in W/m²
        # Add more environment parameters as needed
    }
}
