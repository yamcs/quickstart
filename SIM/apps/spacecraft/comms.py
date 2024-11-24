import socket
import threading
import binascii
from logger import SimLogger
from config import SPACECRAFT_CONFIG
from apps.spacecraft.cdh import CDHModule   

class CommsModule:
    def __init__(self, cdh):
        self.logger = SimLogger.get_logger("CommsModule")
        self.cdh = CDHModule()
        
        # TC (Telecommand) socket configuration
        self.tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.TC_PORT = SPACECRAFT_CONFIG['comms']['tc_port']
        self.tc_socket.bind((SPACECRAFT_CONFIG['comms']['host'], self.TC_PORT))
        
        # TM (Telemetry) socket configuration
        self.tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.TM_PORT = SPACECRAFT_CONFIG['comms']['tm_port']
        
        self.running = False
    
    def start(self):
        """Start the communications module"""
        self.running = True
        self.tc_thread = threading.Thread(target=self._tc_listener)
        self.tc_thread.daemon = True
        self.tc_thread.start()
        self.logger.info(f"CommsModule started - Listening for telecommands on port {self.TC_PORT}")
    
    def stop(self):
        """Stop the communications module"""
        self.running = False
        self.tc_socket.close()
        self.tm_socket.close()
        self.logger.info("CommsModule stopped")
    
    def send_tm_packet(self):
        """Send telemetry packet"""
        try:
            # Get telemetry packet from CDH
            tm_packet = self.cdh.create_tm_packet()
            
            # Send packet
            self.tm_socket.sendto(tm_packet, (SPACECRAFT_CONFIG['comms']['host'], self.TM_PORT))
            hex_data = binascii.hexlify(tm_packet).decode('ascii')
            self.logger.info(f"Sent TM: {hex_data}")
            
        except socket.error as e:
            self.logger.error(f"Socket error while sending TM: {e}")
    
    def _tc_listener(self):
        """Listen for incoming telecommands"""
        while self.running:
            try:
                data, addr = self.tc_socket.recvfrom(1024)
                self.logger.info(f"Received TC from {addr}")
                # Forward command to CDH for processing
                self.cdh.process_command(data)
            except socket.error as e:
                if self.running:
                    self.logger.error(f"Socket error: {e}")
                break
