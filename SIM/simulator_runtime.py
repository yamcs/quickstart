"""
BOSSY Spacecraft Simulator
Real-time simulator for a 3U CubeSat with basic subsystems
"""

import logging
import numpy as np
import socket
import threading
import queue
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import json
import time
from enum import Enum, auto

from spacecraft_config import (
    SpacecraftConfig, 
    SubsystemState,
    ADCSMode,
    ADCSStatus,
    CommsMode,
    OBCMode,
    TelemetryMode
)
from simulator_config import SimulatorConfig

# Set up logging
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )
# logger = logging.getLogger(__name__)

class SubsystemBase:
    """Base class for all subsystems"""
    def __init__(self, name: str, spacecraft_config: SpacecraftConfig, simulator_config: SimulatorConfig):
        self.name = name
        self.config = spacecraft_config
        self.simulator_config = simulator_config
        self.state = SubsystemState.OFF
        self.temperature = 20.0  # Initial temperature in degC
        self.heater_enabled = False
        self.heater_setpoint = self.config.thermal['subsystems'][name.lower()]['initial_temperature']
        self.power_draw = 0.0
        self.logger = logging.getLogger(f"Subsystem.{name}")

    def get_telemetry(self, telemetry_type: TelemetryMode = TelemetryMode.MINIMAL) -> dict:
        """Get base telemetry for all subsystems"""
        telemetry = {
            'state': self.state.value,
            'temperature': self.temperature,
            'power_draw': self.power_draw
        }
        return telemetry

    def process_common_command(self, command: str, parameters: dict) -> bool:
        """Process common telecommands"""
        if command == 'SET_STATE':
            try:
                new_state = SubsystemState(parameters['state'])
                self.state = new_state
                self.logger.info(f"State changed to {new_state.value}")
                return True
            except ValueError:
                self.logger.error(f"Invalid state: {parameters['state']}")
                return False
                
        elif command == 'SET_HEATER':
            self.heater_enabled = parameters['enabled']
            self.logger.info(f"Heater {'enabled' if self.heater_enabled else 'disabled'}")
            return True
            
        elif command == 'SET_HEATER_SETPOINT':
            self.heater_setpoint = float(parameters['temperature'])
            self.logger.info(f"Heater setpoint set to {self.heater_setpoint}°C")
            return True
            
        return False

    def update(self, dt: float, eclipse_state: str = 'NONE') -> None:
        """Update subsystem state"""
        if self.state == SubsystemState.OFF:
            return
            
        self.update_thermal(dt, eclipse_state)
        self._calculate_power_draw()

    def update_thermal(self, dt: float, eclipse_state: str) -> None:
        """Update thermal state using thermal config and eclipse state"""
        thermal_config = self.config.thermal['subsystems'].get(self.name.lower())
        if not thermal_config:
            self.logger.warning(f"No thermal config found for {self.name}")
            return

        thermal_props = self.config.thermal['properties']

        # Adjust heat loss/gain based on eclipse
        if eclipse_state == 'TOTAL':
            environment_heat_rate = -thermal_props['heat_loss_rate']
        elif eclipse_state == 'PARTIAL':
            environment_heat_rate = (thermal_props['heat_gain_rate'] - 
                                   thermal_props['heat_loss_rate']) * 0.5
        else:
            environment_heat_rate = thermal_props['heat_gain_rate']

        # Calculate temperature change
        if self.heater_enabled and self.temperature < self.heater_setpoint:
            heat_rate = (thermal_config['heater_power'] + environment_heat_rate) / thermal_props['thermal_mass']
            self.temperature += heat_rate * dt
            self.power_draw = thermal_config['power_draw'] + thermal_config['heater_power']
        else:
            heat_rate = environment_heat_rate / thermal_props['thermal_mass']
            self.temperature += heat_rate * dt
            self.power_draw = thermal_config['power_draw']

    def _calculate_power_draw(self) -> None:
        """Calculate power draw based on current state"""
        if self.state == SubsystemState.OFF:
            self.power_draw = 0.0
            return
        
        # Use thermal config
        thermal_config = self.config.thermal['subsystems'][self.name.lower()]
        self.power_draw = thermal_config['power_draw']

class PowerSubsystem(SubsystemBase):
    def __init__(self, spacecraft_config: SpacecraftConfig, simulator_config: SimulatorConfig):
        super().__init__("POWER", spacecraft_config, simulator_config)
        self.battery_voltage = self.config.power['battery']['nominal_voltage']
        self.battery_current = 0.0
        self.battery_charge = self.config.power['battery']['initial_charge']
        self.solar_power = 0.0
        self.subsystem_power_draws = {}
        self.simulator_config = simulator_config

    def get_telemetry(self) -> dict:
        """Return power telemetry"""
        common_tm = super().get_telemetry()
        power_tm = {
            'battery_voltage': self.battery_voltage,
            'battery_current': self.battery_current,
            'battery_charge': self.battery_charge,
            'solar_power': self.solar_power
        }
        return {**common_tm, **power_tm}

    def register_subsystem_power(self, subsystem_name: str, power_draw: float) -> None:
        """Register power draw from a subsystem"""
        self.subsystem_power_draws[subsystem_name] = power_draw

    def update(self, dt: float, sun_vector: np.ndarray, spacecraft_orientation: np.ndarray, eclipse_state: str) -> None:
        """Update power subsystem state"""
        super().update(dt, eclipse_state)
        
        if self.state == SubsystemState.OFF:
            return
            
        # Calculate solar power (considering eclipse)
        if eclipse_state == 'TOTAL':
            self.solar_power = 0.0
        elif eclipse_state == 'PARTIAL':
            self.solar_power = self._calculate_solar_power(sun_vector, spacecraft_orientation) * 0.5
        else:
            self.solar_power = self._calculate_solar_power(sun_vector, spacecraft_orientation)
        
        # Update battery state - pass eclipse_state
        self._update_battery(dt, eclipse_state)

    def _update_battery(self, dt: float, eclipse_state: str) -> None:
        """Update battery state considering eclipse"""
        # Calculate total power draw from all subsystems
        total_power_draw = sum(self.subsystem_power_draws.values())
        
        # Adjust charging efficiency based on eclipse
        if eclipse_state == 'TOTAL':
            charging_efficiency = 0.0  # No charging in eclipse
        elif eclipse_state == 'PARTIAL':
            charging_efficiency = self.config.power['battery']['charge_efficiency'] * 0.5
        else:
            charging_efficiency = self.config.power['battery']['charge_efficiency']
        
        # Calculate net power
        net_power = (self.solar_power * charging_efficiency) - total_power_draw
        
        # Update battery charge
        battery_capacity = self.config.power['battery']['capacity']
        self.battery_charge = max(0.0, min(100.0, 
            self.battery_charge + (net_power * dt * 100.0 / battery_capacity)))

    def _calculate_solar_power(self, sun_vector: np.ndarray, spacecraft_orientation: np.ndarray) -> float:
        """Calculate solar power generation based on orientation and panel config"""
        total_power = 0.0
        solar_constant = self.simulator_config.environment['sun']['solar_constant']
        
        # Calculate power for each solar panel
        for panel in self.config.power['solar_panels']['faces']:
            # Transform panel normal vector using spacecraft orientation
            panel_normal = np.array(panel['normal'])
            if spacecraft_orientation is not None:
                rotation_matrix = self._quaternion_to_matrix(spacecraft_orientation)
                panel_normal = rotation_matrix @ panel_normal
            
            # Calculate cosine of angle between sun vector and panel normal
            cos_angle = np.dot(sun_vector, panel_normal)
            
            # Only generate power if sun is hitting front of panel
            if cos_angle > 0:
                panel_power = (
                    solar_constant * 
                    panel['area'] * 
                    panel['efficiency'] * 
                    cos_angle * 
                    self.simulator_config.environment['sun']['intensity_factor']
                )
                total_power += panel_power
        
        return total_power

    def is_power_available(self) -> bool:
        """Check if power system can support spacecraft operations"""
        return (self.state != SubsystemState.OFF and 
                self.battery_charge > self.config.power['battery']['minimum_charge'])

    def process_command(self, command: str, parameters: dict) -> bool:
        """Process power subsystem commands"""
        # Only common commands (SET_STATE, SET_HEATER, SET_HEATER_SETPOINT)
        return super().process_common_command(command, parameters)

    @staticmethod
    def _quaternion_to_matrix(q: np.ndarray) -> np.ndarray:
        """Convert quaternion to rotation matrix
        
        Args:
            q (np.ndarray): Quaternion [w, x, y, z]
        
        Returns:
            np.ndarray: 3x3 rotation matrix
        """
        # Normalize quaternion
        q = q / np.linalg.norm(q)
        
        # Extract quaternion components
        w, x, y, z = q
        
        # Calculate rotation matrix elements
        return np.array([
            [1 - 2*y*y - 2*z*z,     2*x*y - 2*w*z,     2*x*z + 2*w*y],
            [    2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z,     2*y*z - 2*w*x],
            [    2*x*z - 2*w*y,     2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y]
        ])

