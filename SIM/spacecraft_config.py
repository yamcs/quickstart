"""
BOSSY Spacecraft Configuration
Default configuration for a 3U CubeSat with fixed solar panels and Earth-imaging payload
"""

import numpy as np
from enum import Enum, auto
from typing import Dict, List

class TelemetryType(Enum):
    UINT8 = auto()
    INT8 = auto()
    UINT16 = auto()
    INT16 = auto()
    UINT32 = auto()
    INT32 = auto()
    FLOAT = auto()
    DOUBLE = auto()
    STRING = auto()
    BOOLEAN = auto()

class TelemetryMode(Enum):
    MINIMAL = "MINIMAL"
    NORMAL = "NORMAL"
    FULL = "FULL"

# CubeSat Standard Units (in meters)
CUBESAT_UNIT = 0.1  # 10cm per unit

class SubsystemState(Enum):
    OFF = "OFF"
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    ERROR = "ERROR"

class ADCSMode(Enum):
    OFF = "OFF"
    LOCK = "LOCK"
    SUNPOINTING = "SUNPOINTING"
    NADIR = "NADIR"

class ADCSStatus(Enum):
    UNDEFINED = "UNDEFINED"
    SLEWING = "SLEWING"
    POINTING = "POINTING"

class CommsMode(Enum):
    OFF = "OFF"
    TX = "TX"
    RX = "RX"
    TXRX = "TXRX"

class OBCMode(Enum):
    SAFE = "SAFE"
    NOMINAL = "NOMINAL"
    PAYLOAD = "PAYLOAD"

