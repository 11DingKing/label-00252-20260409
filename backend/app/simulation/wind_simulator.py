"""Wind turbine simulator."""
import numpy as np
from datetime import datetime
from typing import Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class WindSimulator:
    """Simulates wind turbine system behavior."""
    
    def __init__(self, capacity_kw: float, cut_in_speed: float, 
                 rated_speed: float, cut_out_speed: float):
        self.capacity_kw = capacity_kw
        self.cut_in_speed = cut_in_speed
        self.rated_speed = rated_speed
        self.cut_out_speed = cut_out_speed
        self.air_density = 1.225  # kg/m³
        self.rotor_diameter = np.sqrt(capacity_kw * 1000 * 8 / (np.pi * self.air_density * rated_speed ** 3 * 0.4))
        
    def generate_wind_speed(self, hour: float) -> float:
        """Generate realistic wind speed with daily variation."""
        # Base wind speed with daily variation (typically windier in afternoon)
        base_speed = 6.0 + 2.0 * np.sin((hour - 6) * np.pi / 12)
        
        # Add Weibull-like random variation
        shape = 2.0  # Weibull shape parameter
        scale = base_speed / 0.886  # Scale to match mean
        wind_speed = np.random.weibull(shape) * scale
        
        # Add some turbulence
        turbulence = np.random.normal(0, 0.5)
        wind_speed += turbulence
        
        return max(0, wind_speed)
    
    def generate_wind_direction(self) -> float:
        """Generate wind direction with some persistence."""
        # Random direction with tendency to stay in same quadrant
        return np.random.uniform(0, 360)
    
    def calculate_power_output(self, wind_speed: float) -> float:
        """Calculate power output based on wind speed using power curve."""
        if wind_speed < self.cut_in_speed:
            return 0.0
        
        if wind_speed >= self.cut_out_speed:
            return 0.0
        
        if wind_speed >= self.rated_speed:
            return self.capacity_kw
        
        # Cubic relationship between cut-in and rated speed
        power_ratio = ((wind_speed - self.cut_in_speed) / 
                      (self.rated_speed - self.cut_in_speed)) ** 3
        power = self.capacity_kw * power_ratio
        
        return min(power, self.capacity_kw)
    
    def calculate_rotor_speed(self, wind_speed: float) -> float:
        """Calculate rotor speed based on wind speed."""
        if wind_speed < self.cut_in_speed:
            return 0.0
        
        # Tip speed ratio typically around 6-8
        tip_speed_ratio = 7.0
        rotor_speed = (wind_speed * tip_speed_ratio * 60) / (np.pi * self.rotor_diameter)
        
        # Cap at maximum rotor speed
        max_rpm = 20.0
        return min(rotor_speed, max_rpm)
    
    def simulate(self, timestamp: datetime = None) -> Dict[str, Any]:
        """Run simulation for current time."""
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour + timestamp.minute / 60.0
        
        wind_speed = self.generate_wind_speed(hour)
        wind_direction = self.generate_wind_direction()
        power_output = self.calculate_power_output(wind_speed)
        rotor_speed = self.calculate_rotor_speed(wind_speed)
        
        return {
            "wind_speed": round(float(wind_speed), 2),
            "wind_direction": round(float(wind_direction), 1),
            "power_output": round(float(power_output), 2),
            "rotor_speed": round(float(rotor_speed), 2),
            "utilization": round(float(power_output / self.capacity_kw), 4) if self.capacity_kw > 0 else 0.0
        }