class ADCSSubsystem(SubsystemBase):
    def __init__(self, spacecraft_config: SpacecraftConfig, simulator_config: SimulatorConfig):
        super().__init__("ADCS", spacecraft_config, simulator_config)
        self.mode = ADCSMode.OFF
        self.status = ADCSStatus.UNDEFINED
        self.target_quaternion = np.array([1., 0., 0., 0.])
        self.current_quaternion = np.array([1., 0., 0., 0.])
        self.angular_rates = np.zeros(3)
        self.control_torques = np.zeros(3)
        self.sun_sensor_reading = None
        self.nadir_sensor_reading = None

    @staticmethod
    def _quaternion_to_matrix(q: np.ndarray) -> np.ndarray:
        """Convert quaternion to rotation matrix
        
        Args:
            q (np.ndarray): Quaternion [w, x, y, z]
        
        Returns:
            np.ndarray: 3x3 rotation matrix
        """
        # Normalize quaternion
        q = q / np.linalg.norm(q)
        
        # Extract quaternion components
        w, x, y, z = q
        
        # Calculate rotation matrix elements
        return np.array([
            [1 - 2*y*y - 2*z*z,     2*x*y - 2*w*z,     2*x*z + 2*w*y],
            [    2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z,     2*y*z - 2*w*x],
            [    2*x*z - 2*w*y,     2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y]
        ])

    @staticmethod
    def _vector_to_quaternion(v: np.ndarray) -> np.ndarray:
        """Convert a vector to a quaternion that rotates the z-axis to that vector
        
        Args:
            v (np.ndarray): Target vector (3D)
        
        Returns:
            np.ndarray: Quaternion [w, x, y, z]
        """
        # Normalize vector
        v = v / np.linalg.norm(v)
        
        # Get rotation axis (cross product with z-axis)
        z_axis = np.array([0, 0, 1])
        axis = np.cross(z_axis, v)
        
        # If vectors are parallel, return identity quaternion
        if np.allclose(axis, 0):
            if v[2] >= 0:
                return np.array([1., 0., 0., 0.])
            else:
                return np.array([0., 1., 0., 0.])
        
        # Calculate rotation angle
        angle = np.arccos(np.dot(z_axis, v))
        
        # Normalize rotation axis
        axis = axis / np.linalg.norm(axis)
        
        # Create quaternion [w, x, y, z]
        return np.array([
            np.cos(angle/2),
            axis[0] * np.sin(angle/2),
            axis[1] * np.sin(angle/2),
            axis[2] * np.sin(angle/2)
        ])

    def _propagate_attitude(self, dt: float) -> None:
        """Propagate attitude quaternion using current angular rates"""
        # Quaternion derivative
        w = self.angular_rates
        q = self.current_quaternion
        
        qdot = 0.5 * np.array([
            [-q[1], -q[2], -q[3]],
            [ q[0], -q[3],  q[2]],
            [ q[3],  q[0], -q[1]],
            [-q[2],  q[1],  q[0]]
        ]) @ w
        
        # Integrate quaternion
        self.current_quaternion += qdot * dt
        
        # Normalize quaternion
        self.current_quaternion = self.current_quaternion / np.linalg.norm(self.current_quaternion)

    def get_telemetry(self, telemetry_type: TelemetryMode = TelemetryMode.MINIMAL) -> dict:
        """Get ADCS telemetry"""
        telemetry = super().get_telemetry(telemetry_type)
        
        if telemetry_type == TelemetryMode.FULL:
            telemetry.update({
                'mode': self.mode.value,
                'status': self.status.value,
                'quaternion': self.current_quaternion.tolist(),
                'angular_rates': self.angular_rates.tolist(),
                'control_torques': self.control_torques.tolist(),
                'sun_sensor': self.sun_sensor_reading.tolist() if self.sun_sensor_reading is not None else None,
                'nadir_sensor': self.nadir_sensor_reading.tolist() if self.nadir_sensor_reading is not None else None
            })
        elif telemetry_type == TelemetryMode.NORMAL:
            telemetry.update({
                'mode': self.mode.value,
                'status': self.status.value,
                'quaternion': self.current_quaternion.tolist(),
                'angular_rates': self.angular_rates.tolist()
            })
        else:  # MINIMAL
            telemetry.update({
                'mode': self.mode.value,
                'status': self.status.value
            })
        
        return telemetry

    def process_command(self, command: str, parameters: dict) -> bool:
        """Process ADCS commands"""
        # Try common commands first
        if super().process_common_command(command, parameters):
            return True

        if command == 'SET_MODE':
            try:
                new_mode = ADCSMode(parameters['mode'])
                if new_mode != self.mode:
                    self.mode = new_mode
                    self.status = ADCSStatus.SLEWING
                    self.logger.info(f"ADCS mode changed to {new_mode.value}")
                return True
            except ValueError:
                self.logger.error(f"Invalid ADCS mode: {parameters['mode']}")
                return False

        elif command == 'SET_QUATERNION':
            if self.state == SubsystemState.OFF:
                self.logger.warning("Cannot set quaternion while ADCS is OFF")
                return False
            
            new_quaternion = np.array(parameters['quaternion'])
            if np.allclose(np.linalg.norm(new_quaternion), 1.0):
                self.target_quaternion = new_quaternion
                self.mode = ADCSMode.LOCK
                self.status = ADCSStatus.SLEWING
                self.logger.info("New target quaternion set")
                return True
            else:
                self.logger.error("Invalid quaternion (not normalized)")
                return False

        return False

    def update(self, dt: float, sun_vector: np.ndarray, nadir_vector: np.ndarray, eclipse_state: str = 'NONE') -> None:
        """Update ADCS state"""
        super().update(dt, eclipse_state)
        
        if self.state == SubsystemState.OFF:
            return

        # Add sensor noise
        noise_amplitude = self.simulator_config.environment['magnetic_field']['strength'] * 0.001
        
        # Update sensor readings with noise
        self.sun_sensor_reading = sun_vector + np.random.normal(0, noise_amplitude, 3)
        self.sun_sensor_reading = self.sun_sensor_reading / np.linalg.norm(self.sun_sensor_reading)
        
        self.nadir_sensor_reading = nadir_vector + np.random.normal(0, noise_amplitude, 3)
        self.nadir_sensor_reading = self.nadir_sensor_reading / np.linalg.norm(self.nadir_sensor_reading)
        
        # Update attitude determination and control based on mode
        if self.mode == ADCSMode.SUNPOINTING:
            self._sunpointing_control(dt)
        elif self.mode == ADCSMode.NADIR:
            self._nadirpointing_control(dt)
        elif self.mode == ADCSMode.SLEW:
            self._slew_to_target(dt)
        
        # Update quaternion based on angular rates
        self._propagate_attitude(dt)

    def _sunpointing_control(self, dt: float) -> None:
        """Control law for sun pointing mode"""
        if self.sun_sensor_reading is None:
            self.logger.warning("No sun sensor reading available")
            return
            
        # Calculate error quaternion
        target_vector = self.sun_sensor_reading
        current_vector = self._get_body_sun_vector()
        
        # Update control torques
        self._calculate_control_torques(current_vector, target_vector, dt)

    def _nadirpointing_control(self, dt: float) -> None:
        """Control law for nadir pointing mode"""
        if self.nadir_sensor_reading is None:
            self.logger.warning("No nadir sensor reading available")
            return
            
        # Calculate error quaternion
        target_vector = self.nadir_sensor_reading
        current_vector = self._get_body_nadir_vector()
        
        # Update control torques
        self._calculate_control_torques(current_vector, target_vector, dt)

    def _get_body_sun_vector(self) -> np.ndarray:
        """Get sun vector in body frame"""
        # Transform sun vector from ECI to body frame using current attitude
        rotation_matrix = self._quaternion_to_matrix(self.current_quaternion)
        return rotation_matrix.T @ self.sun_sensor_reading

    def _get_body_nadir_vector(self) -> np.ndarray:
        """Get nadir vector in body frame"""
        # Transform nadir vector from ECI to body frame using current attitude
        rotation_matrix = self._quaternion_to_matrix(self.current_quaternion)
        return rotation_matrix.T @ self.nadir_sensor_reading

    def _calculate_control_torques(self, current_vector: np.ndarray, target_vector: np.ndarray, dt: float) -> None:
        """Calculate control torques based on current and target vectors"""
        # Cross product control law
        error = np.cross(current_vector, target_vector)
        
        # PD control
        Kp = 0.01  # Proportional gain
        Kd = 0.1   # Derivative gain
        
        self.control_torques = -Kp * error - Kd * self.angular_rates

    def _calculate_target_quaternion(self, sun_vector: np.ndarray, nadir_vector: np.ndarray) -> Optional[np.ndarray]:
        if self.mode == ADCSMode.LOCK:
            return self.target_quaternion
        elif self.mode == ADCSMode.SUNPOINTING:
            return self._quaternion_to_align_vector(np.array([1, 0, 0]), sun_vector)
        elif self.mode == ADCSMode.NADIR:
            return self._quaternion_to_align_vector(np.array([0, 0, -1]), nadir_vector)
        return None

    def _quaternion_to_align_vector(self, body_vector: np.ndarray, target_vector: np.ndarray) -> np.ndarray:
        # Simplified quaternion calculation to align vectors
        cross_product = np.cross(body_vector, target_vector)
        dot_product = np.dot(body_vector, target_vector)
        q = np.zeros(4)
        q[0:3] = cross_product
        q[3] = 1 + dot_product
        return q / np.linalg.norm(q)

    def _interpolate_quaternion(self, q1: np.ndarray, q2: np.ndarray, t: float) -> np.ndarray:
        # Simple spherical linear interpolation
        dot_product = np.dot(q1, q2)
        if dot_product < 0:
            q2 = -q2
            dot_product = -dot_product
        
        theta = np.arccos(dot_product)
        if theta == 0:
            return q1
        
        sin_theta = np.sin(theta)
        return (np.sin((1-t)*theta) * q1 + np.sin(t*theta) * q2) / sin_theta

    def _quaternion_angle_diff(self, q1: np.ndarray, q2: np.ndarray) -> float:
        # Calculate angle difference between two quaternions
        dot_product = np.dot(q1, q2)
        if dot_product < 0:
            q2 = -q2
            dot_product = -dot_product
        
        theta = np.arccos(dot_product)
        return theta

    def _calculate_power_draw(self) -> float:
        """Calculate power draw based on current mode"""
        if self.state == SubsystemState.OFF:
            return 0.0
            
        # Use ADCS power config
        base_power = self.config.adcs['power']['idle']
        if self.status == ADCSStatus.SLEWING:
            # Add power for active reaction wheels
            base_power += (self.config.adcs['reaction_wheels']['power']['active'] * 
                         self.config.adcs['reaction_wheels']['count'])
        elif self.status == ADCSStatus.POINTING:
            # Add power for maintaining pointing
            base_power += (self.config.adcs['reaction_wheels']['power']['idle'] * 
                         self.config.adcs['reaction_wheels']['count'])
            
        return base_power

