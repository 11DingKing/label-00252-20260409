"""Battery storage system simulator."""
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class BatterySimulator:
    """Simulates battery energy storage system behavior."""
    
    def __init__(self, capacity_kwh: float, max_charge_rate: float, 
                 max_discharge_rate: float, charge_efficiency: float,
                 discharge_efficiency: float, min_soc: float, max_soc: float):
        self.capacity_kwh = capacity_kwh
        self.max_charge_rate = max_charge_rate
        self.max_discharge_rate = max_discharge_rate
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.min_soc = min_soc
        self.max_soc = max_soc
        
        # State variables
        self.soc = 0.5  # Initial SOC at 50%
        self.power = 0.0  # Current power (positive=discharge, negative=charge)
        self.temperature = 25.0
        self.status = "idle"
        
        # Battery parameters
        self.nominal_voltage = 400.0  # V
        self.internal_resistance = 0.01  # Ohms
    
    def update_soc_limits(self, min_soc: float, max_soc: float) -> None:
        """Update SOC limits dynamically."""
        self.min_soc = min_soc
        self.max_soc = max_soc
        # Clamp current SOC to new limits
        self.soc = max(self.min_soc, min(self.max_soc, self.soc))
        
    def set_power(self, power: float) -> float:
        """Set battery power command and return actual power."""
        # Positive power = discharge, negative power = charge
        
        if power > 0:  # Discharge
            # Check SOC limit
            available_energy = (self.soc - self.min_soc) * self.capacity_kwh
            max_power = min(self.max_discharge_rate, available_energy * 3600)  # Assuming 1 second step
            actual_power = min(power, max_power)
            self.status = "discharging" if actual_power > 0 else "idle"
            
        elif power < 0:  # Charge
            # Check SOC limit
            available_capacity = (self.max_soc - self.soc) * self.capacity_kwh
            max_power = min(self.max_charge_rate, available_capacity * 3600)
            actual_power = max(power, -max_power)
            self.status = "charging" if actual_power < 0 else "idle"
            
        else:
            actual_power = 0.0
            self.status = "idle"
        
        self.power = actual_power
        return actual_power
    
    def update_soc(self, dt: float = 1.0) -> None:
        """Update SOC based on current power and time step."""
        if self.power > 0:  # Discharging
            energy_out = self.power * dt / 3600  # kWh
            energy_from_battery = energy_out / self.discharge_efficiency
            self.soc -= energy_from_battery / self.capacity_kwh
        elif self.power < 0:  # Charging
            energy_in = abs(self.power) * dt / 3600  # kWh
            energy_to_battery = energy_in * self.charge_efficiency
            self.soc += energy_to_battery / self.capacity_kwh
        
        # Clamp SOC
        self.soc = max(self.min_soc, min(self.max_soc, self.soc))
        
        # Update temperature based on power
        heat_generation = abs(self.power) * 0.05  # 5% of power as heat
        ambient_temp = 25.0
        thermal_time_constant = 300.0  # seconds
        self.temperature += (heat_generation * 0.1 - (self.temperature - ambient_temp) / thermal_time_constant) * dt
    
    def calculate_voltage(self) -> float:
        """Calculate terminal voltage based on SOC and current."""
        # Open circuit voltage varies with SOC
        ocv = self.nominal_voltage * (0.9 + 0.2 * self.soc)
        
        # Voltage drop due to internal resistance
        current = self.power * 1000 / self.nominal_voltage if self.nominal_voltage > 0 else 0
        voltage_drop = current * self.internal_resistance
        
        if self.power > 0:  # Discharging
            return ocv - voltage_drop
        else:  # Charging or idle
            return ocv + abs(voltage_drop)
    
    def calculate_current(self) -> float:
        """Calculate battery current."""
        voltage = self.calculate_voltage()
        if voltage > 0:
            return self.power * 1000 / voltage
        return 0.0
    
    def simulate(self, power_command: Optional[float] = None, dt: float = 1.0) -> Dict[str, Any]:
        """Run simulation step."""
        if power_command is not None:
            self.set_power(power_command)
        
        self.update_soc(dt)
        
        voltage = self.calculate_voltage()
        current = self.calculate_current()
        
        return {
            "soc": round(float(self.soc), 4),
            "power": round(float(self.power), 2),
            "voltage": round(float(voltage), 2),
            "current": round(float(current), 2),
            "temperature": round(float(self.temperature), 2),
            "status": self.status,
            "available_energy": round(float(self.soc * self.capacity_kwh), 2)
        }
    
    def get_available_charge_power(self) -> float:
        """Get maximum available charging power."""
        available_capacity = (self.max_soc - self.soc) * self.capacity_kwh
        return min(self.max_charge_rate, available_capacity * 3600)
    
    def get_available_discharge_power(self) -> float:
        """Get maximum available discharging power."""
        available_energy = (self.soc - self.min_soc) * self.capacity_kwh
        return min(self.max_discharge_rate, available_energy * 3600)
