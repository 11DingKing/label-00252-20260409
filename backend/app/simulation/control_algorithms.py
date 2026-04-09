"""Control algorithms for microgrid management."""
import numpy as np
from typing import Dict, Any, List, Optional
from scipy.optimize import minimize
from app.core.logging import get_logger

logger = get_logger(__name__)


class PIDController:
    """PID controller for power balance and voltage/frequency regulation."""
    
    def __init__(self, kp: float = 1.0, ki: float = 0.1, kd: float = 0.05,
                 setpoint: float = 0.0, output_limits: tuple = (-1000, 1000)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        
        self.integral = 0.0
        self.previous_error = 0.0
        self.last_output = 0.0
        
    def reset(self):
        """Reset controller state."""
        self.integral = 0.0
        self.previous_error = 0.0
        self.last_output = 0.0
        
    def compute(self, measurement: float, dt: float = 1.0) -> float:
        """Compute PID output."""
        error = self.setpoint - measurement
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term with anti-windup
        self.integral += error * dt
        # Anti-windup: limit integral
        max_integral = (self.output_limits[1] - self.output_limits[0]) / (2 * self.ki) if self.ki != 0 else 1000
        self.integral = max(-max_integral, min(max_integral, self.integral))
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = (error - self.previous_error) / dt if dt > 0 else 0
        d_term = self.kd * derivative
        
        # Calculate output
        output = p_term + i_term + d_term
        
        # Apply output limits
        output = max(self.output_limits[0], min(self.output_limits[1], output))
        
        # Store for next iteration
        self.previous_error = error
        self.last_output = output
        
        return output


class MPCController:
    """Model Predictive Controller for optimal power dispatch."""
    
    def __init__(self, prediction_horizon: int = 10, control_horizon: int = 5):
        self.prediction_horizon = prediction_horizon
        self.control_horizon = control_horizon
        self.weights = {
            "power_balance": 100.0,
            "battery_usage": 1.0,
            "grid_usage": 5.0,
            "load_shedding": 50.0
        }
        # Load history for improved prediction
        self.load_history: List[Dict[str, Any]] = []
        self.impulse_detection_threshold = 0.3  # 30% sudden increase
        
    def set_load_history(self, history: List[Dict[str, Any]]) -> None:
        """Set load history for improved prediction."""
        self.load_history = history
        
    def predict_generation(self, current_pv: float, current_wind: float, 
                          steps: int) -> List[Dict[str, float]]:
        """Predict future generation (simplified persistence model)."""
        predictions = []
        for i in range(steps):
            # Simple persistence with decay
            decay = 0.95 ** i
            predictions.append({
                "pv": current_pv * decay * (1 + np.random.normal(0, 0.1)),
                "wind": current_wind * decay * (1 + np.random.normal(0, 0.1))
            })
        return predictions
    
    def detect_impulse_load(self) -> tuple:
        """
        Detect impulse/shock loads from history.
        Returns (is_impulse, impulse_magnitude, decay_rate)
        """
        if len(self.load_history) < 5:
            return False, 0, 0
        
        recent = [h["total_load"] for h in self.load_history[-10:]]
        if len(recent) < 3:
            return False, 0, 0
        
        # Calculate rate of change
        avg_old = np.mean(recent[:-3]) if len(recent) > 3 else recent[0]
        avg_new = np.mean(recent[-3:])
        
        if avg_old > 0:
            change_rate = (avg_new - avg_old) / avg_old
            
            # Detect sudden increase (impulse load like EV fast charging)
            if change_rate > self.impulse_detection_threshold:
                # Estimate impulse magnitude and decay
                impulse_magnitude = avg_new - avg_old
                # Estimate decay rate from recent trend
                if len(recent) >= 5:
                    decay_samples = recent[-5:]
                    if decay_samples[-1] < decay_samples[-3]:
                        decay_rate = 0.9  # Fast decay
                    else:
                        decay_rate = 0.98  # Slow decay
                else:
                    decay_rate = 0.95
                return True, impulse_magnitude, decay_rate
        
        return False, 0, 0
    
    def predict_load(self, current_load: float, steps: int) -> List[float]:
        """
        Predict future load with improved impulse load handling.
        Uses historical data to detect and predict impulse loads.
        """
        predictions = []
        
        # Detect if we're in an impulse load situation
        is_impulse, impulse_mag, decay_rate = self.detect_impulse_load()
        
        # Calculate baseline load (excluding impulse)
        if len(self.load_history) >= 10:
            # Use median of older samples as baseline
            older_loads = [h["total_load"] for h in self.load_history[:-5]]
            baseline = np.median(older_loads) if older_loads else current_load * 0.8
        else:
            baseline = current_load * 0.8
        
        for i in range(steps):
            if is_impulse:
                # Model impulse decay
                impulse_component = impulse_mag * (decay_rate ** i)
                predicted = baseline + impulse_component
                # Add small variation
                predicted *= (1 + np.random.normal(0, 0.03))
            else:
                # Standard persistence model with variation
                predicted = current_load * (1 + np.random.normal(0, 0.05))
            
            predictions.append(max(0, predicted))
        
        return predictions
    
    def optimize(self, current_state: Dict[str, Any], 
                 constraints: Dict[str, Any]) -> Dict[str, float]:
        """Optimize power dispatch using MPC."""
        # Current state
        pv_power = current_state.get("pv_power", 0)
        wind_power = current_state.get("wind_power", 0)
        load_power = current_state.get("load_power", 0)
        battery_soc = current_state.get("battery_soc", 0.5)
        battery_capacity = constraints.get("battery_capacity", 1000)
        max_charge = constraints.get("max_charge_rate", 200)
        max_discharge = constraints.get("max_discharge_rate", 200)
        max_grid_import = constraints.get("max_grid_import", 800)
        max_grid_export = constraints.get("max_grid_export", 500)
        
        # Predict future states
        gen_predictions = self.predict_generation(pv_power, wind_power, self.prediction_horizon)
        load_predictions = self.predict_load(load_power, self.prediction_horizon)
        
        # Check for impulse load - if detected, be more aggressive with battery
        is_impulse, _, _ = self.detect_impulse_load()
        
        # Optimization objective function
        def objective(x):
            battery_power = x[0]  # Positive = discharge
            
            total_cost = 0
            soc = battery_soc
            
            for i in range(min(self.control_horizon, len(gen_predictions))):
                gen = gen_predictions[i]["pv"] + gen_predictions[i]["wind"]
                load = load_predictions[i]
                
                # Power balance
                grid_power = load - gen - battery_power
                
                # Update SOC
                if battery_power > 0:  # Discharge
                    soc -= battery_power / battery_capacity / 3600
                else:  # Charge
                    soc += abs(battery_power) / battery_capacity / 3600
                
                # Cost terms
                power_imbalance = abs(gen + grid_power + battery_power - load)
                total_cost += self.weights["power_balance"] * power_imbalance ** 2
                total_cost += self.weights["battery_usage"] * abs(battery_power)
                total_cost += self.weights["grid_usage"] * abs(grid_power)
                
                # SOC penalty
                if soc < 0.2 or soc > 0.9:
                    total_cost += 100 * (min(0, soc - 0.2) ** 2 + max(0, soc - 0.9) ** 2)
                
                # Extra penalty for grid import during impulse load
                if is_impulse and grid_power > 0:
                    total_cost += 20 * grid_power  # Prefer battery discharge
            
            return total_cost
        
        # Constraints
        bounds = [(-max_charge, max_discharge)]
        
        # Initial guess - bias towards discharge if impulse detected
        x0 = [max_discharge * 0.3] if is_impulse else [0]
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds)
        
        optimal_battery_power = result.x[0]
        
        # Calculate grid power
        total_generation = pv_power + wind_power
        optimal_grid_power = load_power - total_generation - optimal_battery_power
        
        # Apply grid limits
        if optimal_grid_power > max_grid_import:
            # Need to shed load or discharge more battery
            deficit = optimal_grid_power - max_grid_import
            optimal_grid_power = max_grid_import
            # Try to increase battery discharge
            additional_discharge = min(deficit, max_discharge - optimal_battery_power)
            optimal_battery_power += additional_discharge
        elif optimal_grid_power < -max_grid_export:
            # Need to curtail generation or charge more battery
            surplus = -optimal_grid_power - max_grid_export
            optimal_grid_power = -max_grid_export
            # Try to increase battery charge
            additional_charge = min(surplus, max_charge + optimal_battery_power)
            optimal_battery_power -= additional_charge
        
        return {
            "battery_power": round(optimal_battery_power, 2),
            "grid_power": round(optimal_grid_power, 2),
            "optimization_cost": round(result.fun, 2),
            "impulse_detected": is_impulse
        }


