import numpy as np

class Environment:
    """Environmental models for space simulation"""
    
    @staticmethod
    def atmospheric_density(altitude):
        """Simple exponential atmospheric model
        Input: altitude in km
        Output: density in kg/m³
        """
        h0 = 7.249  # Scale height [km]
        rho0 = 1.225 # Sea level density [kg/m³]
        return rho0 * np.exp(-altitude / h0)
    
    @staticmethod
    def solar_illumination(spacecraft_pos, sun_pos, quaternion):
        """Calculate solar panel illumination angles
        Inputs: 
        - spacecraft_pos: [x,y,z] in km
        - sun_pos: [x,y,z] in km
        - quaternion: [q1,q2,q3,q4] spacecraft attitude
        Returns: Dictionary of panel illumination angles in degrees
        """
        # Calculate sun vector in ECI
        sun_vec = sun_pos - spacecraft_pos
        sun_vec = sun_vec / np.linalg.norm(sun_vec)
        
        # Convert quaternion to rotation matrix
        q = quaternion
        R = np.array([
            [1-2*(q[1]**2 + q[2]**2), 2*(q[0]*q[1] - q[2]*q[3]), 2*(q[0]*q[2] + q[1]*q[3])],
            [2*(q[0]*q[1] + q[2]*q[3]), 1-2*(q[0]**2 + q[2]**2), 2*(q[1]*q[2] - q[0]*q[3])],
            [2*(q[0]*q[2] - q[1]*q[3]), 2*(q[1]*q[2] + q[0]*q[3]), 1-2*(q[0]**2 + q[1]**2)]
        ])
        
        # Transform sun vector to body frame
        sun_body = R.T @ sun_vec
        
        # Calculate angles for each panel
        # cos(angle) = dot product with panel normal
        panels = {
            'pX': np.degrees(np.arccos(np.clip(sun_body[0], -1, 1))),
            'nX': np.degrees(np.arccos(np.clip(-sun_body[0], -1, 1))),
            'pY': np.degrees(np.arccos(np.clip(sun_body[1], -1, 1))),
            'nY': np.degrees(np.arccos(np.clip(-sun_body[1], -1, 1)))
        }
        
        return panels
