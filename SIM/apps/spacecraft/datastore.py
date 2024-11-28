import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG, SIM_CONFIG
import numpy as np
import os
import shutil
import time

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
        self.storage_path = config['storage_path']
        self.storage_total = config['storage_total']
        self.storage_used = 0   # Always start with 0 bytes used
        self.files_stored = 0   # Always start with 0 files
        self.storage_remaining = self.storage_total - self.storage_used
        self.number_of_files = self.files_stored
        self.mode = config['mode']
        self.transfer_progress = 0
    def get_telemetry(self):
        """Package current DATASTORE state into telemetry format"""
        self.files = os.listdir(self.storage_path)
        self.number_of_files = len(self.files)
        self.storage_used = sum(os.path.getsize(os.path.join(self.storage_path, file)) for file in self.files)
        self.storage_remaining = self.storage_total - self.storage_used

        values = [
            np.uint8(self.state),                # SubsystemState_Type (8 bits)
            np.int8(self.temperature),           # int8_degC (8 bits)
            np.int8(self.heater_setpoint),       # int8_degC (8 bits)
            np.float32(self.power_draw),         # float_W (32 bits)
            np.float32(self.storage_remaining),  # float_MB (32 bits)
            np.uint32(self.number_of_files),     # uint32 (32 bits)
            np.uint8(self.mode),                  # DatastoreMode_Type (8 bits)
            np.float32(self.transfer_progress)     # uint32 (8 bits)
        ]
        
        return struct.pack(">BbbffIBf", *values)
        
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
                for file in self.files:
                    os.remove(os.path.join(self.storage_path, file))
                
            elif command_id == 64:   # DATASTORE_TRANSFER_FILE
                filename = command_data.decode('utf-8').strip('\x00')
                self.files = os.listdir(self.storage_path)
                self.logger.info(f"Initiating transfer of file: {filename}")
                if filename in self.files:
                    self.mode = 1  # TRANSFERRING
                    file_size = os.path.getsize(os.path.join(self.storage_path, filename))
                    bitrate = SPACECRAFT_CONFIG['spacecraft']['initial_state']['comms']['downlink_bitrate']
                    total_duration = (file_size * 8) / bitrate
                    percentage_complete = 0
                    duration = 0
                    while duration < total_duration: 
                        percentage_complete = (duration / total_duration) * 100
                        self.logger.info(f"Transfer progress: {percentage_complete}%")
                        self.logger.info(f"Total Transfer Duration: {total_duration} seconds")
                        duration += 1
                        time.sleep(1)
                        self.transfer_progress = percentage_complete
                    try:
                        shutil.copy(os.path.join(self.storage_path, filename), os.path.join('../../', SIM_CONFIG['download_directory'], filename))
                        self.mode = 0  # IDLE
                    except Exception as e:
                        self.logger.debug(f"Transfer directory: {os.path.join('../../', SIM_CONFIG['download_directory'])}")
                        self.logger.error(f"Error transferring file: {e}")
                    self.transfer_progress = 0
                else:
                    self.logger.warning(f"File not found: {filename}")
                
            else:
                self.logger.warning(f"Unknown DATASTORE command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking DATASTORE command {command_id}: {e}")