class EnergyManagementSystem:
    """Energy Management System for microgrid optimization."""
    
    def __init__(self):
        # Voltage PID controller: setpoint 380V, ±5% tolerance = ±19V
        self.pid_voltage = PIDController(kp=10, ki=1, kd=0.5, setpoint=380, output_limits=(-100, 100))
        # Frequency PID controller: setpoint 50Hz, ±0.2Hz tolerance
        self.pid_frequency = PIDController(kp=50, ki=5, kd=1, setpoint=50, output_limits=(-50, 50))
        # Phase angle PID controller: setpoint 0°, maintain synchronization
        self.pid_phase_angle = PIDController(kp=20, ki=2, kd=1, setpoint=0, output_limits=(-30, 30))
        
        self.mpc = MPCController()
        self.active_strategy = "economic"
        self.strategy_params = {}
        
        # Stability thresholds
        self.voltage_tolerance = 0.05  # ±5%
        self.frequency_tolerance = 0.2  # ±0.2 Hz
        self.phase_angle_tolerance = 5.0  # ±5 degrees
        
    def set_strategy(self, strategy_type: str, params: Dict[str, Any]) -> None:
        """Set active control strategy."""
        self.active_strategy = strategy_type
        self.strategy_params = params
        
    def check_stability(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Check voltage, frequency, and phase angle stability."""
        grid_voltage = state.get("grid_voltage", 380)
        grid_frequency = state.get("grid_frequency", 50)
        phase_angle = state.get("phase_angle", 0)
        
        voltage_deviation = abs(grid_voltage - 380) / 380 * 100
        frequency_deviation = abs(grid_frequency - 50)
        phase_deviation = abs(phase_angle)
        
        return {
            "voltage_stable": voltage_deviation <= self.voltage_tolerance * 100,
            "frequency_stable": frequency_deviation <= self.frequency_tolerance,
            "phase_stable": phase_deviation <= self.phase_angle_tolerance,
            "voltage_deviation_percent": round(voltage_deviation, 2),
            "frequency_deviation_hz": round(frequency_deviation, 3),
            "phase_deviation_deg": round(phase_deviation, 2)
        }
        
    def calculate_power_dispatch(self, state: Dict[str, Any], 
                                  constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal power dispatch based on current strategy."""
        pv_power = state.get("pv_power", 0)
        wind_power = state.get("wind_power", 0)
        total_generation = pv_power + wind_power
        load_power = state.get("load_power", 0)
        battery_soc = state.get("battery_soc", 0.5)
        grid_voltage = state.get("grid_voltage", 380)
        grid_frequency = state.get("grid_frequency", 50)
        phase_angle = state.get("phase_angle", 0)
        
        # Use MPC for optimal dispatch
        mpc_result = self.mpc.optimize(state, constraints)
        
        # Apply strategy-specific adjustments
        battery_power = mpc_result["battery_power"]
        grid_power = mpc_result["grid_power"]
        
        # Calculate stability corrections
        voltage_correction = self.pid_voltage.compute(grid_voltage)
        frequency_correction = self.pid_frequency.compute(grid_frequency)
        phase_correction = self.pid_phase_angle.compute(phase_angle)
        
        # Check current stability status
        stability = self.check_stability(state)
        
        if self.active_strategy == "economic":
            # Adjust based on electricity prices
            peak_hours = self.strategy_params.get("peak_hours", [10, 11, 12, 13, 14, 15, 18, 19, 20, 21])
            current_hour = state.get("hour", 12)
            
            if current_hour in peak_hours:
                # During peak hours, prefer battery discharge and minimize grid import
                if grid_power > 0 and battery_soc > 0.3:
                    additional_discharge = min(grid_power, constraints.get("max_discharge_rate", 200) - battery_power)
                    battery_power += additional_discharge
                    grid_power -= additional_discharge
            else:
                # During off-peak, charge battery from grid if cheap
                if battery_soc < 0.8 and grid_power < constraints.get("max_grid_import", 800) * 0.5:
                    charge_power = min(
                        constraints.get("max_charge_rate", 200),
                        (0.8 - battery_soc) * constraints.get("battery_capacity", 1000)
                    )
                    battery_power -= charge_power
                    grid_power += charge_power
                    
        elif self.active_strategy == "green":
            # Maximize renewable usage
            grid_import_limit = self.strategy_params.get("grid_import_limit", 0.2)
            max_grid = constraints.get("max_grid_import", 800) * grid_import_limit
            
            if grid_power > max_grid:
                # Reduce grid import by discharging battery or shedding load
                deficit = grid_power - max_grid
                if battery_soc > 0.2:
                    additional_discharge = min(deficit, constraints.get("max_discharge_rate", 200) - battery_power)
                    battery_power += additional_discharge
                    grid_power -= additional_discharge
                    
        elif self.active_strategy == "stability":
            # Prioritize voltage, frequency, and phase angle stability
            
            # Combined stability adjustment using all three PID controllers
            # Weight: voltage (40%), frequency (40%), phase angle (20%)
            stability_adjustment = (
                0.4 * voltage_correction + 
                0.4 * frequency_correction + 
                0.2 * phase_correction
            )
            
            # Apply stability adjustment to battery power
            battery_power += stability_adjustment
            
            # Phase angle correction: adjust reactive power through battery inverter
            # Large phase deviations require faster response
            if not stability.get("phase_stable", True):
                # Increase battery response for phase correction
                phase_boost = phase_correction * 0.5
                battery_power += phase_boost
                logger.info(f"Phase angle correction applied: {phase_boost:.2f} kW")
            
            # Ensure battery reserve for stability
            battery_reserve = self.strategy_params.get("battery_reserve", 0.3)
            if battery_soc < battery_reserve and battery_power > 0:
                battery_power = 0  # Stop discharge to maintain reserve
                
            # Log stability status
            if not stability.get("voltage_stable", True):
                logger.warning(f"Voltage deviation: {stability['voltage_deviation_percent']:.2f}%")
            if not stability.get("frequency_stable", True):
                logger.warning(f"Frequency deviation: {stability['frequency_deviation_hz']:.3f} Hz")
            if not stability.get("phase_stable", True):
                logger.warning(f"Phase angle deviation: {stability['phase_deviation_deg']:.2f}°")
        
        # Apply stability corrections for all strategies when system is unstable
        if not all([stability.get("voltage_stable", True), 
                    stability.get("frequency_stable", True),
                    stability.get("phase_stable", True)]):
            # Emergency stability correction
            emergency_correction = (voltage_correction + frequency_correction + phase_correction) / 3
            battery_power += emergency_correction * 0.3  # 30% of correction
        
        # Calculate final values
        renewable_ratio = total_generation / load_power if load_power > 0 else 0
        self_sufficiency = (total_generation + max(0, battery_power)) / load_power if load_power > 0 else 0
        
        return {
            "battery_power": round(battery_power, 2),
            "grid_power": round(grid_power, 2),
            "renewable_ratio": round(min(1, renewable_ratio), 4),
            "self_sufficiency": round(min(1, self_sufficiency), 4),
            "strategy": self.active_strategy,
            "stability": stability,
            "corrections": {
                "voltage": round(voltage_correction, 2),
                "frequency": round(frequency_correction, 2),
                "phase_angle": round(phase_correction, 2)
            }
        }
    
    def check_load_shedding(self, state: Dict[str, Any], 
                            loads: List[Dict[str, Any]]) -> List[int]:
        """Determine which loads to shed based on priority."""
        available_power = (
            state.get("pv_power", 0) + 
            state.get("wind_power", 0) + 
            state.get("grid_power", 0) + 
            state.get("battery_power", 0)
        )
        
        total_load = sum(load.get("power", 0) for load in loads if load.get("is_on", True))
        
        if available_power >= total_load:
            return []  # No shedding needed
        
        # Sort loads by priority (higher number = lower priority = shed first)
        sorted_loads = sorted(
            [l for l in loads if l.get("is_controllable", False) and l.get("is_on", True)],
            key=lambda x: (-x.get("priority", 3), -x.get("power", 0))
        )
        
        loads_to_shed = []
        power_to_shed = total_load - available_power
        
        for load in sorted_loads:
            if power_to_shed <= 0:
                break
            loads_to_shed.append(load.get("load_id"))
            power_to_shed -= load.get("power", 0)
        
        return loads_to_shed
