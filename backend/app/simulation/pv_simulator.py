"""PV system simulator."""
import numpy as np
from datetime import datetime
from typing import Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class PVSimulator:
    """Simulates photovoltaic system behavior."""
    
    def __init__(self, capacity_kw: float, efficiency: float, panel_area: float):
        self.capacity_kw = capacity_kw
        self.efficiency = efficiency
        self.panel_area = panel_area
        self.temperature_coefficient = -0.004  # Power decrease per °C above 25°C
        self.nominal_temperature = 25.0
        
    def calculate_irradiance(self, hour: float) -> float:
        """Calculate solar irradiance based on time of day."""
        # Simplified solar model: peak at noon
        if hour < 6 or hour > 18:
            return 0.0
        
        # Bell curve centered at noon
        peak_irradiance = 1000.0  # W/m² at peak
        sigma = 3.0  # Standard deviation
        irradiance = peak_irradiance * np.exp(-((hour - 12) ** 2) / (2 * sigma ** 2))
        
        # Add some random variation (clouds, etc.)
        variation = np.random.normal(1.0, 0.1)
        irradiance *= max(0.3, min(1.5, variation))
        
        return max(0, irradiance)
    
    def calculate_temperature(self, hour: float, base_temp: float = 25.0) -> float:
        """Calculate ambient temperature based on time of day."""
        # Temperature varies with time of day
        temp_variation = 8 * np.sin((hour - 6) * np.pi / 12)
        temperature = base_temp + temp_variation + np.random.normal(0, 1)
        return temperature
    
    def calculate_power_output(self, irradiance: float, temperature: float) -> float:
        """Calculate power output based on irradiance and temperature."""
        if irradiance <= 0:
            return 0.0
        
        # Basic power calculation
        power = self.panel_area * irradiance * self.efficiency / 1000  # kW
        
        # Temperature derating
        temp_diff = temperature - self.nominal_temperature
        temp_factor = 1 + self.temperature_coefficient * temp_diff
        power *= max(0.5, min(1.1, temp_factor))
        
        # Cap at capacity
        power = min(power, self.capacity_kw)
        
        return max(0, power)
    
    def simulate(self, timestamp: datetime = None) -> Dict[str, Any]:
        """Run simulation for current time."""
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour + timestamp.minute / 60.0
        
        irradiance = self.calculate_irradiance(hour)
        temperature = self.calculate_temperature(hour)
        power_output = self.calculate_power_output(irradiance, temperature)
        
        # Calculate electrical parameters
        voltage = 380 if power_output > 0 else 0
        current = (power_output * 1000 / voltage / np.sqrt(3)) if voltage > 0 else 0
        
        return {
            "irradiance": round(float(irradiance), 2),
            "temperature": round(float(temperature), 2),
            "power_output": round(float(power_output), 2),
            "voltage": round(float(voltage), 2),
            "current": round(float(current), 2),
            "efficiency": float(self.efficiency),
            "utilization": round(float(power_output / self.capacity_kw), 4) if self.capacity_kw > 0 else 0.0
        }
