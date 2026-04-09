"""Grid connection simulator."""
import numpy as np
from datetime import datetime
from typing import Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class GridSimulator:
    """Simulates grid connection and power exchange."""
    
    def __init__(self, max_import: float, max_export: float, 
                 connection_type: str = "bidirectional"):
        self.max_import = max_import
        self.max_export = max_export
        self.connection_type = connection_type
        self.is_connected = True
        self.mode = "grid_connected"
        
        # Grid parameters
        self.nominal_voltage = 380.0  # V
        self.nominal_frequency = 50.0  # Hz
        self.nominal_phase_angle = 0.0  # degrees
        
        # Stability tolerances (as per requirements)
        self.voltage_tolerance = 0.05  # ±5%
        self.frequency_tolerance = 0.004  # ±0.2 Hz (0.2/50 = 0.004)
        self.phase_angle_tolerance = 5.0  # ±5 degrees for phase stability
        
        # Current state
        self.power = 0.0
        self.voltage = self.nominal_voltage
        self.frequency = self.nominal_frequency
        self.phase_angle = 0.0
        
        # Phase-locked loop (PLL) simulation parameters
        self.pll_locked = True
        self.pll_lock_threshold = 3.0  # degrees - threshold for PLL lock
        
    def set_mode(self, mode: str) -> bool:
        """Set grid connection mode."""
        if mode in ["grid_connected", "islanded"]:
            self.mode = mode
            self.is_connected = (mode == "grid_connected")
            return True
        return False
    
    def calculate_power_exchange(self, generation: float, load: float, 
                                  battery_power: float) -> float:
        """Calculate required power exchange with grid."""
        # Power balance: generation + grid_import = load + battery_charge
        # grid_power = load + battery_power - generation
        # Positive = import from grid, Negative = export to grid
        
        net_power = load + battery_power - generation
        
        if not self.is_connected:
            return 0.0
        
        # Apply limits based on connection type
        if self.connection_type == "import_only":
            net_power = max(0, net_power)
        elif self.connection_type == "export_only":
            net_power = min(0, net_power)
        
        # Apply power limits
        if net_power > 0:  # Import
            net_power = min(net_power, self.max_import)
        else:  # Export
            net_power = max(net_power, -self.max_export)
        
        return net_power
    
    def simulate_grid_quality(self, power_imbalance: float = 0) -> None:
        """Simulate grid voltage, frequency, and phase angle variations."""
        if self.is_connected:
            # Voltage variation based on power flow and random disturbance
            # Higher power import tends to reduce voltage slightly
            power_effect = -power_imbalance * 0.01  # 0.01V per kW imbalance
            voltage_noise = np.random.normal(0, self.nominal_voltage * 0.01)
            self.voltage = self.nominal_voltage + power_effect + voltage_noise
            
            # Frequency variation - affected by power imbalance
            # Power deficit causes frequency drop, surplus causes increase
            freq_power_effect = -power_imbalance * 0.001  # 0.001 Hz per kW
            freq_noise = np.random.normal(0, 0.05)
            self.frequency = self.nominal_frequency + freq_power_effect + freq_noise
            
            # Phase angle variation - simulates synchronization with grid
            # Phase angle affected by frequency deviation and power flow
            phase_freq_effect = (self.frequency - self.nominal_frequency) * 2  # degrees
            phase_noise = np.random.normal(0, 0.5)
            self.phase_angle = phase_freq_effect + phase_noise
            
            # Update PLL lock status
            self.pll_locked = abs(self.phase_angle) < self.pll_lock_threshold
            
        else:
            # Islanded mode - internal voltage/frequency control needed
            # Larger variations without grid support
            self.voltage = self.nominal_voltage + np.random.normal(0, self.nominal_voltage * 0.02)
            self.frequency = self.nominal_frequency + np.random.normal(0, 0.1)
            self.phase_angle = np.random.normal(0, 2)
            self.pll_locked = False
    
    def check_grid_stability(self) -> Dict[str, Any]:
        """Check if grid parameters are within acceptable limits."""
        voltage_deviation = abs(self.voltage - self.nominal_voltage) / self.nominal_voltage
        frequency_deviation = abs(self.frequency - self.nominal_frequency)
        phase_deviation = abs(self.phase_angle - self.nominal_phase_angle)
        
        voltage_ok = voltage_deviation <= self.voltage_tolerance
        frequency_ok = frequency_deviation <= self.frequency_tolerance * self.nominal_frequency
        phase_ok = phase_deviation <= self.phase_angle_tolerance
        
        return {
            "voltage_stable": bool(voltage_ok),
            "frequency_stable": bool(frequency_ok),
            "phase_stable": bool(phase_ok),
            "pll_locked": bool(self.pll_locked),
            "overall_stable": bool(voltage_ok and frequency_ok and phase_ok),
            "voltage_deviation_percent": round(float(voltage_deviation * 100), 2),
            "frequency_deviation_hz": round(float(frequency_deviation), 3),
            "phase_deviation_deg": round(float(phase_deviation), 2)
        }
    
    def apply_phase_correction(self, correction: float) -> None:
        """Apply phase angle correction from control system."""
        # Simulate phase correction effect (e.g., from inverter control)
        # Correction is in degrees, applied gradually
        correction_rate = 0.5  # Apply 50% of correction per cycle
        self.phase_angle -= correction * correction_rate
        
        # Clamp phase angle to reasonable range
        self.phase_angle = max(-30, min(30, self.phase_angle))
    
    def simulate(self, generation: float = 0, load: float = 0, 
                 battery_power: float = 0) -> Dict[str, Any]:
        """Run grid simulation."""
        self.power = self.calculate_power_exchange(generation, load, battery_power)
        
        # Calculate power imbalance for quality simulation
        power_imbalance = load - generation - battery_power - self.power
        self.simulate_grid_quality(power_imbalance)
        
        stability = self.check_grid_stability()
        
        return {
            "power": round(float(self.power), 2),
            "voltage": round(float(self.voltage), 2),
            "frequency": round(float(self.frequency), 4),
            "phase_angle": round(float(self.phase_angle), 2),
            "mode": self.mode,
            "is_connected": bool(self.is_connected),
            "max_import": float(self.max_import),
            "max_export": float(self.max_export),
            "pll_locked": bool(self.pll_locked),
            "stability": stability
        }
