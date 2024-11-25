import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG
import numpy as np

class DatastoreModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("DatastoreModule")
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['datastore']
        
        # Initialize DATASTORE state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        
        # Storage parameters
        self.storage_total = config['storage_total']
        self.storage_used = 0   # Always start with 0 bytes used
        self.files_stored = 0   # Always start with 0 files
        self.files = []        # Always start with empty file list
        self.storage_remaining = self.storage_total - self.storage_used
        self.number_of_files = self.files_stored
        
    def get_telemetry(self):
        """Package current DATASTORE state into telemetry format"""
        values = [
            np.uint8(self.state),                # SubsystemState_Type (8 bits)
            np.int8(self.temperature),           # int8_degC (8 bits)
            np.int8(self.heater_setpoint),       # int8_degC (8 bits)
            np.float32(self.power_draw),         # float_W (32 bits)
            np.float32(self.storage_remaining),  # float_MB (32 bits)
            np.uint32(self.number_of_files)      # uint32 (32 bits)
        ]
        
        return struct.pack(">BbbffI", *values)
        
    def process_command(self, command_id, command_data):
        """Process DATASTORE commands (Command_ID range 60-69)"""
        self.logger.info(f"Processing DATASTORE command {command_id}: {command_data.hex()}")
        
        try:
            if command_id == 60:    # DATASTORE_SET_STATE
                state = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting DATASTORE state to: {state}")
                self.state = state
                
            elif command_id == 61:   # DATASTORE_SET_HEATER
                heater = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting DATASTORE heater to: {heater}")
                self.heater_state = heater
                
            elif command_id == 62:   # DATASTORE_SET_HEATER_SETPOINT
                setpoint = struct.unpack(">f", command_data)[0]
                self.logger.info(f"Setting DATASTORE heater setpoint to: {setpoint}°C")
                self.heater_setpoint = setpoint
                
            elif command_id == 63:   # DATASTORE_CLEAR_DATASTORE
                self.logger.info("Clearing all files from DATASTORE")
                self.files = []
                self.files_stored = 0
                self.storage_used = 0
                
            elif command_id == 64:   # DATASTORE_DELETE_LAST_FILE
                if self.files:
                    last_file = self.files.pop()
                    self.files_stored -= 1
                    self.logger.info(f"Deleted last file: {last_file}")
                else:
                    self.logger.warning("No files to delete")
                
            elif command_id == 65:   # DATASTORE_TRANSFER_FILE
                filename = command_data.decode('utf-8').strip('\x00')
                self.logger.info(f"Initiating transfer of file: {filename}")
                if filename in self.files:
                    self.mode = 1  # TRANSFERRING
                    self.transfer_progress = 0
                else:
                    self.logger.warning(f"File not found: {filename}")
                
            elif command_id == 66:   # DATASTORE_TRANSFER_LAST_FILE
                if self.files:
                    last_file = self.files[-1]
                    self.logger.info(f"Initiating transfer of last file: {last_file}")
                    self.mode = 1  # TRANSFERRING
                    self.transfer_progress = 0
                else:
                    self.logger.warning("No files to transfer")
                
            else:
                self.logger.warning(f"Unknown DATASTORE command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking DATASTORE command {command_id}: {e}")
