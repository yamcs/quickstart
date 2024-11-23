"""
BOSSY Simulator Configuration
Configuration for the simulation environment and runtime parameters
"""

import numpy as np
from datetime import datetime, timezone

class SimulatorConfig:
    def __init__(self):
        # Simulation Time Configuration
        self.time = {
            'start_utc': datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            'time_step': 1.0,        # seconds (fixed at 1 Hz)
            'time_factor': 1,        # simulation speed multiplier (1x, 2x, 5x, 10x, etc.)
            'end_utc': None          # Run indefinitely
        }

        # Orbit Configuration (Sun-Synchronous Orbit)
        self.orbit = {
            'semi_major_axis': 6878.137,  # km (Earth radius + 500 km)
            'eccentricity': 0.0,          # circular orbit
            'inclination': 97.4,          # degrees (sun-synchronous inclination for 500km)
            'raan': 0.0,                  # degrees (Local Time of Ascending Node can be adjusted)
            'arg_perigee': 0.0,           # degrees
            'true_anomaly': 0.0,          # degrees
            'orbit_type': 'SSO',          # Sun-Synchronous Orbit
            'altitude': 500.0,            # km (for reference)
        }

        # Environment Configuration
        self.environment = {
            'sun': {
                'solar_constant': 1361.0,  # W/m^2 at 1 AU
                'intensity_factor': 1.0,   # For orbit variation
                'initial_vector': [1, 0, 0]  # Initial sun vector in ECI
            },
            'earth': {
                'radius': 6378.137,      # km
                'mu': 398600.4418,       # km^3/s^2
                'J2': 0.00108263,        # Earth's J2 perturbation
                'rotation_rate': 7.2921e-5,  # rad/s (Earth's sidereal rotation rate)
                'albedo': 0.3,           # Earth's average albedo
                'ir_emission': 237.0     # W/m^2 (Earth's IR emission)
            },
            'sun': {
                'solar_constant': 1361.0,    # W/m^2 Solar Flux at 1 AU
                'intensity_factor': 1.0,     # For orbit variation
                'initial_vector': [1, 0, 0]  # Initial sun vector in ECI
            },
            'magnetic_field': {
                'strength': 3.12e-5,     # Tesla at equator
                'dipole_tilt': 11.5      # degrees
            },
            'atmosphere': {
                'density_at_perigee': 1.225e-11,  # kg/m^3
                'scale_height': 7.249    # km
            },
            'space': {
                'temperature': 2.7        # K (cosmic background)
            }   
        }

        # Communication Configuration
        self.communication = {
            'ground_station': {
                'name': 'GHY',                # Goonhilly Earth Station
                'latitude': 50.0472,          # degrees N
                'longitude': -5.1831,         # degrees W
                'altitude': 0.114,            # km above sea level
                'min_elevation': 10.0,        # degrees
                'location': 'Cornwall, UK'    # Human readable location
            },
            'network': {
                'udp_tm_port': 10015,        # Telemetry UDP port
                'udp_tc_port': 10025,        # Telecommand UDP port
                'host': 'localhost'
            }
        }

        # Simulation Features
        self.features = {
            'enable_perturbations': True,
            'enable_thermal': True,
            'enable_power': True,
            'enable_comms': True,
            'enable_adcs': True
        }

        # Logging Configuration
        self.logging = {
            'stats_interval': 5.0,     # How often to log statistics (seconds)
            'level': 'INFO',           # Logging level (DEBUG, INFO, WARNING, ERROR)
            'file': 'simulator.log',   # Log file name
            'console': True,           # Whether to log to console
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'telemetry': {
                'save_interval': 1.0,  # How often to save telemetry (seconds)
                'file': 'telemetry.csv'  # Telemetry file name
            }
        }

        # Visualization Configuration
        self.visualization = {
            'enable': False  # Toggle visualization on/off
        }

        # Initial States Configuration
        self.initial_states = {
            'power': 'ACTIVE',
            'obc': 'ACTIVE',
            'comms': 'ACTIVE',
            'adcs': {
                'state': 'IDLE',
                'mode': 'SUNPOINTING'
            },
            'payload': 'IDLE',
            'datastore': 'IDLE'
        }