class CommunicationsSubsystem(SubsystemBase):
    def __init__(self, spacecraft_config: SpacecraftConfig, simulator_config: SimulatorConfig):
        super().__init__("COMMS", spacecraft_config, simulator_config)
        self.mode = CommsMode.OFF
        self.tm_bitrate = self.config.comms['downlink_rate']
        self.tc_bitrate = self.config.comms['uplink_rate']
        self.tm_queue = queue.Queue()
        self.tc_queue = queue.Queue()

        # Setup UDP sockets
        self.tm_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tc_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Get network config from spacecraft config
        self.tm_address = (
            self.config.comms['network']['tm_host'],
            self.config.comms['network']['tm_port']
        )
        
        # Bind TC socket
        try:
            self.tc_socket.bind((
                self.config.comms['network']['tc_host'],
                self.config.comms['network']['tc_port']
            ))
            self.tc_socket.setblocking(False)
            self.logger.info(f"TC socket bound to port {self.config.comms['network']['tc_port']}")
        except socket.error as e:
            self.logger.error(f"Failed to bind TC socket: {e}")
            self.status = SubsystemState.ERROR
            raise

        # Start TC listener thread
        self.tc_thread = threading.Thread(target=self._tc_listener, daemon=True)
        self.tc_thread.start()

    def _tc_listener(self):
        """Listen for telecommands"""
        while True:
            try:
                if self.state == SubsystemState.OFF or self.mode not in [CommsMode.RX, CommsMode.TXRX]:
                    time.sleep(0.1)
                    continue
                    
                # Try to receive data (non-blocking)
                data, addr = self.tc_socket.recvfrom(1024)
                self.logger.debug(f"Received TC from {addr}: {data}")
                
                try:
                    command = json.loads(data.decode())
                    self.command_queue.put(command)  # Use existing command queue
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse TC: {e}")
                    
            except BlockingIOError:
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"TC listener error: {e}")
                time.sleep(1)

    def send_telemetry(self, telemetry: dict) -> None:
        """Send telemetry packet"""
        if self.state == SubsystemState.OFF or self.mode not in [CommsMode.TX, CommsMode.TXRX]:
            return
            
        try:
            data = json.dumps(telemetry).encode()
            self.tm_socket.sendto(data, self.tm_address)
            self.logger.debug(f"Sent TM packet: {telemetry}")
        except Exception as e:
            self.logger.error(f"Failed to send TM: {e}")

    def get_telemetry(self, telemetry_mode: TelemetryMode = TelemetryMode.MINIMAL) -> dict:
        """Return communications telemetry"""
        common_tm = super().get_telemetry()
        comms_tm = {
            'mode': self.mode.value,
            'tm_queue_size': self._get_queue_size_bits(self.tm_queue),
            'tc_queue_size': self._get_queue_size_bits(self.tc_queue),
            'tm_bitrate': self.tm_bitrate,
            'tc_bitrate': self.tc_bitrate
        }
        return {**common_tm, **comms_tm}

    def _get_queue_size_bits(self, q: queue.Queue) -> int:
        """Calculate queue size in bits"""
        total_bits = 0
        for packet in list(q.queue):
            total_bits += len(packet) * 8
        return total_bits

    def process_command(self, command: str, parameters: dict) -> bool:
        """Process communications commands"""
        if super().process_common_command(command, parameters):
            return True

        if command == 'SET_MODE':
            try:
                new_mode = CommsMode(parameters['mode'])
                self.mode = new_mode
                self.logger.info(f"Communications mode changed to {new_mode.value}")
                return True
            except ValueError:
                self.logger.error(f"Invalid communications mode: {parameters['mode']}")
                return False

        elif command == 'CLEAR_TM_QUEUE':
            with self.tm_queue.mutex:
                self.tm_queue.queue.clear()
            self.logger.info("Telemetry queue cleared")
            return True

        elif command == 'CLEAR_TC_QUEUE':
            with self.tc_queue.mutex:
                self.tc_queue.queue.clear()
            self.logger.info("Telecommand queue cleared")
            return True

        elif command == 'SET_TM_BITRATE':
            new_bitrate = int(parameters['bitrate'])
            if new_bitrate > 0:
                self.tm_bitrate = new_bitrate
                self.logger.info(f"Telemetry bitrate set to {new_bitrate} bps")
                return True
            return False

        elif command == 'SET_TC_BITRATE':
            new_bitrate = int(parameters['bitrate'])
            if new_bitrate > 0:
                self.tc_bitrate = new_bitrate
                self.logger.info(f"Telecommand bitrate set to {new_bitrate} bps")
                return True
            return False

        return False

    def update(self, dt: float, eclipse_state: str = 'NONE') -> None:
        """Update communications subsystem state"""
        super().update(dt, eclipse_state)

        if self.state == SubsystemState.OFF or self.mode == CommsMode.OFF:
            return

        # Process downlink queue if in TX or TXRX mode
        if self.mode in [CommsMode.TX, CommsMode.TXRX]:
            bytes_per_update = int(self.tm_bitrate * dt / 8)  # Convert bits to bytes
            self._process_tm_queue(bytes_per_update)

        # Process uplink queue if in RX or TXRX mode
        if self.mode in [CommsMode.RX, CommsMode.TXRX]:
            self._check_incoming_tc()

        # Update power draw based on mode
        self.power_draw = self._calculate_power_draw()

    def _process_tm_queue(self, bytes_per_update: int) -> None:
        """Process telemetry queue based on current bitrate"""
        while bytes_per_update > 0 and not self.tm_queue.empty():
            packet = self.tm_queue.queue[0]  # Peek at next packet
            if len(packet) <= bytes_per_update:
                self.tm_queue.get()  # Remove packet from queue
                try:
                    self.tm_socket.sendto(packet, ('localhost', self.config.comms['ground_station_port']))
                except socket.error as e:
                    self.logger.error(f"Failed to send telemetry: {e}")
                bytes_per_update -= len(packet)
            else:
                break

    def _check_incoming_tc(self) -> None:
        """Check for incoming telecommands"""
        try:
            while True:
                data, addr = self.tc_socket.recvfrom(1024)
                self.tc_queue.put(data)
        except BlockingIOError:
            pass  # No more data to read

    def _calculate_power_draw(self) -> float:
        """Calculate power draw based on current mode"""
        if self.state == SubsystemState.OFF or self.mode == CommsMode.OFF:
            return 0.0
        
        base_power = self.config.comms['power']['idle']
        if self.mode == CommsMode.TX:
            base_power += self.config.comms['power']['tx']
        elif self.mode == CommsMode.RX:
            base_power += self.config.comms['power']['rx']
        elif self.mode == CommsMode.TXRX:
            base_power += self.config.comms['power']['tx'] + self.config.comms['power']['rx']
        
        return base_power