class SpacecraftConfig:
    def __init__(self):
        # Structure Configuration
        self.structure = {
            'dimensions': {
                'x': CUBESAT_UNIT,      # 1U width
                'y': CUBESAT_UNIT,      # 1U depth
                'z': CUBESAT_UNIT * 3   # 3U length
            },
            'mass': 4.0,  # kg
            'center_of_mass': np.array([0.0, 0.0, 0.0]),  # m, in body frame
            'inertia_tensor': np.array([  # kg*m^2
                [0.033, 0, 0],
                [0, 0.033, 0],
                [0, 0, 0.007]
            ]),
            'surfaces': {
                'albedo': 0.8,  # Reflectivity coefficient
                'emissivity': 0.9  # Thermal emissivity
            }
        }

        # Communications Configuration
        self.comms = {
            'uplink_rate': 9600,     # bps
            'downlink_rate': 115200,  # bps
            'power': {
                'idle': 0.2,         # Watts
                'active': 2.0        # Watts
            },
            'frequencies': {
                'uplink': 435.0,     # MHz (UHF)
                'downlink': 145.0    # MHz (VHF)
            },
            'link_budget': {
                'tx_power': 1.0,  # W
                'rx_sensitivity': -105,  # dBm
                'antenna_gain': 2.0  # dBi
            },
            'network': {
                'tm_host': 'localhost',
                'tm_port': 10015,    # YAMCS TM port
                'tc_host': 'localhost',
                'tc_port': 10025     # YAMCS TC port
            }
        }

        # On-Board Computer Configuration
        self.obc = {
            'telemetry_rate': 1.0,   # Hz
            'power': {
                'idle': 0.3,         # Watts
                'active': 0.5        # Watts
            },
        }

        # ADCS Configuration
        self.adcs = {
            'magnetorquers': {
                'count': 3,
                'max_dipole': 0.2,   # Am^2
                'power_per_axis': 0.2 # Watts at max dipole
            },
            'reaction_wheels': {
                'count': 3,
                'max_torque': 0.001, # Nm
                'momentum_capacity': 0.050, # Nms
                'power': {
                    'idle': 0.1,     # Watts
                    'active': 0.3    # Watts per wheel
                }
            },
            'power': {
                'idle': 0.2,         # Watts (controller only)
                'active': 0.4        # Watts (controller only)
            }
        }

        # Power System Configuration
        self.power = {
            'battery': {
                'nominal_voltage': 7.4,     # Volts
                'capacity': 10.0,           # Amp-hours
                'initial_charge': 1.0,      # 100%
                'minimum_charge': 0.2,      # 20%
                'maximum_charge': 1.0,      # 100%
                'charge_efficiency': 0.95,   # 95%
                'discharge_efficiency': 0.95 # 95%
            },
            'solar_panels': {
                'faces': [
                    {
                        'name': '+X',
                        'area': 0.03,        # m^2
                        'efficiency': 0.30,   # 30%
                        'normal': [1, 0, 0]
                    },
                    {
                        'name': '-X',
                        'area': 0.03,
                        'efficiency': 0.30,
                        'normal': [-1, 0, 0]
                    },
                    {
                        'name': '+Y',
                        'area': 0.1,
                        'efficiency': 0.30,
                        'normal': [0, 1, 0]
                    },
                    {
                        'name': '-Y',
                        'area': 0.1,
                        'efficiency': 0.30,
                        'normal': [0, -1, 0]
                    },
                    {
                        'name': '+Z',
                        'area': 0.03,
                        'efficiency': 0.30,
                        'normal': [0, 0, 1]
                    },
                    {
                        'name': '-Z',
                        'area': 0.03,
                        'efficiency': 0.30,
                        'normal': [0, 0, -1]
                    }
                ]
            },
            'subsystems': {
                'obc': {
                    'idle': 0.2,    # Watts
                    'active': 0.5
                },
                'comms': {
                    'idle': 0.1,
                    'active': 2.0,
                    'rx': 0.3,
                    'tx': 2.0
                },
                'adcs': {
                    'idle': 0.1,
                    'active': 0.4,
                    'slew': 0.6
                },
                'payload': {
                    'idle': 0.1,
                    'active': 2.5,
                    'imaging': 1.5,
                    'processing': 0.8
                },
                'datastore': {
                    'idle': 0.1,
                    'active': 0.5,
                    'read': 0.3,
                    'write': 0.4
                }
            }
        }

        # Thermal Configuration
        self.thermal = {
            'properties': {
                'thermal_mass': 5.0,  # kg
                'heat_loss_rate': 2.0,  # W/K
                'heat_gain_rate': 1.0   # W/K
            },
            'subsystems': {
                'power': {
                    'initial_temperature': 20.0,  # Celsius
                    'heater_power': 2.0,         # Watts
                    'power_draw': 0.5,           # Watts baseline power draw
                    'operating_range': {
                        'min': -10.0,
                        'max': 50.0
                    }
                },
                'obc': {
                    'initial_temperature': 20.0,
                    'heater_power': 1.0,
                    'power_draw': 0.3,
                    'operating_range': {
                        'min': 0.0,
                        'max': 40.0
                    }
                },
                'comms': {
                    'initial_temperature': 20.0,
                    'heater_power': 2.0,
                    'power_draw': 0.4,
                    'operating_range': {
                        'min': -20.0,
                        'max': 60.0
                    }
                },
                'adcs': {
                    'initial_temperature': 20.0,
                    'heater_power': 1.5,
                    'power_draw': 0.3,
                    'operating_range': {
                        'min': -10.0,
                        'max': 45.0
                    }
                },
                'payload': {
                    'initial_temperature': 20.0,
                    'heater_power': 3.0,
                    'power_draw': 0.6,
                    'operating_range': {
                        'min': 15.0,
                        'max': 35.0
                    }
                },
                'datastore': {
                    'initial_temperature': 20.0,
                    'heater_power': 1.0,
                    'power_draw': 0.2,
                    'operating_range': {
                        'min': -5.0,
                        'max': 40.0
                    }
                }
            }
        }

        # Payload (Earth Imaging Camera) Configuration
        self.payload = {
            'camera': {
                'resolution': (2048, 2048),  # pixels
                'pixel_size': 5.5e-6,        # m
                'focal_length': 0.070,       # m
                'field_of_view': 15.0,       # degrees
                'bits_per_pixel': 12,
                'orientation': np.array([0, 0, -1]),  # Points in -Z direction
                'power': {
                    'idle': 0.1,             # Watts
                    'active': 2.5            # Watts during imaging
                }
            }
        }

        # Datastore Configuration
        self.datastore = {
            'total_storage': 1024.0,     # MB
            'write_speed': 2.0,          # MB/s
            'read_speed': 5.0,           # MB/s
            'power': {
                'idle': 0.1,             # Watts
                'active': 0.5            # Watts during read/write
            },
            'temperature_limits': {
                'min_operating': -5.0,   # Celsius
                'max_operating': 40.0    # Celsius
            },
            'error_rates': {
                'read': 1e-9,            # Bit error rate during read
                'write': 1e-9            # Bit error rate during write
            }
        }

        # General Configuration
        self.general = {
            'name': 'spacecraft',
            'safe_mode_power': 2.0,               # Watts (minimum power for safe mode)
            'default_orientation': np.array([0, 0, 0, 1]),  # quaternion
            'operational_temperature_range': {
                'min': -20.0,  # Celsius
                'max': 50.0    # Celsius
            },
            'modes': {
                'safe': {'required_subsystems': ['obc', 'power', 'comms']},
                'nominal': {'required_subsystems': ['obc', 'power', 'comms', 'adcs']},
                'payload': {'required_subsystems': ['obc', 'power', 'comms', 'adcs', 'payload']}
            }
        }

        # Common telemetry for all subsystems
        self.common_telemetry = {
            'parameters': {
                'state': {
                    'type': TelemetryType.STRING,
                    'enum': SubsystemState,
                    'description': 'Subsystem state'
                },
                'temperature': {
                    'type': TelemetryType.FLOAT,
                    'unit': 'degC',
                    'description': 'Subsystem temperature'
                },
                'heater_setpoint': {
                    'type': TelemetryType.FLOAT,
                    'unit': 'degC',
                    'description': 'Heater setpoint temperature'
                },
                'power_draw': {
                    'type': TelemetryType.FLOAT,
                    'unit': 'W',
                    'description': 'Total power consumption'
                }
            }
        }

        # Common telecommands for all subsystems
        self.common_telecommands = {
            'SET_STATE': {
                'code': 1,
                'parameters': {
                    'state': {
                        'type': TelemetryType.STRING,
                        'enum': SubsystemState,
                        'description': 'Desired subsystem state'
                    }
                }
            },
            'SET_HEATER': {
                'code': 2,
                'parameters': {
                    'enabled': {
                        'type': TelemetryType.BOOLEAN,
                        'description': 'Heater enabled state'
                    }
                }
            },
            'SET_HEATER_SETPOINT': {
                'code': 3,
                'parameters': {
                    'temperature': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'degC',
                        'description': 'Desired heater setpoint'
                    }
                }
            }
        }

        # Subsystem-specific telemetry and telecommands
        self.telemetry = {
            'OBC': {
                'apid': 100,
                'parameters': {
                    **self.common_telemetry['parameters'],
                    'mode': {
                        'type': TelemetryType.STRING,
                        'options': ['SAFE', 'NOMINAL', 'PAYLOAD'],
                        'description': 'Spacecraft operation mode'
                    }
                }
            },
            'POWER': {
                'apid': 101,
                'parameters': {
                    **self.common_telemetry['parameters'],
                    'battery_voltage': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'V',
                        'description': 'Battery voltage'
                    },
                    'battery_current': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'A',
                        'description': 'Battery current'
                    },
                    'battery_charge': {
                        'type': TelemetryType.FLOAT,
                        'unit': '%',
                        'description': 'Battery charge percentage'
                    },
                    'solar_power': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'W',
                        'description': 'Solar power generation'
                    }
                }
            },
            'ADCS': {
                'apid': 102,
                'parameters': {
                    **self.common_telemetry['parameters'],
                    'mode': {
                        'type': TelemetryType.STRING,
                        'enum': ADCSMode,
                        'description': 'Current ADCS mode'
                    },
                    'status': {
                        'type': TelemetryType.STRING,
                        'enum': ADCSStatus,
                        'description': 'Current ADCS status'
                    },
                    'quaternion': {
                        'type': TelemetryType.FLOAT,
                        'size': 4,
                        'description': 'Current attitude quaternion'
                    },
                    'angular_velocity': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'deg/s',
                        'size': 3,
                        'description': 'Angular velocity per axis'
                    },
                    'earth_latitude': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'deg',
                        'description': 'Current Earth latitude'
                    },
                    'earth_longitude': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'deg',
                        'description': 'Current Earth longitude'
                    },
                    'earth_altitude': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'km',
                        'description': 'Current altitude'
                    }
                }
            },
            'COMMS': {
                'apid': 103,
                'parameters': {
                    **self.common_telemetry['parameters'],
                    'mode': {
                        'type': TelemetryType.STRING,
                        'enum': CommsMode,
                        'description': 'Communications mode'
                    },
                    'tm_queue_size': {
                        'type': TelemetryType.UINT32,
                        'unit': 'bits',
                        'description': 'Telemetry queue size'
                    },
                    'tc_queue_size': {
                        'type': TelemetryType.UINT32,
                        'unit': 'bits',
                        'description': 'Telecommand queue size'
                    },
                    'tm_bitrate': {
                        'type': TelemetryType.UINT32,
                        'unit': 'bps',
                        'description': 'Current telemetry bitrate'
                    },
                    'tc_bitrate': {
                        'type': TelemetryType.UINT32,
                        'unit': 'bps',
                        'description': 'Current telecommand bitrate'
                    }
                }
            },
            'PAYLOAD': {
                'apid': 104,
                'parameters': {
                    **self.common_telemetry['parameters'],
                    'status': {
                        'type': TelemetryType.STRING,
                        'options': ['READY', 'BUSY'],
                        'description': 'Payload status'
                    }
                }
            },
            'DATASTORE': {
                'apid': 105,
                'parameters': {
                    **self.common_telemetry['parameters'],
                    'storage_remaining': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'MB',
                        'description': 'Remaining storage space'
                    },
                    'number_of_files': {
                        'type': TelemetryType.UINT32,
                        'description': 'Number of stored files'
                    },
                    'last_file_size': {
                        'type': TelemetryType.FLOAT,
                        'unit': 'MB',
                        'description': 'Size of last stored file'
                    },
                    'last_file_name': {
                        'type': TelemetryType.STRING,
                        'description': 'Name of last stored file'
                    }
                }
            }
        }

        self.telecommands = {
            'OBC': {
                'apid': 200,
                'commands': {
                    **self.common_telecommands,
                    'SET_MODE': {
                        'code': 10,
                        'parameters': {
                            'mode': {
                                'type': TelemetryType.STRING,
                                'options': ['SAFE', 'NOMINAL', 'PAYLOAD'],
                                'description': 'Desired spacecraft mode'
                            }
                        }
                    },
                    'RESET': {
                        'code': 11,
                        'parameters': {},
                        'description': 'Reset and initialize spacecraft'
                    }
                }
            },
            'POWER': {
                'apid': 201,
                'commands': {
                    **self.common_telecommands
                }
            },
            'ADCS': {
                'apid': 202,
                'commands': {
                    **self.common_telecommands,
                    'SET_MODE': {
                        'code': 10,
                        'parameters': {
                            'mode': {
                                'type': TelemetryType.STRING,
                                'enum': ADCSMode,
                                'description': 'Desired ADCS mode'
                            }
                        }
                    },
                    'SET_QUATERNION': {
                        'code': 11,
                        'parameters': {
                            'quaternion': {
                                'type': TelemetryType.FLOAT,
                                'size': 4,
                                'description': 'Target quaternion (mode will change to LOCK when reached)'
                            }
                        }
                    }
                }
            },
            'COMMS': {
                'apid': 203,
                'commands': {
                    **self.common_telecommands,
                    'SET_MODE': {
                        'code': 10,
                        'parameters': {
                            'mode': {
                                'type': TelemetryType.STRING,
                                'enum': CommsMode,
                                'description': 'Desired communications mode'
                            }
                        }
                    },
                    'CLEAR_TM_QUEUE': {
                        'code': 11,
                        'parameters': {},
                        'description': 'Clear telemetry queue'
                    },
                    'CLEAR_TC_QUEUE': {
                        'code': 12,
                        'parameters': {},
                        'description': 'Clear telecommand queue'
                    },
                    'SET_TM_BITRATE': {
                        'code': 13,
                        'parameters': {
                            'bitrate': {
                                'type': TelemetryType.UINT32,
                                'unit': 'bps',
                                'description': 'Desired telemetry bitrate'
                            }
                        }
                    },
                    'SET_TC_BITRATE': {
                        'code': 14,
                        'parameters': {
                            'bitrate': {
                                'type': TelemetryType.UINT32,
                                'unit': 'bps',
                                'description': 'Desired telecommand bitrate'
                            }
                        }
                    }
                }
            },
            'PAYLOAD': {
                'apid': 204,
                'commands': {
                    **self.common_telecommands,
                    'CAPTURE': {
                        'code': 10,
                        'parameters': {},
                        'description': 'Start image capture'
                    }
                }
            },
            'DATASTORE': {
                'apid': 205,
                'commands': {
                    **self.common_telecommands,
                    'CLEAR_DATASTORE': {
                        'code': 10,
                        'parameters': {},
                        'description': 'Clear all files from datastore'
                    },
                    'DELETE_LAST_FILE': {
                        'code': 11,
                        'parameters': {},
                        'description': 'Delete most recent file'
                    },
                    'TRANSFER_FILE': {
                        'code': 12,
                        'parameters': {
                            'filename': {
                                'type': TelemetryType.STRING,
                                'description': 'Name of file to transfer'
                            }
                        }
                    },
                    'TRANSFER_LAST_FILE': {
                        'code': 13,
                        'parameters': {},
                        'description': 'Transfer most recent file'
                    }
                }
            }
        }
