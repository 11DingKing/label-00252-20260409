"""Simulation engine tests."""
import pytest
from datetime import datetime
import numpy as np

from app.simulation.pv_simulator import PVSimulator
from app.simulation.wind_simulator import WindSimulator
from app.simulation.battery_simulator import BatterySimulator
from app.simulation.load_simulator import LoadSimulator
from app.simulation.grid_simulator import GridSimulator
from app.simulation.control_algorithms import PIDController, MPCController, EnergyManagementSystem


class TestPVSimulator:
    """Test PV simulator."""
    
    def test_initialization(self):
        """Test PV simulator initialization."""
        pv = PVSimulator(capacity_kw=100.0, efficiency=0.18, panel_area=500.0)
        assert pv.capacity_kw == 100.0
        assert pv.efficiency == 0.18
        assert pv.panel_area == 500.0
    
    def test_irradiance_daytime(self):
        """Test irradiance calculation during daytime."""
        pv = PVSimulator(capacity_kw=100.0, efficiency=0.18, panel_area=500.0)
        irradiance = pv.calculate_irradiance(12.0)  # Noon
        assert irradiance > 0
        assert irradiance <= 1500  # Max reasonable irradiance
    
    def test_irradiance_nighttime(self):
        """Test irradiance calculation during nighttime."""
        pv = PVSimulator(capacity_kw=100.0, efficiency=0.18, panel_area=500.0)
        irradiance_night = pv.calculate_irradiance(2.0)  # 2 AM
        assert irradiance_night == 0
    
    def test_power_output_capped(self):
        """Test that power output is capped at capacity."""
        pv = PVSimulator(capacity_kw=100.0, efficiency=0.18, panel_area=500.0)
        power = pv.calculate_power_output(irradiance=1000.0, temperature=25.0)
        assert power <= pv.capacity_kw
    
    def test_simulate_returns_dict(self):
        """Test that simulate returns expected dictionary."""
        pv = PVSimulator(capacity_kw=100.0, efficiency=0.18, panel_area=500.0)
        result = pv.simulate()
        assert isinstance(result, dict)
        assert "irradiance" in result
        assert "temperature" in result
        assert "power_output" in result
        assert "voltage" in result
        assert "current" in result


class TestWindSimulator:
    """Test wind simulator."""
    
    def test_initialization(self):
        """Test wind simulator initialization."""
        wind = WindSimulator(capacity_kw=50.0, cut_in_speed=3.0, rated_speed=12.0, cut_out_speed=25.0)
        assert wind.capacity_kw == 50.0
        assert wind.cut_in_speed == 3.0
    
    def test_power_below_cut_in(self):
        """Test power output below cut-in speed."""
        wind = WindSimulator(capacity_kw=50.0, cut_in_speed=3.0, rated_speed=12.0, cut_out_speed=25.0)
        power = wind.calculate_power_output(wind_speed=2.0)
        assert power == 0
    
    def test_power_above_cut_out(self):
        """Test power output above cut-out speed."""
        wind = WindSimulator(capacity_kw=50.0, cut_in_speed=3.0, rated_speed=12.0, cut_out_speed=25.0)
        power = wind.calculate_power_output(wind_speed=30.0)
        assert power == 0
    
    def test_power_at_rated_speed(self):
        """Test power output at rated speed."""
        wind = WindSimulator(capacity_kw=50.0, cut_in_speed=3.0, rated_speed=12.0, cut_out_speed=25.0)
        power = wind.calculate_power_output(wind_speed=12.0)
        assert power == wind.capacity_kw