class OBCSubsystem(SubsystemBase):
    def __init__(self, spacecraft_config: SpacecraftConfig, simulator_config: SimulatorConfig):
        super().__init__("OBC", spacecraft_config, simulator_config)
        self.mode = OBCMode.SAFE
        self.subsystems = {}
        self.telemetry_timer = 0.0
        self.last_telemetry_time = datetime.now(timezone.utc)
        self.tm_sequence_count = 0

    def get_telemetry(self) -> dict:
        """Return OBC telemetry"""
        common_tm = super().get_telemetry()
        obc_tm = {
            'mode': self.mode.value
        }
        return {**common_tm, **obc_tm}

    def register_subsystem(self, subsystem: SubsystemBase) -> None:
        """Register a subsystem with the OBC"""
        self.subsystems[subsystem.name] = subsystem
        self.logger.info(f"Registered subsystem: {subsystem.name}")

    def process_command(self, command: str, parameters: dict) -> bool:
        """Process OBC commands"""
        if super().process_common_command(command, parameters):
            return True

        if command == 'SET_MODE':
            try:
                new_mode = OBCMode(parameters['mode'])
                if self._can_change_mode(new_mode):
                    self._change_mode(new_mode)
                    return True
                return False
            except ValueError:
                self.logger.error(f"Invalid OBC mode: {parameters['mode']}")
                return False

        elif command == 'RESET':
            self.logger.info("Initiating spacecraft reset")
            self._reset_spacecraft()
            return True

        return False

    def update(self, dt: float, eclipse_state: str = 'NONE') -> None:
        """Update OBC state"""
        super().update(dt, eclipse_state)

        if self.state == SubsystemState.OFF:
            return

        # Update telemetry collection timer
        self.telemetry_timer += dt
        if self.telemetry_timer >= 1.0 / self.config.obc['telemetry_rate']:
            self.collect_telemetry()
            self.telemetry_timer = 0.0

        # Process any pending commands from comms
        if 'COMMS' in self.subsystems:
            self._process_telecommands()

        # Mode-specific updates
        self._update_mode_requirements()

        # Update power draw
        self.power_draw = self._calculate_power_draw()

    def collect_telemetry(self) -> None:
        """Collect telemetry from all subsystems"""
        if self.state == SubsystemState.OFF or 'COMMS' not in self.subsystems:
            return

        telemetry_packet = {
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'mission_time': self.simulation_time,
            'obc_mode': self.mode.value,
            'subsystems': {}
        }

        # Collect telemetry from each subsystem
        for name, subsystem in self.subsystems.items():
            telemetry_packet['subsystems'][name] = subsystem.get_telemetry()

        # Create CCSDS packet
        packet = CCSDSPacket()
        packet.packet_type = 0  # TM
        packet.apid = self.config.telemetry['OBC']['apid']
        packet.sequence_count = self.tm_sequence_count
        self.tm_sequence_count = (self.tm_sequence_count + 1) & 0x3FFF
        
        # Add payload
        packet.payload = json.dumps(telemetry_packet).encode()

        # Send to communications subsystem
        comms = self.subsystems['COMMS']
        if comms.state != SubsystemState.OFF:
            comms.tm_queue.put(packet.to_bytes())

    def _process_telecommands(self) -> None:
        """Process commands from the communications subsystem"""
        comms = self.subsystems['COMMS']
        while not comms.tc_queue.empty():
            try:
                tc_data = comms.tc_queue.get()
                packet = CCSDSPacket.from_bytes(tc_data)
                
                if packet.packet_type != 1:  # Not a TC
                    self.logger.warning("Received non-TC packet")
                    continue

                command_data = json.loads(packet.payload.decode())
                target = command_data.get('subsystem')
                command = command_data.get('command')
                parameters = command_data.get('parameters', {})

                if target in self.subsystems:
                    subsystem = self.subsystems[target]
                    if subsystem.state != SubsystemState.OFF:
                        success = subsystem.process_command(command, parameters)
                        self.logger.info(f"Command {command} for {target} {'succeeded' if success else 'failed'}")
                    else:
                        self.logger.warning(f"Cannot process command: {target} is OFF")
                else:
                    self.logger.warning(f"Command received for unknown subsystem: {target}")

            except Exception as e:
                self.logger.error(f"Failed to process telecommand: {e}")

    def _can_change_mode(self, new_mode: OBCMode) -> bool:
        """Check if mode change is possible"""
        if self.state == SubsystemState.OFF:
            return False

        if new_mode == OBCMode.PAYLOAD:
            required_subsystems = ['ADCS', 'PAYLOAD', 'DATASTORE']
            for subsys in required_subsystems:
                if (subsys not in self.subsystems or 
                    self.subsystems[subsys].state == SubsystemState.OFF):
                    self.logger.warning(f"Cannot enter PAYLOAD mode: {subsys} not available")
                    return False
        return True

    def _change_mode(self, new_mode: OBCMode) -> None:
        """Change spacecraft mode"""
        old_mode = self.mode
        self.mode = new_mode
        self.logger.info(f"Mode changed from {old_mode.value} to {new_mode.value}")

        # Mode-specific configurations
        if new_mode == OBCMode.SAFE:
            self._configure_safe_mode()
        elif new_mode == OBCMode.NOMINAL:
            self._configure_nominal_mode()
        elif new_mode == OBCMode.PAYLOAD:
            self._configure_payload_mode()

    def _configure_safe_mode(self) -> None:
        """Configure spacecraft for safe mode"""
        if 'ADCS' in self.subsystems:
            self.subsystems['ADCS'].process_command('SET_MODE', {'mode': 'SUNPOINTING'})
        
        if 'PAYLOAD' in self.subsystems:
            self.subsystems['PAYLOAD'].process_command('SET_STATE', {'state': 'OFF'})

    def _configure_nominal_mode(self) -> None:
        """Configure spacecraft for nominal mode"""
        if 'ADCS' in self.subsystems:
            self.subsystems['ADCS'].process_command('SET_MODE', {'mode': 'NADIR'})

    def _configure_payload_mode(self) -> None:
        """Configure spacecraft for payload mode"""
        if 'ADCS' in self.subsystems:
            self.subsystems['ADCS'].process_command('SET_MODE', {'mode': 'NADIR'})
        
        if 'PAYLOAD' in self.subsystems:
            self.subsystems['PAYLOAD'].process_command('SET_STATE', {'state': 'IDLE'})

    def _reset_spacecraft(self) -> None:
        """Reset all spacecraft subsystems"""
        self.mode = OBCMode.SAFE
        for subsystem in self.subsystems.values():
            subsystem.process_command('SET_STATE', 
                {'state': SubsystemState.OFF.value})
        
        # Restart critical subsystems
        critical_subsystems = ['POWER', 'OBC', 'COMMS']
        for name in critical_subsystems:
            if name in self.subsystems:
                self.subsystems[name].process_command('SET_STATE', 
                    {'state': SubsystemState.IDLE.value})

    def _update_mode_requirements(self) -> None:
        """Ensure mode requirements are maintained"""
        if not self._can_change_mode(self.mode):
            self.logger.warning("Mode requirements not met, switching to SAFE mode")
            self._change_mode(OBCMode.SAFE)

    def _calculate_power_draw(self) -> float:
        """Calculate power draw based on current state"""
        if self.state == SubsystemState.OFF:
            return 0.0
        return self.config.obc['power']['active']

