import time
import logging
from datetime import datetime, timedelta
from apps.spacecraft.comms import CommsModule
from apps.spacecraft.cdh import CDHModule
from config import SIM_CONFIG, SPACECRAFT_CONFIG, UNIVERSE_CONFIG
from logger import SimLogger, LOG_LEVEL, LOG_RATE

class Simulator:
    def __init__(self, mission_start_time=None, time_step=None, time_factor=None):
        """Initialize the simulator"""
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("Simulator")
        
        # Set simulation timing parameters from config (with optional overrides)
        self.mission_start_time = mission_start_time or SIM_CONFIG['mission_start_time']
        self.time_step = time_step or SIM_CONFIG['time_step']
        self.time_factor = time_factor or SIM_CONFIG['time_factor']
        self.mission_elapsed_time = timedelta(seconds=0)
        
        # Initialize subsystems with config
        self.cdh = CDHModule()
        self.comms = CommsModule(self.cdh)
        
        # Control flags
        self.running = False
        
    def start(self):
        """Start the simulator"""
        self.running = True
        self.comms.start()
        self.logger.info(f"Simulator started - Mission start time: {self.mission_start_time}")
        self.logger.info(f"Time step: {self.time_step}s, Time factor: {self.time_factor}x")
        
        # Main simulation loop
        last_update = time.time()
        
        while self.running:
            try:
                # Calculate time until next update
                current_time = time.time()
                elapsed = current_time - last_update
                sleep_time = (self.time_step / self.time_factor) - elapsed
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Update simulation time
                self.mission_elapsed_time += timedelta(seconds=self.time_step)
                current_mission_time = self.mission_start_time + self.mission_elapsed_time
                
                # Log simulation time every LOG_RATE seconds
                if self.mission_elapsed_time.seconds % LOG_RATE == 0:
                    self.logger.info(f"Mission Time: {current_mission_time}")
                    self.logger.info(f"Mission Elapsed Time: {self.mission_elapsed_time}")
                
                # Update subsystems
                self._update_subsystems()
                
                last_update = time.time()
                
            except KeyboardInterrupt:
                self.stop()
                break
            
            except Exception as e:
                self.logger.error(f"Error in simulation loop: {e}")
                self.stop()
                break
    
    def stop(self):
        """Stop the simulator"""
        self.running = False
        self.comms.stop()
        self.logger.info("Simulator stopped")
    
    def _update_subsystems(self):
        """Update all subsystem states"""
        # Update ADCS temperature
        self.cdh.adcs_temperature += 1
        # Send telemetry
        self.comms.send_tm_packet()

if __name__ == "__main__":
    # Use configuration from config.py
    sim = Simulator()
    
    try:
        sim.start()
    except KeyboardInterrupt:
        sim.stop()
