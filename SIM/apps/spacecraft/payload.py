import struct
from logger import SimLogger
from config import SPACECRAFT_CONFIG, SIM_CONFIG
import numpy as np
import time
import requests
import os
from PIL import Image
from io import BytesIO
from datetime import datetime

class PayloadModule:
    def __init__(self, adcs):
        self.logger = SimLogger.get_logger("PayloadModule")
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['payload']
        
        # Initialize PAYLOAD state from config
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        self.status = config['status']
        self.storage_path = SPACECRAFT_CONFIG['spacecraft']['initial_state']['datastore']['storage_path']
        self.adcs_module = adcs  # Reference to ADCS module
        self.latitude = self.adcs_module.position[0]
        self.longitude = self.adcs_module.position[1]
        self.altitude = self.adcs_module.position[2]
        self.mission_epoch = SIM_CONFIG['mission_start_time']
        self.current_time = SIM_CONFIG['mission_start_time']

        # EO Camera Configuration
        self.eo_camera = SPACECRAFT_CONFIG['spacecraft']['hardware']['eo_camera']
        self.swath = self.eo_camera['swath']
        self.resolution = self.eo_camera['resolution']
        
    def get_telemetry(self):
        """Package current PAYLOAD state into telemetry format"""
        values = [
            np.uint8(self.state),              # SubsystemState_Type (8 bits)
            np.int8(self.temperature),         # int8_degC (8 bits)
            np.int8(self.heater_setpoint),     # int8_degC (8 bits)
            np.float32(self.power_draw),       # float_W (32 bits)
            np.uint8(self.status)              # PayloadStatus_Type (8 bits)
        ]
        
        return struct.pack(">BbbfB", *values)
    
    def update(self, current_time, adcs):
        """Update PAYLOAD state"""
        self.adcs = adcs
        self.latitude = self.adcs.latitude
        self.longitude = self.adcs.longitude
        self.altitude = self.adcs.altitude
        self.current_time = current_time
        
    def process_command(self, command_id, command_data):
        """Process PAYLOAD commands (Command_ID range 50-59)"""
        self.logger.info(f"Processing PAYLOAD command {command_id}: {command_data.hex()}")
        
        try:
            if command_id == 50:    # PAYLOAD_SET_STATE
                state = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting PAYLOAD state to: {state}")
                self.state = state
                
            elif command_id == 51:   # PAYLOAD_SET_HEATER
                heater = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting PAYLOAD heater to: {heater}")
                self.heater_state = heater
                
            elif command_id == 52:   # PAYLOAD_SET_HEATER_SETPOINT
                setpoint = struct.unpack(">f", command_data)[0]
                self.logger.info(f"Setting PAYLOAD heater setpoint to: {setpoint}°C")
                self.heater_setpoint = setpoint
                
            elif command_id == 53:   # PAYLOAD_IMAGE_CAPTURE
                met_sec = struct.unpack(">I", command_data)[0]
                epoch = self.mission_epoch
                current_time = self.current_time
                lat = self.latitude
                lon = self.longitude
                alt = self.altitude
                res = self.resolution
                swath = self.swath
                self.logger.info(f"Starting image capture at MET seconds: {met_sec}, Lat: {lat}, Lon: {lon}, Alt: {alt}, Res: {res}, Swath: {swath}")
                if self.state == 2:  # Only if powered ON
                    self._capture_image(met_sec, epoch, current_time, lat, lon, alt, res, swath)
                
            else:
                self.logger.warning(f"Unknown PAYLOAD command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking PAYLOAD command {command_id}: {e}")


    def _capture_image(self, met_sec, epoch, current_time, lat, lon, alt, res, swath):
        """Capture an image at the specified MET seconds"""
        self.logger.debug(f"Current time: {current_time}")
        self.logger.debug(f"Epoch: {epoch}")
        self.logger.debug(f"Current MET seconds: {(current_time - epoch).total_seconds()}")
        self.logger.debug(f"Capturing image at MET seconds: {met_sec}, Lat: {lat}, Lon: {lon}, Alt: {alt}, Res: {res}, Swath: {swath}")
        
        wait_time = met_sec - (current_time - epoch).total_seconds()
        while wait_time > 0:
            self.logger.debug(f"Waiting for {wait_time} seconds before capturing image")
            time.sleep(1)
            wait_time -= 1
        
        self.logger.debug("Capturing image")
        try:
            self.status = 1  # Set to CAPTURING

            zoom = 12  # google api specific value that is roughly the swath width at equator
            
            # Build API request
            params = {
                'center': f'{lat},{lon}',  # Use spacecraft's actual position
                'zoom': zoom,
                'size': f'{res}x{res}',  # 1024x1024 pixels
                'maptype': 'satellite',
                'key': 'AIzaSyDL__brVoZ4VY72_ZnRl5MhLnWLpuP4bsA',
                'scale': 2  # Request high-resolution tiles
            }

            self.logger.info(f"Capturing {res}x{res} image at position (lat={lat}, lon={lon}) at zoom level {zoom}")
            
            # Create filename that increments with each capture
            filename = f"EO_image_met_{met_sec}.png"
            filepath = os.path.join(self.storage_path, filename)

            # Ensure storage directory exists
            os.makedirs(self.storage_path, exist_ok=True)

            # Make API request
            base_url = "https://maps.googleapis.com/maps/api/staticmap"
            response = requests.get(base_url, params=params)
            img = Image.open(BytesIO(response.content))
            
            # Resize to exactly resxres if needed
            if img.size != (res, res):
                img = img.resize((res, res), Image.Resampling.LANCZOS)
            
            # Save the image in PNG format
            img.save(filepath, 'PNG')
            self.logger.info(f"Saved {img.size} image to {filepath}")
            
            # Update payload status to indicate capture complete
            self.status = 0  # Back to IDLE
            
        except Exception as e:
            self.logger.error(f"Error capturing/saving image: {e}")
            self.status = 0  # Set back to IDLE on error
        return