class PayloadSubsystem(SubsystemBase):
    def __init__(self, spacecraft_config: SpacecraftConfig, simulator_config: SimulatorConfig):
        super().__init__("PAYLOAD", spacecraft_config, simulator_config)
        self.status = 'READY'
        self.imaging = False
        self.image_progress = 0.0
        self.last_image_time = None
        self.datastore = None  # Will be set by simulator

    def get_telemetry(self) -> dict:
        """Return payload telemetry"""
        common_tm = super().get_telemetry()
        payload_tm = {
            'status': self.status
        }
        return {**common_tm, **payload_tm}

    def process_command(self, command: str, parameters: dict) -> bool:
        """Process payload commands"""
        if super().process_common_command(command, parameters):
            return True

        if command == 'CAPTURE':
            if self.state == SubsystemState.OFF:
                self.logger.warning("Cannot capture image while payload is OFF")
                return False
            
            if self.status != 'READY':
                self.logger.warning("Payload busy, cannot start new capture")
                return False
            
            if self.start_imaging():
                self.logger.info("Starting image capture")
                return True
            else:
                self.logger.error("Failed to start image capture")
                return False

        return False

    def start_imaging(self) -> bool:
        """Start capturing an image"""
        if self.state == SubsystemState.OFF or self.imaging:
            return False
            
        # Calculate image size using camera config
        camera_config = self.config.payload['camera']
        image_size = (camera_config['resolution'][0] * 
                     camera_config['resolution'][1] * 
                     camera_config['bits_per_pixel']) / (8 * 1024 * 1024)  # Convert to MB
        
        if self.datastore and self.datastore.has_space(image_size):
            self.imaging = True
            self.image_progress = 0.0
            self.status = 'BUSY'
            self.state = SubsystemState.ACTIVE
            self.last_image_time = datetime.now(timezone.utc)
            return True
        else:
            self.logger.warning("Not enough storage space for image")
            return False

    def update(self, dt: float, eclipse_state: str = 'NONE') -> None:
        """Update payload state"""
        super().update(dt, eclipse_state)

        if self.state == SubsystemState.OFF:
            self.status = 'READY'
            self.imaging = False
            self.image_progress = 0.0
            return

        if self.imaging:
            # Calculate image size in MB
            image_size = (self.config.payload['camera']['resolution'][0] * 
                         self.config.payload['camera']['resolution'][1] * 
                         self.config.payload['camera']['bits_per_pixel']) / (8 * 1024 * 1024)
            
            # Progress based on datastore write speed
            progress_rate = self.config.datastore['write_speed'] / image_size
            self.image_progress += progress_rate * dt
            
            if self.image_progress >= 1.0:
                self.complete_imaging()

        # Update power draw
        self.power_draw = self._calculate_power_draw()

    def complete_imaging(self) -> None:
        """Complete the imaging process"""
        if not self.imaging:
            return

        # Create image metadata
        image_metadata = {
            'timestamp': self.last_image_time.isoformat(),
            'resolution': self.config.payload['camera']['resolution'],
            'bits_per_pixel': self.config.payload['camera']['bits_per_pixel']
        }

        # Calculate image size in MB
        image_size = (self.config.payload['camera']['resolution'][0] * 
                     self.config.payload['camera']['resolution'][1] * 
                     self.config.payload['camera']['bits_per_pixel']) / (8 * 1024 * 1024)

        # Store the image
        if self.datastore:
            filename = f"IMG_{self.last_image_time.strftime('%Y%m%d_%H%M%S')}.raw"
            self.datastore.store_file(filename, image_size, image_metadata)

        self.imaging = False
        self.image_progress = 0.0
        self.status = 'READY'
        self.state = SubsystemState.IDLE
        self.logger.info("Image capture completed")

    def _calculate_power_draw(self) -> None:
        """Calculate power draw based on current state"""
        if self.state == SubsystemState.OFF:
            self.power_draw = 0.0
        elif self.state == SubsystemState.IDLE:
            self.power_draw = self.config.power['subsystems']['payload']['idle']
        elif self.state == SubsystemState.ACTIVE:
            if self.imaging:
                self.power_draw = self.config.power['subsystems']['payload']['imaging']
            else:
                self.power_draw = self.config.power['subsystems']['payload']['processing']

    def set_datastore(self, datastore) -> None:
        """Set reference to datastore subsystem"""
        self.datastore = datastore