class TestBatterySimulator:
    """Test battery simulator."""
    
    def test_initialization(self):
        """Test battery simulator initialization."""
        battery = BatterySimulator(
            capacity_kwh=500.0,
            max_charge_rate=100.0,
            max_discharge_rate=100.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.1,
            max_soc=0.9
        )
        assert battery.capacity_kwh == 500.0
        assert battery.soc == 0.5  # Default initial SOC
    
    def test_charge(self):
        """Test battery charging."""
        battery = BatterySimulator(
            capacity_kwh=500.0,
            max_charge_rate=100.0,
            max_discharge_rate=100.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.1,
            max_soc=0.9
        )
        initial_soc = battery.soc
        battery.set_power(-50.0)  # Negative = charge
        battery.update_soc(3600)  # 1 hour
        assert battery.soc > initial_soc
    
    def test_discharge(self):
        """Test battery discharging."""
        battery = BatterySimulator(
            capacity_kwh=500.0,
            max_charge_rate=100.0,
            max_discharge_rate=100.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.1,
            max_soc=0.9
        )
        initial_soc = battery.soc
        battery.set_power(50.0)  # Positive = discharge
        battery.update_soc(3600)  # 1 hour
        assert battery.soc < initial_soc
    
    def test_soc_limits(self):
        """Test SOC stays within limits."""
        battery = BatterySimulator(
            capacity_kwh=500.0,
            max_charge_rate=100.0,
            max_discharge_rate=100.0,
            charge_efficiency=0.95,
            discharge_efficiency=0.95,
            min_soc=0.1,
            max_soc=0.9
        )
        # Try to overcharge
        battery.soc = 0.85
        battery.set_power(-100.0)
        battery.update_soc(36000)  # 10 hours
        assert battery.soc <= 0.9
        
        # Try to over-discharge
        battery.soc = 0.15
        battery.set_power(100.0)
        battery.update_soc(36000)  # 10 hours
        assert battery.soc >= 0.1


class TestLoadSimulator:
    """Test load simulator."""
    
    def test_initialization(self):
        """Test load simulator initialization."""
        load = LoadSimulator(
            load_id=1,
            name="Office Load",
            load_type="office",
            rated_power=50.0,
            priority=1,
            is_controllable=True
        )
        assert load is not None
        assert load.name == "Office Load"
    
    def test_simulate_returns_dict(self):
        """Test that simulate returns expected dictionary."""
        load = LoadSimulator(
            load_id=1,
            name="Office Load",
            load_type="office",
            rated_power=50.0,
            priority=1,
            is_controllable=True
        )
        result = load.simulate()
        assert isinstance(result, dict)
        assert "power" in result
        assert "load_type" in result


class TestGridSimulator:
    """Test grid simulator."""
    
    def test_initialization(self):
        """Test grid simulator initialization."""
        grid = GridSimulator(max_import=500.0, max_export=500.0)
        assert grid.max_import == 500.0
        assert grid.max_export == 500.0
        assert grid.phase_angle_tolerance == 5.0  # ±5 degrees
    
    def test_grid_connected_mode(self):
        """Test grid connected mode."""
        grid = GridSimulator(max_import=500.0, max_export=500.0)
        grid.set_mode("grid_connected")
        assert grid.mode == "grid_connected"
    
    def test_grid_islanded_mode(self):
        """Test grid islanded mode."""
        grid = GridSimulator(max_import=500.0, max_export=500.0)
        grid.set_mode("islanded")
        assert grid.mode == "islanded"
    
    def test_phase_stability_check(self):
        """Test phase angle stability check."""
        grid = GridSimulator(max_import=500.0, max_export=500.0)
        grid.phase_angle = 2.0  # Within tolerance
        stability = grid.check_grid_stability()
        assert stability["phase_stable"] is True
        
        grid.phase_angle = 10.0  # Outside tolerance
        stability = grid.check_grid_stability()
        assert stability["phase_stable"] is False
    
    def test_pll_lock_status(self):
        """Test PLL lock status."""
        grid = GridSimulator(max_import=500.0, max_export=500.0)
        grid.phase_angle = 1.0  # Within PLL lock threshold
        grid.simulate_grid_quality(0)
        # PLL should be locked when phase angle is small
        assert grid.pll_lock_threshold == 3.0
    
    def test_phase_correction(self):
        """Test phase angle correction."""
        grid = GridSimulator(max_import=500.0, max_export=500.0)
        grid.phase_angle = 5.0
        grid.apply_phase_correction(4.0)  # Apply correction
        assert grid.phase_angle < 5.0  # Phase should be reduced


