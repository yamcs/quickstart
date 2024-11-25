import numpy as np
from datetime import datetime

class CelestialBody:
    """Base class for celestial bodies"""
    def __init__(self, name, mass, radius):
        self.name = name
        self.mass = mass      # kg
        self.radius = radius  # meters
        
    def gravitational_parameter(self):
        """Calculate μ = GM"""
        G = 6.67430e-11  # m^3 kg^-1 s^-2
        return G * self.mass

class Earth(CelestialBody):
    def __init__(self):
        super().__init__(
            name="Earth",
            mass=5.972e24,    # kg
            radius=6371.0e3   # meters
        )
        self.rotation_rate = 7.2921150e-5  # rad/s
        self.J2 = 1.08263e-3  # Earth's J2 perturbation
        
    def get_position_at_time(self, time):
        """Earth is at origin of ECI frame"""
        return np.array([0.0, 0.0, 0.0])

class Sun(CelestialBody):
    def __init__(self):
        super().__init__(
            name="Sun",
            mass=1.989e30,    # kg
            radius=696340e3   # meters
        )
        
    def get_position_at_time(self, time):
        """Simple solar position model in ECI frame
        Based on simplified orbital elements"""
        # Earth's orbital period in seconds
        year = 365.25 * 24 * 3600
        
        # Earth's mean orbital radius
        au = 149597870.7e3  # meters
        
        # Calculate solar angle based on time
        t_epoch = datetime(2000, 1, 1, 12, 0, 0)  # J2000 epoch
        dt = (time - t_epoch).total_seconds()
        theta = (2 * np.pi * dt / year) % (2 * np.pi)
        
        # Return solar position in ECI
        x = au * np.cos(theta)
        y = au * np.sin(theta)
        return np.array([x, y, 0.0])

class Moon(CelestialBody):
    def __init__(self):
        super().__init__(
            name="Moon",
            mass=7.34767309e22,  # kg
            radius=1737.1e3      # meters
        )
        
    def get_position_at_time(self, time):
        """Simple lunar position model in ECI frame"""
        # Moon's orbital period in seconds
        month = 27.32 * 24 * 3600
        
        # Moon's mean orbital radius
        radius = 384400e3  # meters
        
        # Calculate lunar angle based on time
        t_epoch = datetime(2000, 1, 1, 12, 0, 0)
        dt = (time - t_epoch).total_seconds()
        theta = (2 * np.pi * dt / month) % (2 * np.pi)
        
        # Include 5.145° orbital inclination
        incl = np.radians(5.145)
        
        # Return lunar position in ECI
        x = radius * np.cos(theta)
        y = radius * np.sin(theta) * np.cos(incl)
        z = radius * np.sin(theta) * np.sin(incl)
        return np.array([x, y, z]) 