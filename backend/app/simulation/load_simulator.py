"""Load simulator."""
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from app.core.logging import get_logger

logger = get_logger(__name__)


class LoadSimulator:
    """Simulates various types of electrical loads."""
    
    # Load profiles by type (hourly multipliers)
    LOAD_PROFILES = {
        "office": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.3, 0.6, 0.9, 1.0, 1.0, 0.9,
                   0.8, 0.9, 1.0, 1.0, 0.9, 0.7, 0.4, 0.2, 0.1, 0.1, 0.1, 0.1],
        "production": [0.3, 0.3, 0.3, 0.3, 0.3, 0.4, 0.6, 0.9, 1.0, 1.0, 1.0, 0.9,
                       0.8, 0.9, 1.0, 1.0, 1.0, 0.8, 0.5, 0.4, 0.3, 0.3, 0.3, 0.3],
        "lighting": [0.8, 0.8, 0.8, 0.8, 0.8, 0.6, 0.3, 0.2, 0.2, 0.2, 0.2, 0.2,
                     0.2, 0.2, 0.2, 0.2, 0.3, 0.5, 0.8, 0.9, 0.9, 0.9, 0.9, 0.8],
        "hvac": [0.3, 0.3, 0.3, 0.3, 0.3, 0.4, 0.5, 0.7, 0.9, 1.0, 1.0, 1.0,
                 1.0, 1.0, 1.0, 0.9, 0.8, 0.6, 0.4, 0.3, 0.3, 0.3, 0.3, 0.3],
        "ev_charger": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.3, 0.4, 0.3, 0.2, 0.3,
                       0.4, 0.3, 0.2, 0.3, 0.5, 0.7, 0.8, 0.6, 0.4, 0.2, 0.1, 0.1],
        "other": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.6, 0.7, 0.8, 0.8, 0.8,
                  0.8, 0.8, 0.8, 0.8, 0.7, 0.6, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
    }
    
    def __init__(self, load_id: int, name: str, load_type: str, 
                 rated_power: float, priority: int, is_controllable: bool):
        self.load_id = load_id
        self.name = name
        self.load_type = load_type
        self.rated_power = rated_power
        self.priority = priority
        self.is_controllable = is_controllable
        self.is_on = True
        self.power_factor = 0.95
        
        # For EV charger simulation (flash charging)
        self.ev_charging_active = False
        self.ev_charge_start_time = None
        self.ev_charge_duration = 0
        
    def get_base_load_factor(self, hour: int) -> float:
        """Get base load factor from profile."""
        profile = self.LOAD_PROFILES.get(self.load_type, self.LOAD_PROFILES["other"])
        return profile[hour % 24]
    
    def simulate_ev_charger(self, timestamp: datetime) -> float:
        """Simulate EV flash charger with impulse load characteristics."""
        hour = timestamp.hour
        
        # Random charging events during typical hours
        if not self.ev_charging_active:
            # Probability of starting a charge session
            charge_probability = self.LOAD_PROFILES["ev_charger"][hour] * 0.1
            if np.random.random() < charge_probability:
                self.ev_charging_active = True
                self.ev_charge_start_time = timestamp
                self.ev_charge_duration = np.random.randint(5, 30)  # 5-30 minutes
        
        if self.ev_charging_active:
            # Check if charging session is complete
            if self.ev_charge_start_time:
                elapsed = (timestamp - self.ev_charge_start_time).total_seconds() / 60
                if elapsed >= self.ev_charge_duration:
                    self.ev_charging_active = False
                    self.ev_charge_start_time = None
                    return 0.0
            
            # Flash charging profile: high initial power, tapering off
            if self.ev_charge_start_time:
                elapsed = (timestamp - self.ev_charge_start_time).total_seconds() / 60
                # Exponential decay from peak power
                power_factor = np.exp(-elapsed / (self.ev_charge_duration * 0.5))
                # Add some noise
                power_factor *= (1 + np.random.normal(0, 0.1))
                return min(1.0, max(0.3, power_factor))
        
        return 0.0
    
    def simulate(self, timestamp: datetime = None) -> Dict[str, Any]:
        """Run load simulation."""
        if timestamp is None:
            timestamp = datetime.now()
        
        if not self.is_on:
            return {
                "load_id": self.load_id,
                "name": self.name,
                "load_type": self.load_type,
                "power": 0.0,
                "voltage": 380.0,
                "current": 0.0,
                "power_factor": float(self.power_factor),
                "rated_power": float(self.rated_power),
                "priority": self.priority,
                "is_on": False,
                "utilization": 0.0
            }
        
        hour = timestamp.hour
        
        # Get base load factor
        if self.load_type == "ev_charger":
            load_factor = self.simulate_ev_charger(timestamp)
            if load_factor == 0:
                load_factor = self.get_base_load_factor(hour) * 0.1  # Standby power
        else:
            load_factor = self.get_base_load_factor(hour)
        
        # Add random variation
        variation = np.random.normal(1.0, 0.05)
        load_factor *= max(0.5, min(1.2, variation))
        
        # Calculate power
        power = self.rated_power * load_factor
        
        # Calculate electrical parameters
        voltage = 380.0
        current = power * 1000 / (voltage * np.sqrt(3) * self.power_factor)
        
        return {
            "load_id": self.load_id,
            "name": self.name,
            "load_type": self.load_type,
            "power": round(float(power), 2),
            "voltage": round(float(voltage), 2),
            "current": round(float(current), 2),
            "power_factor": float(self.power_factor),
            "rated_power": float(self.rated_power),
            "priority": self.priority,
            "is_on": bool(self.is_on),
            "utilization": round(float(power / self.rated_power), 4) if self.rated_power > 0 else 0.0
        }
    
    def set_state(self, is_on: bool) -> None:
        """Set load on/off state."""
        if self.is_controllable:
            self.is_on = is_on
            if not is_on:
                self.ev_charging_active = False
                self.ev_charge_start_time = None