class TestPIDController:
    """Test PID controller."""
    
    def test_initialization(self):
        """Test PID controller initialization."""
        pid = PIDController(kp=1.0, ki=0.1, kd=0.01)
        assert pid.kp == 1.0
        assert pid.ki == 0.1
        assert pid.kd == 0.01
    
    def test_compute(self):
        """Test PID compute output."""
        pid = PIDController(kp=1.0, ki=0.1, kd=0.01, setpoint=100.0)
        output = pid.compute(measurement=90.0, dt=0.1)
        assert output != 0  # Should produce some output for error
    
    def test_reset(self):
        """Test PID reset."""
        pid = PIDController(kp=1.0, ki=0.1, kd=0.01, setpoint=100.0)
        pid.compute(measurement=90.0, dt=0.1)
        pid.reset()
        assert pid.integral == 0
        assert pid.previous_error == 0


class TestMPCController:
    """Test MPC controller."""
    
    def test_initialization(self):
        """Test MPC controller initialization."""
        mpc = MPCController(prediction_horizon=10, control_horizon=5)
        assert mpc.prediction_horizon == 10
        assert mpc.control_horizon == 5
    
    def test_optimize(self):
        """Test MPC optimization."""
        mpc = MPCController(prediction_horizon=10, control_horizon=5)
        result = mpc.optimize(
            current_state={
                "pv_power": 50.0,
                "wind_power": 30.0,
                "load_power": 100.0,
                "battery_soc": 0.5
            },
            constraints={
                "battery_capacity": 1000,
                "max_charge_rate": 200,
                "max_discharge_rate": 200,
                "max_grid_import": 800,
                "max_grid_export": 500
            }
        )
        assert isinstance(result, dict)
        assert "battery_power" in result
        assert "grid_power" in result


class TestEnergyManagementSystem:
    """Test energy management system."""
    
    def test_initialization(self):
        """Test EMS initialization."""
        ems = EnergyManagementSystem()
        assert ems is not None
        assert ems.pid_phase_angle is not None  # Phase angle PID controller exists
        assert ems.phase_angle_tolerance == 5.0  # ±5 degrees
    
    def test_check_stability(self):
        """Test stability check including phase angle."""
        ems = EnergyManagementSystem()
        
        # Test stable state
        state = {
            "grid_voltage": 380,
            "grid_frequency": 50,
            "phase_angle": 0
        }
        stability = ems.check_stability(state)
        assert stability["voltage_stable"] is True
        assert stability["frequency_stable"] is True
        assert stability["phase_stable"] is True
        
        # Test unstable phase angle
        state["phase_angle"] = 10  # Outside ±5° tolerance
        stability = ems.check_stability(state)
        assert stability["phase_stable"] is False
    
    def test_calculate_power_dispatch(self):
        """Test power dispatch calculation."""
        ems = EnergyManagementSystem()
        result = ems.calculate_power_dispatch(
            state={
                "pv_power": 50.0,
                "wind_power": 30.0,
                "load_power": 100.0,
                "battery_soc": 0.5,
                "grid_voltage": 380,
                "grid_frequency": 50,
                "phase_angle": 0,
                "hour": 12
            },
            constraints={
                "battery_capacity": 1000,
                "max_charge_rate": 200,
                "max_discharge_rate": 200,
                "max_grid_import": 800,
                "max_grid_export": 500
            }
        )
        assert isinstance(result, dict)
        assert "battery_power" in result
        assert "grid_power" in result
        assert "renewable_ratio" in result
        assert "stability" in result
        assert "corrections" in result
        assert "phase_angle" in result["corrections"]
    
    def test_stability_strategy_with_phase_control(self):
        """Test stability strategy includes phase angle control."""
        ems = EnergyManagementSystem()
        ems.set_strategy("stability", {"battery_reserve": 0.3})
        
        # Test with phase angle deviation
        result = ems.calculate_power_dispatch(
            state={
                "pv_power": 50.0,
                "wind_power": 30.0,
                "load_power": 100.0,
                "battery_soc": 0.5,
                "grid_voltage": 380,
                "grid_frequency": 50,
                "phase_angle": 8.0,  # Outside tolerance
                "hour": 12
            },
            constraints={
                "battery_capacity": 1000,
                "max_charge_rate": 200,
                "max_discharge_rate": 200,
                "max_grid_import": 800,
                "max_grid_export": 500
            }
        )
        # Phase correction should be applied
        assert result["corrections"]["phase_angle"] != 0