class DatastoreSubsystem(SubsystemBase):
    def __init__(self, spacecraft_config: SpacecraftConfig, simulator_config: SimulatorConfig):
        super().__init__("DATASTORE", spacecraft_config, simulator_config)
        self.storage_remaining = self.config.datastore['total_storage']  # MB
        self.files = []  # List of stored files
        self.transfer_progress = 0.0
        self.current_transfer = None

    def get_telemetry(self) -> dict:
        """Return datastore telemetry"""
        common_tm = super().get_telemetry()
        datastore_tm = {
            'storage_remaining': self.storage_remaining,
            'number_of_files': len(self.files),
            'size_of_last_file': self.files[-1]['size'] if self.files else 0,
            'name_of_last_file': self.files[-1]['name'] if self.files else ''
        }
        return {**common_tm, **datastore_tm}

    def process_command(self, command: str, parameters: dict) -> bool:
        """Process datastore commands"""
        if super().process_common_command(command, parameters):
            return True

        if command == 'CLEAR_DATASTORE':
            self.files.clear()
            self.storage_remaining = self.config.datastore['total_storage']
            self.logger.info("Datastore cleared")
            return True

        elif command == 'DELETE_LAST_FILE':
            if self.files:
                last_file = self.files.pop()
                self.storage_remaining += last_file['size']
                self.logger.info(f"Deleted file: {last_file['name']}")
                return True
            return False

        elif command == 'TRANSFER_FILE':
            filename = parameters['filename']
            file_info = next((f for f in self.files if f['name'] == filename), None)
            if file_info:
                self.current_transfer = file_info
                self.transfer_progress = 0.0
                self.logger.info(f"Starting transfer of {filename}")
                return True
            return False

        elif command == 'TRANSFER_LAST_FILE':
            if self.files:
                self.current_transfer = self.files[-1]
                self.transfer_progress = 0.0
                self.logger.info(f"Starting transfer of {self.files[-1]['name']}")
                return True
            return False

        return False

    def update(self, dt: float, eclipse_state: str = 'NONE') -> None:
        """Update datastore state"""
        super().update(dt, eclipse_state)

        # Handle file transfer
        if self.current_transfer and self.state != SubsystemState.OFF:
            transfer_rate = self.config.datastore['transfer_speed'] * dt  # MB/s
            self.transfer_progress += transfer_rate / self.current_transfer['size']
            
            if self.transfer_progress >= 1.0:
                self.logger.info(f"Completed transfer of {self.current_transfer['name']}")
                self.current_transfer = None
                self.transfer_progress = 0.0

        # Update power draw
        self.power_draw = self._calculate_power_draw()

    def has_space(self, size_mb: float) -> bool:
        """Check if there's enough space for a new file"""
        return self.storage_remaining >= size_mb

    def store_file(self, filename: str, size_mb: float, metadata: dict) -> bool:
        """Store a new file"""
        if not self.has_space(size_mb):
            return False

        file_info = {
            'name': filename,
            'size': size_mb,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata
        }
        
        self.files.append(file_info)
        self.storage_remaining -= size_mb
        self.logger.info(f"Stored new file: {filename} ({size_mb:.1f} MB)")
        return True

    def _calculate_power_draw(self) -> float:
        """Calculate power draw based on current state"""
        if self.state == SubsystemState.OFF:
            return 0.0
        elif self.current_transfer:
            return self.config.datastore['power']['active']
        else:
            return self.config.datastore['power']['idle']

