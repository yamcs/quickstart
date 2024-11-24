import socket
import logging
import threading
import time
import binascii
import struct

class CommsModule:
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("CommsModule")
        
        # TC (Telecommand) socket configuration
        self.tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.TC_PORT = 10025
        self.tc_socket.bind(('localhost', self.TC_PORT))
        
        # TM (Telemetry) socket configuration
        self.tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.TM_PORT = 10015
        
        self.running = False
        self.sequence_count = 0
        self.adcs_temperature = -10  # Starting temperature
    
    def start(self):
        """Start the communications module"""
        self.running = True
        self.tc_thread = threading.Thread(target=self._tc_listener)
        self.tm_thread = threading.Thread(target=self._tm_sender)
        self.tc_thread.daemon = True
        self.tm_thread.daemon = True
        self.tc_thread.start()
        self.tm_thread.start()
        self.logger.info("CommsModule started - Listening for telecommands on port %d", self.TC_PORT)
    
    def stop(self):
        """Stop the communications module"""
        self.running = False
        self.tc_socket.close()
        self.tm_socket.close()
        self.logger.info("CommsModule stopped")
    
    def _create_tm_packet(self):
        """Create a CCSDS telemetry packet with all housekeeping parameters in XTCE order"""
        # CCSDS Primary Header (6 bytes = 48 bits)
        version = 0
        packet_type = 0  # TM
        sec_hdr_flag = 0
        apid = 100  # Housekeeping
        sequence_flags = 3  # Standalone packet
        packet_sequence_count = self.sequence_count & 0x3FFF  # 14 bits
        
        # First 2 bytes: Version(3), Type(1), Sec Hdr Flag(1), APID(11)
        first_word = (version << 13) | (packet_type << 12) | (sec_hdr_flag << 11) | apid
        
        # Next 2 bytes: Sequence Flags(2), Sequence Count(14)
        second_word = (sequence_flags << 14) | packet_sequence_count
        
        fmt = ">BBBfB"  # OBC (5)
        fmt += "BBBfB"  # CDH (5)
        fmt += "BBBfffff"  # POWER (8)
        fmt += "ffff"  # POWER solar (4)
        fmt += "BbBfBB"  # ADCS (6)
        fmt += "ffff"  # ADCS quaternion (4)
        fmt += "fff"   # ADCS angular velocity (3)
        fmt += "fffB"  # ADCS position and eclipse (4)
        fmt += "BBBfB"  # COMMS (5)
        fmt += "IIII"  # COMMS queue and bitrate (4)
        fmt += "BBBfB"  # PAYLOAD (5)
        fmt += "BBBffI"  # DATASTORE (6)
        
        # Create list of values with explicit type conversion
        values = []
        
        # OBC (5)
        values.extend([int(2), int(20), int(25), float(2.5), int(1)])
        # CDH (5)
        values.extend([int(2), int(22), int(25), float(2.0), int(2)])
        # POWER (8)
        values.extend([int(23), int(25), int(10), float(7.4), float(1.2), 
                      float(85.0), float(0.0), float(100.0)])
        # POWER solar (4)
        values.extend([float(25.0), float(25.0), float(25.0), float(25.0)])
        # ADCS (6) - Fixed order and using signed temperature
        values.extend([int(2),                    # ADCS_state (unsigned)
                      int(self.adcs_temperature), # ADCS_temperature (signed)
                      int(25),                    # ADCS_heater_setpoint (unsigned)
                      float(5.0),                 # ADCS_power_draw
                      int(2),                     # ADCS_mode (unsigned)
                      int(2)])                    # ADCS_status (unsigned)
        # ADCS quaternion (4)
        values.extend([float(0.707), float(0.0), float(0.0), float(0.707)])
        # ADCS angular velocity (3)
        values.extend([float(0.1), float(0.1), float(0.1)])
        # ADCS position and eclipse (4)
        values.extend([float(0.0), float(0.0), float(400.0), int(0)])
        # COMMS (5)
        values.extend([int(2), int(22), int(25), float(3.0), int(2)])
        # COMMS queue and bitrate (4)
        values.extend([int(1024), int(512), int(9600), int(9600)])
        # PAYLOAD (5)
        values.extend([int(2), int(21), int(25), float(2.0), int(0)])
        # DATASTORE (6)
        values.extend([int(2), int(20), int(25), float(1.5), float(1000.0), int(10)])

        # Debug print each value and its type
        print("\nValues and their types:")
        for i, (f, v) in enumerate(zip(fmt[1:], values)):  # Skip the '>' in fmt
            print(f"Value {i}: format '{f}', value {v} ({type(v)})")
        
        # Create data section with all parameters in XTCE order
        data = struct.pack(fmt, *values)
        
        # Calculate packet length (minus 1 per CCSDS standard)
        packet_length = len(data) - 1
        
        # Create the complete packet
        packet = struct.pack(">HHH", first_word, second_word, packet_length) + data
        
        self.sequence_count += 1
        return packet
    
    def _tc_listener(self):
        """Listen for incoming telecommands"""
        while self.running:
            try:
                data, addr = self.tc_socket.recvfrom(1024)
                hex_data = binascii.hexlify(data).decode('ascii')
                self.logger.info(f"Received TC: {hex_data} from {addr}")
            except socket.error as e:
                if self.running:
                    self.logger.error(f"Socket error: {e}")
                break
    
    def _tm_sender(self):
        """Send telemetry packets"""
        while self.running:
            try:
                # Increment temperature before creating packet
                self.adcs_temperature += 1
                
                # Create and send telemetry packet
                tm_packet = self._create_tm_packet()
                self.tm_socket.sendto(tm_packet, ('localhost', self.TM_PORT))
                hex_data = binascii.hexlify(tm_packet).decode('ascii')
                self.logger.info(f"Sent TM: {hex_data}")
                
                # Wait 1 second
                time.sleep(1)
                
            except socket.error as e:
                self.logger.error(f"Socket error while sending TM: {e}")
                break

if __name__ == "__main__":
    # Test the module
    comms = CommsModule()
    try:
        comms.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        comms.stop()
