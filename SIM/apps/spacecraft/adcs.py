import numpy as np
from ..universe.environment import Environment
from ..universe.orbit import OrbitPropagator
from config import SPACECRAFT_CONFIG, SIM_CONFIG
from logger import SimLogger
import struct

class ADCSModule:
    def __init__(self):
        self.logger = SimLogger.get_logger("ADCSModule")
        
        # Initialize from config
        config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['adcs']
        self.state = config['state']
        self.temperature = config['temperature']
        self.heater_setpoint = config['heater_setpoint']
        self.power_draw = config['power_draw']
        self.mode = config['mode']
        self.status = config['status']

        # Get configuration values
        self.dt = SIM_CONFIG['time_step']
        adcs_config = SPACECRAFT_CONFIG['spacecraft']['initial_state']['adcs']
        adcs_hw_config = SPACECRAFT_CONFIG['spacecraft']['hardware']['adcs']
        
        # Initialize attitude state from config
        self.quaternion = np.array(adcs_config['quaternion'])
        self.angular_velocity = np.array(adcs_config['angular_velocity']) * np.pi/180.0  # Convert deg/s to rad/s
        
        # Initialize mode and status from config
        self.mode = adcs_config['mode']
        self.status = adcs_config['status']
        
        # Get pointing requirements from config
        self.accuracy_threshold = adcs_hw_config['pointing_requirements']['accuracy_threshold']
        self.stability_duration = adcs_hw_config['pointing_requirements']['stability_duration']
        self.max_slew_rate = adcs_hw_config['pointing_requirements']['max_slew_rate']
        self.nominal_slew_rate = adcs_hw_config['pointing_requirements']['nominal_slew_rate']
        
        # Initialize attitude and position
        self.quaternion = np.array(config['quaternion'])
        self.angular_velocity = np.array(config['angular_velocity'])
        self.position = np.array(config['position'])
        self.eclipse = config['eclipse']
        
        # Initialize environment and orbit
        self.environment = Environment()
        self.orbit_propagator = OrbitPropagator()
        
        # Track last update time
        self.last_update_time = SIM_CONFIG['mission_start_time']
        
        # Get hardware config
        hw_config = SPACECRAFT_CONFIG['spacecraft']['hardware']['adcs']
        self.pointing_accuracy = hw_config['pointing_requirements']['accuracy_threshold']
        self.pointing_duration = hw_config['pointing_requirements']['stability_duration']
        self.pointing_start_time = None
        
        # Get actuator limits
        self.max_magnetic_moment = hw_config['magnetorquers']['x']['max_moment']  # Assuming symmetric
        self.max_wheel_torque = hw_config['reaction_wheels']['x']['max_torque']   # Assuming symmetric
        
        self.time_step = SIM_CONFIG['time_step']
        
        self.logger.info("ADCS Module initialized")
        
    def update(self, current_time):
        """Update ADCS state"""
        if current_time == self.last_update_time:
            return
            
        try:
            # Get new orbital state
            orbit_state = self.orbit_propagator.propagate(current_time)
            
            # Debug logging
            self.logger.debug(f"Orbit state: {orbit_state}")
            
            # Update position and eclipse state
            old_position = self.position.copy()
            self.position = [
                orbit_state['lat'],
                orbit_state['lon'],
                orbit_state['alt']
            ]
            
            # More debug logging
            self.logger.debug(f"New position: lat={self.position[0]:.2f}, lon={self.position[1]:.2f}, alt={self.position[2]:.2f}")
            
            old_eclipse = self.eclipse
            self.eclipse = 1 if orbit_state['eclipse'] else 0
            
            # Calculate environmental effects
            self.density = self.environment.atmospheric_density(orbit_state['alt'])
            sun_pos = self.orbit_propagator.sun.get_position_at_time(current_time)
            self.panel_angles = self.environment.solar_illumination(
                orbit_state['position'],
                sun_pos,
                self.quaternion
            )
            
            # Update attitude based on mode
            self._update_attitude(orbit_state)
            
            # Log significant changes
            if np.any(np.abs(np.array(self.position) - np.array(old_position)) > 0.1):
                self.logger.debug(f"Position updated: lat={self.position[0]:.1f}°, " +
                                f"lon={self.position[1]:.1f}°, alt={self.position[2]:.1f}km")
            
            if self.eclipse != old_eclipse:
                self.logger.info(f"Eclipse state changed: {'ECLIPSE' if self.eclipse else 'SUNLIGHT'}")
            
            self.last_update_time = current_time

            self.logger.debug(f"ADCS state updated - pos: {self.position}, q: {self.quaternion}")
            
        except Exception as e:
            self.logger.error(f"Error updating ADCS state: {str(e)}")
            self.status = 0  # Set to UNCONTROLLED
        
    def get_telemetry(self):
        """Package current ADCS state into telemetry format"""
        # Debug output before packing
        self.logger.debug(f"Packing telemetry - lat: {self.position[0]}, lon: {self.position[1]}, alt: {self.position[2]}")
        self.logger.debug(f"Quaternion: {self.quaternion}")
        self.logger.debug(f"Angular velocity (deg/s): {np.degrees(self.angular_velocity)}")

        # Pack values in correct order with proper types
        values = [
            np.uint8(self.state),                    # SubsystemState_Type (8 bits)
            np.int8(self.temperature),               # int8_degC (8 bits)
            np.int8(self.heater_setpoint),           # int8_degC (8 bits)
            np.float32(self.power_draw),             # float_W (32 bits)
            np.uint8(self.mode),                     # ADCSMode_Type (8 bits)
            np.uint8(self.status),                   # ADCSStatus_Type (8 bits)
            np.float32(self.quaternion[0]),          # float (32 bits)
            np.float32(self.quaternion[1]),          # float (32 bits)
            np.float32(self.quaternion[2]),          # float (32 bits)
            np.float32(self.quaternion[3]),          # float (32 bits)
            np.float32(self.angular_velocity[0]),    # float_deg_s (32 bits)
            np.float32(self.angular_velocity[1]),    # float_deg_s (32 bits)
            np.float32(self.angular_velocity[2]),    # float_deg_s (32 bits)
            np.float32(self.position[0]),            # float_deg (32 bits)
            np.float32(self.position[1]),            # float_deg (32 bits)
            np.float32(self.position[2]),            # float_km (32 bits)
            np.uint8(self.eclipse)                   # Eclipse_Type (8 bits)
        ]
        
        # Pack using correct format string
        return struct.pack(">BbbfBBffffffffffB", *values)
        
    def process_command(self, command_id, command_data):
        """Process ADCS commands (Command_ID range 30-39)"""
        self.logger.info(f"Processing ADCS command {command_id}: {command_data.hex()}")
        
        try:
            if command_id == 30:    # ADCS_SET_STATE
                state = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting ADCS state to: {state}")
                self.state = state
                
            elif command_id == 31:   # ADCS_SET_HEATER
                heater = struct.unpack(">B", command_data)[0]
                self.logger.info(f"Setting ADCS heater to: {heater}")
                self.heater_state = heater
                
            elif command_id == 32:   # ADCS_SET_HEATER_SETPOINT
                setpoint = struct.unpack(">f", command_data)[0]
                self.logger.info(f"Setting ADCS heater setpoint to: {setpoint}°C")
                self.heater_setpoint = setpoint
                
            elif command_id == 33:  # Set ADCS mode
                new_mode = struct.unpack('B', command_data)[0]
                self.logger.info(f"Received request to change to mode: {new_mode}")
                
                # Validate mode
                if new_mode > 4:
                    self.logger.error(f"Invalid ADCS mode: {new_mode}")
                    return
                
                # Update the mode directly instead of using requested_mode
                self.mode = new_mode  # Add this line
                self.status = 1  # SLEWING
                self.pointing_start_time = None
                self.logger.info(f"Beginning slew to requested mode {new_mode}")
                
            elif command_id == 34:   # ADCS_SET_QUATERNION
                q = struct.unpack(">ffff", command_data)
                self.logger.info(f"Setting ADCS quaternion to: {q}")
                self.quaternion = list(q)
                
            else:
                self.logger.warning(f"Unknown ADCS command ID: {command_id}")
                
        except struct.error as e:
            self.logger.error(f"Error unpacking ADCS command {command_id}: {e}")

    def _update_attitude(self, orbit_state):
        """Update spacecraft attitude based on current mode"""
        try:
            self.logger.debug(f"Updating attitude - mode: {self.mode}, status: {self.status}")
            control_mode = self.mode
            q_desired = None

            if control_mode == 0:  # UNCONTROLLED / OFF
                self._uncontrolled_motion()

            elif self.status == 2 or control_mode == 1:  # POINTING ACHIEVED or LOCK mode
                self.logger.debug("POINTING ACHIEVED or LOCK mode")
                if not hasattr(self, 'lock_quaternion'):
                    self.lock_quaternion = self.quaternion.copy()
                if q_desired is None:
                    q_desired = self.quaternion
                elif control_mode == 1:
                    q_desired = self.lock_quaternion
                elif control_mode == 3:  # SUNPOINTING POINTING
                    q_desired = self._q_desired_sunpointing(orbit_state)
                elif control_mode == 3:  # NADIR POINTING
                    q_desired = self._q_desired_nadir(orbit_state)
                elif control_mode == 4:  # DOWNLOAD POINTING
                    q_desired = self._q_desired_nadir(orbit_state)

                q_current, ang_vel = self._keep_pointing(q_desired)
                self.quaternion = q_current
                self.angular_velocity = ang_vel

            elif control_mode == 2:  # SUNPOINTING (+X to Sun)
                q_desired = self._q_desired_sunpointing(orbit_state)
                q_current = self.quaternion  # Current attitude
                q_current, ang_vel, errors = self._keep_slewing(q_desired, q_current)
                self.quaternion = q_current 
                self.angular_velocity = ang_vel

                if (np.abs(errors[0]) > self.pointing_accuracy * 2.0) | (np.abs(errors[1]) > self.pointing_accuracy * 2.0) | (np.abs(errors[2]) > self.pointing_accuracy * 2.0):  # If error more than twice pointing accuracy
                    self.status = 1  # SLEWING
                else:
                    self.status = 2  # POINTING ACHIEVED
                    rand_noise = np.random.uniform(-0.001, 0.001, 3)
                    self.angular_velocity = np.array([0.0, 0.0, 0.0]) + rand_noise
                
            elif control_mode == 3:  # NADIR (-Z to Earth)
                q_desired = self._q_desired_nadir(orbit_state)
                q_current = self.quaternion  # Current attitude
                q_current, ang_vel, errors = self._keep_slewing(q_desired, q_current)
                self.quaternion = q_current 
                self.angular_velocity = ang_vel

                if (np.abs(errors[0]) > self.pointing_accuracy * 2.0) | (np.abs(errors[1]) > self.pointing_accuracy * 2.0) | (np.abs(errors[2]) > self.pointing_accuracy * 2.0):  # If error more than twice pointing accuracy
                    self.status = 1  # SLEWING
                else:
                    self.status = 2  # POINTING ACHIEVED
                    rand_noise = np.random.uniform(-0.001, 0.001, 3)
                    self.angular_velocity = np.array([0.0, 0.0, 0.0]) + rand_noise

            elif control_mode == 4:  # DOWNLOAD (+Z to Earth)
                q_desired = self._q_desired_download(orbit_state)  # Convert to quaternion
                q_current = self.quaternion  # Current attitude
                q_current, ang_vel, errors = self._keep_slewing(q_desired, q_current)
                self.quaternion = q_current 
                self.angular_velocity = ang_vel

                if (np.abs(errors[0]) > self.pointing_accuracy * 2.0) | (np.abs(errors[1]) > self.pointing_accuracy * 2.0) | (np.abs(errors[2]) > self.pointing_accuracy * 2.0):  # If error more than twice pointing accuracy
                    self.status = 1  # SLEWING
                else:
                    self.status = 2  # POINTING ACHIEVED
                    rand_noise = np.random.uniform(-0.001, 0.001, 3)
                    self.angular_velocity = np.array([0.0, 0.0, 0.0]) + rand_noise
                
        except Exception as e:
            self.logger.error(f"Error in attitude update: {str(e)}")
            self.status = 0  # ERROR

    def _keep_pointing(self, q_desired):
        q_current = self.quaternion  # Current attitude
        rpy_desired = list(self._quaternion_to_euler(q_desired))  # Current Euler angles
        rpy_current = list(self._quaternion_to_euler(q_current))  # Current Euler angles
        rand_error_x = np.random.uniform(-0.1, 0.1)
        rand_error_y = np.random.uniform(-0.1, 0.1)
        rand_error_z = np.random.uniform(-0.1, 0.1)
        rpy_current[0] = rpy_desired[0] + rand_error_x
        rpy_current[1] = rpy_desired[1] + rand_error_y
        rpy_current[2] = rpy_desired[2] + rand_error_z
        q_current = self._euler_to_quaternion(rpy_current[0], rpy_current[1], rpy_current[2])
        ang_vel = np.array([rand_error_x, rand_error_y, rand_error_z])  # deg/s
        return q_current, ang_vel
    
    def _keep_slewing(self, q_desired, q_current):
        rpy_desired = list(self._quaternion_to_euler(q_desired))  # Current Euler angles
        rpy_current = list(self._quaternion_to_euler(q_current))  # Current Euler angles
        x_error = rpy_desired[0] - rpy_current[0]  # Roll error
        y_error = rpy_desired[1] - rpy_current[1]  # Pitch error
        z_error = rpy_desired[2] - rpy_current[2]  # Yaw error  
        applied_slew_rate_x = np.random.uniform(-0.1, 0.1) + self.nominal_slew_rate  # Add some randomness to slew rate 
        applied_slew_rate_y = np.random.uniform(-0.1, 0.1) + self.nominal_slew_rate  # Add some randomness to slew rate 
        applied_slew_rate_z = np.random.uniform(-0.1, 0.1) + self.nominal_slew_rate  # Add some randomness to slew rate 
        rpy_current[0] = rpy_current[0] + (np.sign(x_error) * applied_slew_rate_x * self.time_step)
        rpy_current[1] = rpy_current[1] + (np.sign(y_error) * applied_slew_rate_y * self.time_step)
        rpy_current[2] = rpy_current[2] + (np.sign(z_error) * applied_slew_rate_z * self.time_step)
        q_current = self._euler_to_quaternion(rpy_current[0], rpy_current[1], rpy_current[2])
        ang_vel = np.array([applied_slew_rate_x, applied_slew_rate_y, applied_slew_rate_z])  # deg/s

        error_angle = self._calculate_error_angle(self.quaternion, q_desired)
        est_time_to_target = (error_angle / (np.random.uniform(0.001, 0.1) + self.nominal_slew_rate)) * 1.1  # Add 10% to account for error
        
        modes = ['OFF',"LOCK","SUNPOINTING","NADIR","DOWNLOAD"]
        self.logger.debug(f"                     Going to: {modes[self.mode]}")
        self.logger.debug(f"  Target quaternion for NADIR: {q_desired}")
        self.logger.debug(f"Target Euler angles for NADIR: {rpy_desired} deg")
        self.logger.debug(f"           Current quaternion: {q_current}")
        self.logger.debug(f"         Current Euler angles: {rpy_current} deg")
        self.logger.debug(f"           Applied slew rates: {applied_slew_rate_x:.2f} deg/s, {applied_slew_rate_y:.2f} deg/s, {applied_slew_rate_z:.2f} deg/s")
        self.logger.debug(f"                  Euler error: {x_error:.2f} deg, {y_error:.2f} deg, {z_error:.2f} deg")
        self.logger.debug(f"     Estimated time to target: {est_time_to_target:.2f} seconds")    
        self.logger.debug(f"            Pointing accuracy: {self.pointing_accuracy:.2f} deg")

        return q_current, ang_vel, [x_error,y_error,z_error]

    def _q_desired_sunpointing(self, orbit_state):
        sun_pos = self.orbit_propagator.sun.get_position_at_time(orbit_state['time'])  # Get Sun position 
        sun_vec = sun_pos / np.linalg.norm(sun_pos)  # Normalize
        z_body = np.array([0, 0, 1])  # +Z-axis points to Earth 
        x_body = sun_vec  # +X-axis points to Sun
        y_body = np.cross(z_body, x_body)  # +Y-axis completes right-handed system
        y_body = y_body / np.linalg.norm(y_body)  # Normalize
        z_body = np.cross(x_body, y_body)  # +Z-axis completes right-handed system
        R = np.column_stack((x_body, y_body, z_body))  # Form rotation matrix
        q_desired = self._rotation_matrix_to_quaternion(R)  # Convert to quaternion
        return q_desired

    def _q_desired_nadir(self, orbit_state):
        earth_pos = -np.array(orbit_state['position'])  # Get vector pointing to Earth center
        earth_vec = earth_pos / np.linalg.norm(earth_pos)  # Normalize
        z_body = -earth_vec  # -Z-axis points to Earth
        temp_vec = np.array([0, 0, 1])  # Try using Z-axis first
        x_body = np.cross(z_body, temp_vec)
        if np.linalg.norm(x_body) < 1e-10:  # If vectors were parallel
            temp_vec = np.array([0, 1, 0])  # Try Y-axis instead
            x_body = np.cross(z_body, temp_vec)
        x_body = x_body / np.linalg.norm(x_body)  # Normalize   
        y_body = np.cross(z_body, x_body)  # Y-axis completes right-handed system
        y_body = y_body / np.linalg.norm(y_body)  # Normalize
        R = np.column_stack((x_body, y_body, z_body))  # Form rotation matrix
        q_desired = self._rotation_matrix_to_quaternion(R)  # Convert to quaternion
        return q_desired
    
    def _q_desired_download(self, orbit_state):
        earth_pos = -np.array(orbit_state['position'])  # Get vector pointing to Earth center
        earth_vec = earth_pos / np.linalg.norm(earth_pos)  # Normalize
        z_body = earth_vec  # -Z-axis points to Earth
        temp_vec = np.array([0, 0, 1])  # Try using Z-axis first
        x_body = np.cross(z_body, temp_vec)
        if np.linalg.norm(x_body) < 1e-10:  # If vectors were parallel
            temp_vec = np.array([0, 1, 0])  # Try Y-axis instead
            x_body = np.cross(z_body, temp_vec)
        x_body = x_body / np.linalg.norm(x_body)  # Normalize   
        y_body = np.cross(z_body, x_body)  # Y-axis completes right-handed system
        y_body = y_body / np.linalg.norm(y_body)  # Normalize
        R = np.column_stack((x_body, y_body, z_body))  # Form rotation matrix
        q_desired = self._rotation_matrix_to_quaternion(R)  # Convert to quaternion
        return q_desired

    def _uncontrolled_motion(self):
        """Update attitude for uncontrolled spacecraft (OFF mode or UNCONTROLLED status)"""
        # Natural dynamics only - small random disturbances
        q_current = self.quaternion  # Current attitude
        rpy_current = list(self._quaternion_to_euler(q_current))  # Current Euler angles
        applied_random_rate_x = np.random.uniform(0.001, 0.1)  # Add some randomness 
        applied_random_rate_y = np.random.uniform(0.001, 0.1)  # Add some randomness 
        applied_random_rate_z = np.random.uniform(0.001, 0.1)  # Add some randomness 
        rpy_current[0] = rpy_current[0] + (applied_random_rate_x * self.time_step)
        rpy_current[1] = rpy_current[1] + (applied_random_rate_y * self.time_step)
        rpy_current[2] = rpy_current[2] + (applied_random_rate_z * self.time_step)
        q_current = self._euler_to_quaternion(rpy_current[0], rpy_current[1], rpy_current[2])
        self.angular_velocity = np.array([applied_random_rate_x, applied_random_rate_y, applied_random_rate_z])  # deg/s
        self.quaternion = q_current

    def _euler_to_quaternion(self, roll_deg, pitch_deg, yaw_deg):
        """
        Convert Euler angles to quaternion.
        Input angles in degrees in ZYX (yaw, pitch, roll) rotation sequence.
        Returns quaternion in [x,y,z,w] format.
        
        Args:
            roll_deg (float): Rotation around X axis in degrees
            pitch_deg (float): Rotation around Y axis in degrees
            yaw_deg (float): Rotation around Z axis in degrees
        
        Returns:
            np.array: Quaternion in [x,y,z,w] format
        """
        # Convert to radians for numpy trig functions
        roll = np.radians(roll_deg)
        pitch = np.radians(pitch_deg)
        yaw = np.radians(yaw_deg)
        
        # Calculate trig functions once
        cy = np.cos(yaw * 0.5)
        sy = np.sin(yaw * 0.5)
        cp = np.cos(pitch * 0.5)
        sp = np.sin(pitch * 0.5)
        cr = np.cos(roll * 0.5)
        sr = np.sin(roll * 0.5)

        # Quaternion components
        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        # Return in [x,y,z,w] format
        q = np.array([x, y, z, w])
        return q / np.linalg.norm(q)  # Ensure normalized

    def _quaternion_to_euler(self, q):
        """
        Convert quaternion to Euler angles.
        Input quaternion in [x,y,z,w] format.
        Returns Euler angles in degrees in ZYX (yaw, pitch, roll) rotation sequence.
        
        Args:
            q (np.array): Quaternion in [x,y,z,w] format
        
        Returns:
            tuple: (roll, pitch, yaw) in degrees
        """
        # Normalize quaternion
        q = q / np.linalg.norm(q)
        
        # Extract quaternion components
        x, y, z, w = q
        
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            # Use 90 degrees if out of range
            pitch = np.copysign(np.pi / 2, sinp)
        else:
            pitch = np.arcsin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)

        # Convert to degrees
        return np.degrees(roll), np.degrees(pitch), np.degrees(yaw)

    def _rotation_matrix_to_quaternion(self, R):
        """Convert 3x3 rotation matrix to quaternion [x,y,z,w]"""
        try:
            trace = np.trace(R)
            
            if trace > 0:
                S = np.sqrt(trace + 1.0) * 2
                w = 0.25 * S
                x = (R[2,1] - R[1,2]) / S
                y = (R[0,2] - R[2,0]) / S
                z = (R[1,0] - R[0,1]) / S
            elif R[0,0] > R[1,1] and R[0,0] > R[2,2]:
                S = np.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2]) * 2
                w = (R[2,1] - R[1,2]) / S
                x = 0.25 * S
                y = (R[0,1] + R[1,0]) / S
                z = (R[0,2] + R[2,0]) / S
            elif R[1,1] > R[2,2]:
                S = np.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2]) * 2
                w = (R[0,2] - R[2,0]) / S
                x = (R[0,1] + R[1,0]) / S
                y = 0.25 * S
                z = (R[1,2] + R[2,1]) / S
            else:
                S = np.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1]) * 2
                w = (R[1,0] - R[0,1]) / S
                x = (R[0,2] + R[2,0]) / S
                y = (R[1,2] + R[2,1]) / S
                z = 0.25 * S
                
            q = np.array([x, y, z, w])
            return q / np.linalg.norm(q)  # Ensure normalized
            
        except Exception as e:
            self.logger.error(f"Error in rotation matrix to quaternion conversion: {str(e)}")
            return np.array([0, 0, 0, 1])  # Return identity quaternion on error

    def _calculate_error_angle(self, q_current, q_desired):
        """Calculate the angular error between current and desired quaternions"""
        try:
            # Ensure quaternions are normalized
            q_current = q_current / np.linalg.norm(q_current)
            q_desired = q_desired / np.linalg.norm(q_desired)
            
            # Calculate the error quaternion
            q_error = self._quaternion_multiply(self._quaternion_conjugate(q_current), q_desired)
            
            # Convert to angle in degrees
            angle = 2 * np.arccos(np.clip(abs(q_error[3]), -1.0, 1.0))
            return np.degrees(angle)
            
        except Exception as e:
            self.logger.error(f"Error calculating error angle: {str(e)}")
            return float('inf')  # Return large error on failure

    def _quaternion_multiply(self, q1, q2):
        """Multiply two quaternions"""
        w1, x1, y1, z1 = q1[3], q1[0], q1[1], q1[2]
        w2, x2, y2, z2 = q2[3], q2[0], q2[1], q2[2]
        
        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
        z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
        
        return np.array([x, y, z, w])

    def _quaternion_conjugate(self, q):
        """Return the conjugate of a quaternion"""
        return np.array([-q[0], -q[1], -q[2], q[3]])