class CCSDSPacket:
    """CCSDS Space Packet Protocol implementation"""
    def __init__(self):
        self.version = 0              # 3 bits, always 0
        self.packet_type = 0          # 1 bit, 0=TM, 1=TC
        self.sec_header_flag = 0      # 1 bit
        self.apid = 0                 # 11 bits
        self.sequence_flags = 3       # 2 bits, 3=standalone packet
        self.sequence_count = 0       # 14 bits
        self.packet_length = 0        # 16 bits, (total length) - 7
        self.payload = bytearray()    # Variable length

    @classmethod
    def from_bytes(cls, data: bytes) -> 'CCSDSPacket':
        packet = cls()
        # First 16 bits contain version, type, sec header flag, and APID
        primary = int.from_bytes(data[0:2], byteorder='big')
        packet.version = (primary >> 13) & 0x7
        packet.packet_type = (primary >> 12) & 0x1
        packet.sec_header_flag = (primary >> 11) & 0x1
        packet.apid = primary & 0x7FF
        
        # Next 16 bits contain sequence flags and count
        sequence = int.from_bytes(data[2:4], byteorder='big')
        packet.sequence_flags = (sequence >> 14) & 0x3
        packet.sequence_count = sequence & 0x3FFF
        
        # Next 16 bits contain packet length
        packet.packet_length = int.from_bytes(data[4:6], byteorder='big')
        
        # Remaining bytes are payload
        packet.payload = bytearray(data[6:])
        return packet

    def to_bytes(self) -> bytes:
        # Construct primary header (6 bytes)
        primary = ((self.version & 0x7) << 13) | \
                 ((self.packet_type & 0x1) << 12) | \
                 ((self.sec_header_flag & 0x1) << 11) | \
                 (self.apid & 0x7FF)
        
        sequence = ((self.sequence_flags & 0x3) << 14) | \
                  (self.sequence_count & 0x3FFF)
        
        header = bytearray()
        header.extend(primary.to_bytes(2, byteorder='big'))
        header.extend(sequence.to_bytes(2, byteorder='big'))
        header.extend(len(self.payload).to_bytes(2, byteorder='big'))
        
        return bytes(header + self.payload)

