import time
import signal
import sys
from datetime import datetime, timedelta
from apps.spacecraft.cdh import CDHModule
from config import SIM_CONFIG
from logger import SimLogger

class Simulator:
    _sim_time = SIM_CONFIG['mission_start_time']  # Initialize at class level
    
    @classmethod
    def get_sim_time(cls):
        return cls._sim_time  # Simply return the current simulation time

    def __init__(self):
        self.logger = SimLogger.get_logger("Simulator")
        
        # Initialize CDH (which initializes all other subsystems)
        self.cdh = CDHModule()
        
        # Start the COMMS module
        self.cdh.comms.start()
        
        # Get simulation configuration
        self.mission_start_time = SIM_CONFIG['mission_start_time']
        self.time_step = SIM_CONFIG['time_step']
        self.time_factor = SIM_CONFIG['time_factor']
        
        # Initialize simulation time
        self.current_time = self.mission_start_time
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.logger.info(f"Simulator started - Mission start time: {self.mission_start_time}")
        self.logger.info(f"Time step: {self.time_step}s, Time factor: {self.time_factor}x")
        self.logger.info("Press Ctrl+C to stop the simulator")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("\nShutdown signal received. Stopping simulator...")
        self.stop()
        sys.exit(0)

    def run(self):
        self.running = True
        
        try:
            while self.running:
                # Debug logging for time updates
                self.logger.debug(f"Before update - Sim time: {Simulator._sim_time}")
                
                # Update simulation time - use time_factor here
                Simulator._sim_time += timedelta(seconds=self.time_step * self.time_factor)
                self.current_time = Simulator._sim_time
                
                # Debug logging after update
                self.logger.debug(f"After update - Sim time: {Simulator._sim_time}")
                
                # Update subsystems
                self.cdh.adcs.update(self.current_time)
                self.cdh.power.update(self.current_time, self.cdh.adcs)
                #self.cdh.payload.update(self.current_time)
                #self.cdh.obc.update(self.current_time)
                
                # Create telemetry packet through CDH
                tm_packet = self.cdh.create_tm_packet()
                
                # Send telemetry packet through COMMS
                self.cdh.comms.send_tm_packet(tm_packet)
                
                # Sleep for time_step adjusted by time_factor
                time.sleep(self.time_step / self.time_factor)
                
        except Exception as e:
            self.logger.error(f"Error in simulation loop: {str(e)}")
            self.stop()

    def stop(self):
        """Clean shutdown of simulator"""
        self.running = False
        self.logger.info("Stopping COMMS module...")
        self.cdh.comms.stop()
        self.logger.info("Simulator stopped")

if __name__ == "__main__":
    simulator = Simulator()
    simulator.run()
