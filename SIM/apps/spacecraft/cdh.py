import struct
from logger import SimLogger

class CDHModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("CDHModule")
        self.sequence_count = 0
        self.adcs_temperature = -10  # Move from comms to here
        
    def create_tm_packet(self):
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

        # Format string for all parameters
        fmt = ">"
        fmt += "BBBfB"     # OBC parameters
        fmt += "BBBfB"     # CDH parameters
        fmt += "BBBfffff"  # POWER parameters
        fmt += "ffff"      # POWER solar parameters
        fmt += "BbBfBB"    # ADCS parameters
        fmt += "ffff"      # ADCS quaternion
        fmt += "fff"       # ADCS angular velocity
        fmt += "fffB"      # ADCS position and eclipse
        fmt += "BBBfB"     # COMMS parameters
        fmt += "IIII"      # COMMS queue and bitrate
        fmt += "BBBfB"     # PAYLOAD parameters
        fmt += "BBBffI"    # DATASTORE parameters
        
        # Get latest parameter values
        values = []

        # OBC Parameters
        values.append(2)           # OBC_state (uint8) - TODO: Get from OBC subsystem
        values.append(20)          # OBC_temperature (uint8) - TODO: Get from OBC subsystem
        values.append(25)          # OBC_heater_setpoint (uint8) - TODO: Get from OBC subsystem
        values.append(2.5)         # OBC_power_draw (float) - TODO: Get from OBC subsystem
        values.append(1)           # OBC_mode (uint8) - TODO: Get from OBC subsystem

        # CDH Parameters
        values.append(2)           # CDH_state (uint8) - TODO: Get from CDH subsystem
        values.append(22)          # CDH_temperature (uint8) - TODO: Get from CDH subsystem
        values.append(25)          # CDH_heater_setpoint (uint8) - TODO: Get from CDH subsystem
        values.append(2.0)         # CDH_power_draw (float) - TODO: Get from CDH subsystem
        values.append(2)           # POWER_state (uint8) - TODO: Get from POWER subsystem

        # POWER Parameters
        values.append(23)          # POWER_temperature (uint8) - TODO: Get from POWER subsystem
        values.append(25)          # POWER_heater_setpoint (uint8) - TODO: Get from POWER subsystem
        values.append(10)          # POWER_power_draw (uint8) - TODO: Get from POWER subsystem
        values.append(7.4)         # POWER_battery_voltage (float) - TODO: Get from POWER subsystem
        values.append(1.2)         # POWER_battery_current (float) - TODO: Get from POWER subsystem
        values.append(85.0)        # POWER_battery_charge (float) - TODO: Get from POWER subsystem
        values.append(0.0)         # POWER_total_power_balance (float) - TODO: Get from POWER subsystem
        values.append(100.0)       # POWER_solar_total_generation (float) - TODO: Get from POWER subsystem

        # POWER Solar Parameters
        values.append(25.0)        # POWER_solar_panel_generation_pX (float) - TODO: Get from POWER subsystem
        values.append(25.0)        # POWER_solar_panel_generation_nX (float) - TODO: Get from POWER subsystem
        values.append(25.0)        # POWER_solar_panel_generation_pY (float) - TODO: Get from POWER subsystem
        values.append(25.0)        # POWER_solar_panel_generation_nY (float) - TODO: Get from POWER subsystem

        # ADCS Parameters
        values.append(2)           # ADCS_state (uint8) - TODO: Get from ADCS subsystem
        values.append(22)          # ADCS_temperature (int8) - TODO: Get from ADCS subsystem
        values.append(25)          # ADCS_heater_setpoint (uint8) - TODO: Get from ADCS subsystem
        values.append(5.0)         # ADCS_power_draw (float) - TODO: Get from ADCS subsystem
        values.append(2)           # ADCS_mode (uint8) - TODO: Get from ADCS subsystem
        values.append(2)           # ADCS_status (uint8) - TODO: Get from ADCS subsystem

        # ADCS Quaternion
        values.append(0.707)       # ADCS_quaternion_q1 (float) - TODO: Get from ADCS subsystem
        values.append(0.0)         # ADCS_quaternion_q2 (float) - TODO: Get from ADCS subsystem
        values.append(0.0)         # ADCS_quaternion_q3 (float) - TODO: Get from ADCS subsystem
        values.append(0.707)       # ADCS_quaternion_q4 (float) - TODO: Get from ADCS subsystem

        # ADCS Angular Velocity
        values.append(0.1)         # ADCS_angular_velocity_x (float) - TODO: Get from ADCS subsystem
        values.append(0.1)         # ADCS_angular_velocity_y (float) - TODO: Get from ADCS subsystem
        values.append(0.1)         # ADCS_angular_velocity_z (float) - TODO: Get from ADCS subsystem

        # ADCS Position and Eclipse
        values.append(0.0)         # ADCS_earth_latitude (float) - TODO: Get from ADCS subsystem
        values.append(0.0)         # ADCS_earth_longitude (float) - TODO: Get from ADCS subsystem
        values.append(400.0)       # ADCS_earth_altitude (float) - TODO: Get from ADCS subsystem
        values.append(0)           # ADCS_eclipse (uint8) - TODO: Get from ADCS subsystem

        # COMMS Parameters
        values.append(2)           # COMMS_state (uint8) - TODO: Get from COMMS subsystem
        values.append(22)          # COMMS_temperature (uint8) - TODO: Get from COMMS subsystem
        values.append(25)          # COMMS_heater_setpoint (uint8) - TODO: Get from COMMS subsystem
        values.append(3.0)         # COMMS_power_draw (float) - TODO: Get from COMMS subsystem
        values.append(2)           # COMMS_mode (uint8) - TODO: Get from COMMS subsystem

        # COMMS Queue and Bitrate
        values.append(1024)        # COMMS_tm_queue_size (uint32) - TODO: Get from COMMS subsystem
        values.append(512)         # COMMS_tc_queue_size (uint32) - TODO: Get from COMMS subsystem
        values.append(9600)        # COMMS_tm_bitrate (uint32) - TODO: Get from COMMS subsystem
        values.append(9600)        # COMMS_tc_bitrate (uint32) - TODO: Get from COMMS subsystem

        # PAYLOAD Parameters
        values.append(2)           # PAYLOAD_state (uint8) - TODO: Get from PAYLOAD subsystem
        values.append(21)          # PAYLOAD_temperature (uint8) - TODO: Get from PAYLOAD subsystem
        values.append(25)          # PAYLOAD_heater_setpoint (uint8) - TODO: Get from PAYLOAD subsystem
        values.append(2.0)         # PAYLOAD_power_draw (float) - TODO: Get from PAYLOAD subsystem
        values.append(0)           # PAYLOAD_status (uint8) - TODO: Get from PAYLOAD subsystem

        # DATASTORE Parameters
        values.append(2)           # DATASTORE_state (uint8) - TODO: Get from DATASTORE subsystem
        values.append(20)          # DATASTORE_temperature (uint8) - TODO: Get from DATASTORE subsystem
        values.append(25)          # DATASTORE_heater_setpoint (uint8) - TODO: Get from DATASTORE subsystem
        values.append(1.5)         # DATASTORE_power_draw (float) - TODO: Get from DATASTORE subsystem
        values.append(1000.0)      # DATASTORE_storage_remaining (float) - TODO: Get from DATASTORE subsystem
        values.append(10)          # DATASTORE_number_of_files (uint32) - TODO: Get from DATASTORE subsystem
        
        # Create data section with all parameters in XTCE order
        data = struct.pack(fmt, *values)
        
        # Calculate packet length (minus 1 per CCSDS standard)
        packet_length = len(data) - 1
        
        # Create the complete packet
        packet = struct.pack(">HHH", first_word, second_word, packet_length) + data
        
        self.sequence_count += 1
        return packet

    def process_command(self, command_data):
        """Process incoming telecommands"""
        hex_data = command_data.hex()
        self.logger.info(f"Processing TC: {hex_data}")
        # TODO: Add actual command processing logic