class Simulator:
    def __init__(self, spacecraft_config: SpacecraftConfig, simulator_config: SimulatorConfig):
        self.spacecraft_config = spacecraft_config
        self.simulator_config = simulator_config
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, simulator_config.logging['level']),
            format=simulator_config.logging['format'],
            handlers=[
                logging.FileHandler(simulator_config.logging['file']),
                logging.StreamHandler() if simulator_config.logging['console'] else None
            ]
        )
        self.logger = logging.getLogger("Simulator")

        # Initialize simulation
        self.simulation_time = 0.0
        self.current_utc = simulator_config.time['start_utc']   
        self._init_statistics()
        self._init_subsystems()

    def run(self):
        """Run the simulation"""
        dt = self.simulator_config.time['time_step'] / self.simulator_config.time['time_factor']
        last_stats_time = datetime.now()
        last_telemetry_time = datetime.now()

        while True:
            try:
                # Update simulation
                self.update(dt)
                
                # Log statistics at specified interval
                if (datetime.now() - last_stats_time).total_seconds() >= self.simulator_config.logging['stats_interval']:
                    self._log_statistics()
                    last_stats_time = datetime.now()
                
                # Save telemetry at specified interval
                if (datetime.now() - last_telemetry_time).total_seconds() >= self.simulator_config.logging['telemetry']['save_interval']:
                    self._save_telemetry()
                    last_telemetry_time = datetime.now()
                
                time.sleep(dt)
                
            except KeyboardInterrupt:
                self.logger.info("Simulation stopped by user")
                break

    def _init_subsystems(self) -> None:
        """Initialize all spacecraft subsystems"""
        # Create subsystems
        self.power = PowerSubsystem(self.spacecraft_config, self.simulator_config)
        self.adcs = ADCSSubsystem(self.spacecraft_config, self.simulator_config)
        self.comms = CommunicationsSubsystem(self.spacecraft_config, self.simulator_config)
        self.payload = PayloadSubsystem(self.spacecraft_config, self.simulator_config)
        self.datastore = DatastoreSubsystem(self.spacecraft_config, self.simulator_config)
        self.obc = OBCSubsystem(self.spacecraft_config, self.simulator_config)
        
        # Register subsystems with OBC
        self.obc.register_subsystem(self.power)
        self.obc.register_subsystem(self.adcs)
        self.obc.register_subsystem(self.comms)
        self.obc.register_subsystem(self.payload)
        self.obc.register_subsystem(self.datastore)
        
        # Set up subsystem references
        self.payload.set_datastore(self.datastore)
        self.obc.simulation_time = self.simulation_time
        
        # Initialize subsystem states from config
        self._init_subsystem_states()

    def _init_subsystem_states(self) -> None:
        """Initialize subsystem states based on config"""
        # Initialize states from config
        self.power.process_command('SET_STATE', 
            {'state': SubsystemState(
                self.simulator_config.initial_states['power']).value})
        
        self.obc.process_command('SET_STATE',
            {'state': SubsystemState(
                self.simulator_config.initial_states['obc']).value})
        
        self.comms.process_command('SET_STATE',
            {'state': SubsystemState(
                self.simulator_config.initial_states['comms']).value})
        
        # Set ADCS state and mode
        self.adcs.process_command('SET_STATE',
            {'state': SubsystemState(
                self.simulator_config.initial_states['adcs']['state']).value})
        self.adcs.process_command('SET_MODE',
            {'mode': ADCSMode(
                self.simulator_config.initial_states['adcs']['mode']).value})
        
        self.payload.process_command('SET_STATE',
            {'state': SubsystemState(
                self.simulator_config.initial_states['payload']).value})
        
        self.datastore.process_command('SET_STATE',
            {'state': SubsystemState(
                self.simulator_config.initial_states['datastore']).value})

    def _init_statistics(self) -> None:
        """Initialize simulation statistics"""
        self.stats = {
            'simulation_time': 0.0,
            'power_generated': 0.0,
            'power_consumed': 0.0,
            'battery_charge': 100.0,
            'tm_packets_sent': 0,
            'tc_packets_received': 0,
            'eclipse_duration': 0.0,
            'eclipse_count': 0,
            'subsystem_states': {},
            'temperature_readings': {},
            'errors_detected': 0,
            'commands_processed': 0
        }

        # Initialize subsystem-specific stats
        for subsystem in ['power', 'obc', 'comms', 'adcs', 'payload', 'datastore']:
            self.stats['subsystem_states'][subsystem] = 'OFF'
            self.stats['temperature_readings'][subsystem] = 20.0  # Initial temperature

    def _update_statistics(self) -> None:
        """Update simulation statistics"""
        self.stats['simulation_time'] = self.simulation_time
        self.stats['power_generated'] = self.power.solar_power
        self.stats['power_consumed'] = sum(self.power.subsystem_power_draws.values())
        self.stats['battery_charge'] = self.power.battery_charge

        # Update subsystem states and temperatures
        for name, subsystem in {
            'power': self.power,
            'obc': self.obc,
            'comms': self.comms,
            'adcs': self.adcs,
            'payload': self.payload,
            'datastore': self.datastore
        }.items():
            self.stats['subsystem_states'][name] = subsystem.state.value
            self.stats['temperature_readings'][name] = subsystem.temperature

    def _log_statistics(self) -> None:
        """Log simulation statistics"""
        self._update_statistics()  # Ensure stats are current
        
        # Format quaternion for logging
        quat = self.adcs.current_quaternion
        quat_str = f"[{quat[0]:.3f}, {quat[1]:.3f}, {quat[2]:.3f}, {quat[3]:.3f}]"
        
        # Format times
        mission_time = self.current_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        self.logger.info(
            f"Simulation stats - "
            f"Mission Time: {mission_time}, "
            f"Power gen/used: {self.stats['power_generated']:.1f}/{self.stats['power_consumed']:.1f}W, "
            f"Battery: {self.stats['battery_charge']:.1f}%, "
            f"TM/TC: {self.stats['tm_packets_sent']}/{self.stats['tc_packets_received']}, "
            f"Quaternion: {quat_str}"
        )

    def _save_telemetry(self) -> None:
        """Save telemetry data to file"""
        # Implement telemetry saving logic here
        pass

    def _check_subsystem_states(self) -> bool:
        """Verify all subsystems are in valid states"""
        if self.power.state == self.spacecraft_config.SubsystemState.OFF:
            self.logger.error("Power subsystem is OFF")
            return False
            
        critical_subsystems = {
            'OBC': self.obc,
            'COMMS': self.comms
        }
        
        for name, subsystem in critical_subsystems.items():
            if subsystem.state == self.spacecraft_config.SubsystemState.OFF:
                self.logger.error(f"{name} subsystem is OFF")
                return False
                
        return True

    def update(self, dt: float) -> None:
        """Update simulation state
        
        Args:
            dt (float): Time step in seconds
        """
        # Update simulation time
        self.simulation_time += dt
        self.current_utc += timedelta(seconds=dt)

        # Propagate orbit and get vectors
        sun_vector, nadir_vector, lat, lon, alt, eclipse_state = self._propagate_orbit(dt)

        # Update subsystems in dependency order
        self.power.update(dt, sun_vector, self.adcs.current_quaternion, eclipse_state)
        self.obc.update(dt)
        self.comms.update(dt)
        self.adcs.update(dt, sun_vector, nadir_vector, eclipse_state)
        self.payload.update(dt)
        self.datastore.update(dt)

        # Update statistics
        self._update_statistics()

    def _propagate_orbit(self, dt: float) -> tuple:
        """Propagate orbit and calculate relevant vectors
        
        Args:
            dt (float): Time step in seconds
            
        Returns:
            tuple: (sun_vector, nadir_vector, latitude, longitude, altitude, eclipse_state)
        """
        # Simple circular orbit for now
        orbit_period = 2 * np.pi * np.sqrt(
            (self.simulator_config.orbit['semi_major_axis'] ** 3) / 
            self.simulator_config.environment['earth']['mu']
        )
        
        # Update orbit angle
        orbit_angle = (self.simulation_time * 2 * np.pi / orbit_period) % (2 * np.pi)
        
        # Calculate position in orbital frame
        x = self.simulator_config.orbit['semi_major_axis'] * np.cos(orbit_angle)
        y = self.simulator_config.orbit['semi_major_axis'] * np.sin(orbit_angle)
        
        # Calculate vectors
        position = np.array([x, y, 0])
        nadir_vector = -position / np.linalg.norm(position)
        
        # Simple sun vector (rotating with time)
        sun_angle = (self.simulation_time * 2 * np.pi / 
                    (24 * 3600)) % (2 * np.pi)  # 24-hour period
        sun_vector = np.array([np.cos(sun_angle), np.sin(sun_angle), 0])
        
        # Calculate eclipse state
        sun_dot_pos = np.dot(sun_vector, position)
        if sun_dot_pos < 0:
            # Check if in Earth's shadow
            shadow_dist = np.linalg.norm(np.cross(sun_vector, position))
            if shadow_dist < self.simulator_config.environment['earth']['radius']:
                eclipse_state = 'TOTAL'
            else:
                eclipse_state = 'NONE'
        else:
            eclipse_state = 'NONE'
        
        # Calculate lat/lon/alt (simplified)
        earth_rotation = self.simulator_config.environment['earth']['rotation_rate'] * self.simulation_time
        lon = np.degrees(np.arctan2(y, x) - earth_rotation) % 360
        lat = np.degrees(np.arcsin(0))  # Assuming equatorial orbit
        alt = np.linalg.norm(position) - self.simulator_config.environment['earth']['radius']
        
        return sun_vector, nadir_vector, lat, lon, alt, eclipse_state

# Main entry point
if __name__ == "__main__":
    # Load configurations
    spacecraft_config = SpacecraftConfig()
    simulator_config = SimulatorConfig()
    
    # Create and run simulator
    simulator = Simulator(spacecraft_config, simulator_config)
    
    try:
        simulator.run()
    except KeyboardInterrupt:
        simulator.stop()
