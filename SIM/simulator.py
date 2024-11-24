import time
from datetime import datetime, timedelta
from apps.spacecraft.cdh import CDHModule
from config import SIM_CONFIG
from logger import SimLogger

class Simulator:
    def __init__(self):
        self.logger = SimLogger.get_logger("Simulator")
        
        # Initialize CDH (which initializes all other subsystems)
        self.cdh = CDHModule()
        
        # Get simulation configuration
        self.mission_start_time = SIM_CONFIG['mission_start_time']
        self.time_step = SIM_CONFIG['time_step']
        self.time_factor = SIM_CONFIG['time_factor']
        
        # Initialize simulation time
        self.current_time = self.mission_start_time
        self.running = False
        
        self.logger.info(f"Simulator started - Mission start time: {self.mission_start_time}")
        self.logger.info(f"Time step: {self.time_step}s, Time factor: {self.time_factor}x")

    def run(self):
        self.running = True
        
        try:
            while self.running:
                # Create telemetry packet through CDH
                tm_packet = self.cdh.create_tm_packet()
                
                # Send telemetry packet through COMMS
                self.cdh.comms.send_tm_packet(tm_packet)
                
                # Update simulation time
                self.current_time += timedelta(seconds=self.time_step)
                
                # Sleep for time_step adjusted by time_factor
                time.sleep(self.time_step / self.time_factor)
                
        except Exception as e:
            self.logger.error(f"Error in simulation loop: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False
        self.cdh.comms.stop()
        self.logger.info("Simulator stopped")

if __name__ == "__main__":
    simulator = Simulator()
    simulator.run()
