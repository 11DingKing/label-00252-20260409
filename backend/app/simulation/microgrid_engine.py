"""Microgrid simulation engine."""
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session

from app.simulation.pv_simulator import PVSimulator
from app.simulation.wind_simulator import WindSimulator
from app.simulation.battery_simulator import BatterySimulator
from app.simulation.load_simulator import LoadSimulator
from app.simulation.grid_simulator import GridSimulator
from app.simulation.control_algorithms import EnergyManagementSystem
from app.core.logging import get_logger

logger = get_logger(__name__)


class MicrogridEngine:
    """
    Main simulation engine for the microgrid system.
    
    This engine runs independently of WebSocket connections and maintains
    the simulation state. It is designed to be thread-safe and supports
    concurrent access from multiple clients.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.pv_simulators: Dict[int, PVSimulator] = {}
        self.wind_simulators: Dict[int, WindSimulator] = {}
        self.battery_simulators: Dict[int, BatterySimulator] = {}
        self.load_simulators: Dict[int, LoadSimulator] = {}
        self.grid_simulator: Optional[GridSimulator] = None
        self.ems = EnergyManagementSystem()
        
        self.running = False
        self.simulation_speed = 1.0
        self.last_update = datetime.now()
        
        # Current state cache with thread-safe access
        self._state_lock = threading.RLock()
        self.current_state: Dict[str, Any] = {}
        self.state_history: List[Dict[str, Any]] = []
        self.max_history = 3600  # Keep 1 hour of data at 1s intervals
        
        # Simulation statistics
        self.simulation_step_count = 0
        self.simulation_start_time: Optional[datetime] = None
        
        # Callbacks for real-time updates
        self.update_callbacks: List[Callable] = []
        self.alarm_callbacks: List[Callable] = []
        
        # Manual control mode for batteries
        self.battery_manual_mode: Dict[int, bool] = {}
        self.battery_manual_power: Dict[int, float] = {}
        
        # Load shedding state
        self.load_shedding_enabled = True
        self.shed_loads: List[int] = []  # Currently shed load IDs
        
        # Pending alarms to be written to database
        self.pending_alarms: List[Dict[str, Any]] = []
        
        # Load history for MPC prediction
        self.load_history: List[Dict[str, float]] = []
        self.max_load_history = 300  # 5 minutes of history
        
        self._initialized = True
        logger.info("MicrogridEngine initialized")
    
    def initialize_from_db(self, db: Session) -> None:
        """Initialize simulators from database configuration."""
        from app.models.pv import PVSystem
        from app.models.wind import WindSystem
        from app.models.battery import BatterySystem
        from app.models.load import Load
        from app.models.grid import GridConnection
        from app.models.strategy import ControlStrategy
        
        with self._state_lock:
            # Initialize PV simulators
            pv_systems = db.query(PVSystem).filter(PVSystem.is_active == True).all()
            for pv in pv_systems:
                self.pv_simulators[pv.id] = PVSimulator(
                    capacity_kw=pv.capacity_kw,
                    efficiency=pv.efficiency,
                    panel_area=pv.panel_area
                )
            logger.info(f"Initialized {len(self.pv_simulators)} PV simulators")
            
            # Initialize Wind simulators
            wind_systems = db.query(WindSystem).filter(WindSystem.is_active == True).all()
            for wind in wind_systems:
                self.wind_simulators[wind.id] = WindSimulator(
                    capacity_kw=wind.capacity_kw,
                    cut_in_speed=wind.cut_in_speed,
                    rated_speed=wind.rated_speed,
                    cut_out_speed=wind.cut_out_speed
                )
            logger.info(f"Initialized {len(self.wind_simulators)} Wind simulators")
            
            # Initialize Battery simulators
            battery_systems = db.query(BatterySystem).filter(BatterySystem.is_active == True).all()
            for battery in battery_systems:
                self.battery_simulators[battery.id] = BatterySimulator(
                    capacity_kwh=battery.capacity_kwh,
                    max_charge_rate=battery.max_charge_rate,
                    max_discharge_rate=battery.max_discharge_rate,
                    charge_efficiency=battery.charge_efficiency,
                    discharge_efficiency=battery.discharge_efficiency,
                    min_soc=battery.min_soc,
                    max_soc=battery.max_soc
                )
            logger.info(f"Initialized {len(self.battery_simulators)} Battery simulators")
            
            # Initialize Load simulators
            loads = db.query(Load).filter(Load.is_active == True).all()
            for load in loads:
                self.load_simulators[load.id] = LoadSimulator(
                    load_id=load.id,
                    name=load.name,
                    load_type=load.load_type,
                    rated_power=load.rated_power,
                    priority=load.priority,
                    is_controllable=load.is_controllable
                )
            logger.info(f"Initialized {len(self.load_simulators)} Load simulators")
            
            # Initialize Grid simulator
            grid = db.query(GridConnection).first()
            if grid:
                self.grid_simulator = GridSimulator(
                    max_import=grid.max_import,
                    max_export=grid.max_export,
                    connection_type=grid.connection_type
                )
                self.grid_simulator.is_connected = grid.is_connected
            logger.info("Initialized Grid simulator")
            
            # Load active strategy
            strategy = db.query(ControlStrategy).filter(
                ControlStrategy.is_default == True,
                ControlStrategy.is_active == True
            ).first()
            if strategy:
                self.ems.set_strategy(strategy.strategy_type, strategy.parameters)
                logger.info(f"Loaded control strategy: {strategy.name}")
            
            # Mark simulation start time
            self.simulation_start_time = datetime.now()
            self.running = True
    
    def add_update_callback(self, callback: Callable) -> None:
        """Add callback for state updates."""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable) -> None:
        """Remove update callback."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def add_alarm_callback(self, callback: Callable) -> None:
        """Add callback for alarm events."""
        self.alarm_callbacks.append(callback)
    
    async def notify_update(self, state: Dict[str, Any]) -> None:
        """Notify all update callbacks."""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(state)
                else:
                    callback(state)
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
    
    async def notify_alarm(self, alarm: Dict[str, Any]) -> None:
        """Notify all alarm callbacks."""
        for callback in self.alarm_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alarm)
                else:
                    callback(alarm)
            except Exception as e:
                logger.error(f"Error in alarm callback: {e}")
    
    def simulate_step(self, timestamp: datetime = None) -> Dict[str, Any]:
        """
        Run one simulation step.
        
        This method is thread-safe and can be called from the background task.
        It updates the current state and broadcasts to connected clients.
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        with self._state_lock:
            # Simulate PV systems
            pv_data = {}
            total_pv_power = 0
            for pv_id, simulator in self.pv_simulators.items():
                data = simulator.simulate(timestamp)
                pv_data[pv_id] = data
                total_pv_power += data["power_output"]
            
            # Simulate Wind systems
            wind_data = {}
            total_wind_power = 0
            for wind_id, simulator in self.wind_simulators.items():
                data = simulator.simulate(timestamp)
                wind_data[wind_id] = data
                total_wind_power += data["power_output"]
            
            # Simulate Loads
            load_data = {}
            total_load_power = 0
            load_list_for_ems = []
            for load_id, simulator in self.load_simulators.items():
                data = simulator.simulate(timestamp)
                load_data[load_id] = data
                if data["is_on"]:
                    total_load_power += data["power"]
                load_list_for_ems.append({
                    "load_id": load_id,
                    "power": data["power"],
                    "is_on": data["is_on"],
                    "priority": data["priority"],
                    "is_controllable": simulator.is_controllable
                })
            
            # Track load history for MPC prediction
            self.load_history.append({
                "timestamp": timestamp,
                "total_load": total_load_power,
                "by_type": {ld["load_type"]: ld["power"] for ld in load_data.values() if ld["is_on"]}
            })
            if len(self.load_history) > self.max_load_history:
                self.load_history.pop(0)
            
            # Calculate optimal dispatch using EMS
            total_generation = total_pv_power + total_wind_power
            
            # Get battery constraints
            battery_capacity = sum(sim.capacity_kwh for sim in self.battery_simulators.values())
            max_charge = sum(sim.max_charge_rate for sim in self.battery_simulators.values())
            max_discharge = sum(sim.max_discharge_rate for sim in self.battery_simulators.values())
            avg_soc = sum(sim.soc for sim in self.battery_simulators.values()) / len(self.battery_simulators) if self.battery_simulators else 0.5
            
            constraints = {
                "battery_capacity": battery_capacity,
                "max_charge_rate": max_charge,
                "max_discharge_rate": max_discharge,
                "max_grid_import": self.grid_simulator.max_import if self.grid_simulator else 800,
                "max_grid_export": self.grid_simulator.max_export if self.grid_simulator else 500
            }
            
            state = {
                "pv_power": total_pv_power,
                "wind_power": total_wind_power,
                "load_power": total_load_power,
                "battery_soc": avg_soc,
                "grid_voltage": self.grid_simulator.voltage if self.grid_simulator else 380,
                "grid_frequency": self.grid_simulator.frequency if self.grid_simulator else 50,
                "phase_angle": self.grid_simulator.phase_angle if self.grid_simulator else 0,
                "hour": timestamp.hour
            }
            
            # Pass load history to EMS for better MPC prediction
            self.ems.mpc.set_load_history(self.load_history)
            
            dispatch = self.ems.calculate_power_dispatch(state, constraints)
            
            # Check stability and generate alarms
            stability = dispatch.get("stability", {})
            self._check_and_generate_alarms(stability, state, timestamp)
            
            # Execute load shedding if needed
            if self.load_shedding_enabled:
                shed_state = {
                    "pv_power": total_pv_power,
                    "wind_power": total_wind_power,
                    "grid_power": dispatch["grid_power"],
                    "battery_power": dispatch["battery_power"]
                }
                loads_to_shed = self.ems.check_load_shedding(shed_state, load_list_for_ems)
                
                # Apply load shedding
                for load_id in loads_to_shed:
                    if load_id not in self.shed_loads:
                        self.set_load_state(load_id, False)
                        self.shed_loads.append(load_id)
                        logger.info(f"Load shedding: turned off load {load_id}")
                        self._generate_alarm(
                            alarm_code="ALM_LOAD_SHED",
                            alarm_name="负载削减",
                            severity="warning",
                            module="load",
                            message=f"负载 {load_id} 因功率不足被自动切除",
                            timestamp=timestamp
                        )
                
                # Restore shed loads if power is sufficient
                if not loads_to_shed and self.shed_loads:
                    available_power = total_generation + dispatch["grid_power"] + dispatch["battery_power"]
                    current_load = sum(ld["power"] for ld in load_list_for_ems if ld["is_on"])
                    
                    # Try to restore loads in reverse priority order
                    for load_id in list(self.shed_loads):
                        load_sim = self.load_simulators.get(load_id)
                        if load_sim and available_power - current_load > load_sim.rated_power * 0.5:
                            self.set_load_state(load_id, True)
                            self.shed_loads.remove(load_id)
                            current_load += load_sim.rated_power * 0.5
                            logger.info(f"Load restored: turned on load {load_id}")
                
                # Recalculate total load after shedding
                total_load_power = sum(
                    ld["power"] for ld in load_data.values() 
                    if self.load_simulators[ld["load_id"]].is_on
                )
            
            # Distribute battery power among battery systems
            battery_data = {}
            total_battery_power = dispatch["battery_power"]
            for battery_id, simulator in self.battery_simulators.items():
                # Check if battery is in manual mode
                if self.battery_manual_mode.get(battery_id, False):
                    # Use manual power setting
                    power_command = self.battery_manual_power.get(battery_id, 0)
                else:
                    # Proportional distribution based on capacity
                    ratio = simulator.capacity_kwh / battery_capacity if battery_capacity > 0 else 1
                    power_command = total_battery_power * ratio
                data = simulator.simulate(power_command)
                battery_data[battery_id] = data
                
                # Check battery alarms
                if data["soc"] < 0.15:
                    self._generate_alarm(
                        alarm_code="ALM_BAT_LOW",
                        alarm_name="电池电量低",
                        severity="warning",
                        module="battery",
                        message=f"电池 {battery_id} SOC 低于 15%: {data['soc']*100:.1f}%",
                        timestamp=timestamp
                    )
                if data["temperature"] > 45:
                    self._generate_alarm(
                        alarm_code="ALM_BAT_TEMP",
                        alarm_name="电池温度过高",
                        severity="critical",
                        module="battery",
                        message=f"电池 {battery_id} 温度过高: {data['temperature']:.1f}°C",
                        timestamp=timestamp
                    )
            
            # Simulate Grid
            grid_data = {}
            if self.grid_simulator:
                actual_battery_power = sum(d["power"] for d in battery_data.values())
                grid_result = self.grid_simulator.simulate(
                    generation=total_generation,
                    load=total_load_power,
                    battery_power=actual_battery_power
                )
                grid_data = grid_result
            
            # Compile current state
            self.current_state = {
                "timestamp": timestamp.isoformat(),
                "pv": pv_data,
                "wind": wind_data,
                "battery": battery_data,
                "load": load_data,
                "grid": grid_data,
                "summary": {
                    "total_generation": round(total_generation, 2),
                    "pv_power": round(total_pv_power, 2),
                    "wind_power": round(total_wind_power, 2),
                    "total_load": round(total_load_power, 2),
                    "battery_power": round(sum(d["power"] for d in battery_data.values()), 2),
                    "battery_soc": round(avg_soc, 4),
                    "grid_power": round(grid_data.get("power", 0), 2),
                    "grid_voltage": round(grid_data.get("voltage", 380), 2),
                    "grid_frequency": round(grid_data.get("frequency", 50), 4),
                    "grid_mode": grid_data.get("mode", "grid_connected"),
                    "renewable_ratio": dispatch["renewable_ratio"],
                    "self_sufficiency": dispatch["self_sufficiency"],
                    "strategy": dispatch["strategy"],
                    "shed_loads": self.shed_loads.copy()
                }
            }
            
            # Add to history
            self.state_history.append(self.current_state)
            if len(self.state_history) > self.max_history:
                self.state_history.pop(0)
            
            # Update statistics
            self.simulation_step_count += 1
            self.last_update = timestamp
            
            return self.current_state
    
    def _check_and_generate_alarms(self, stability: Dict[str, Any], state: Dict[str, Any], timestamp: datetime) -> None:
        """Check stability status and generate alarms if needed."""
        # Voltage alarm
        if not stability.get("voltage_stable", True):
            deviation = stability.get("voltage_deviation_percent", 0)
            severity = "critical" if deviation > 8 else "warning"
            self._generate_alarm(
                alarm_code="ALM_VOLTAGE",
                alarm_name="电压偏差告警",
                severity=severity,
                module="grid",
                message=f"电网电压偏差 {deviation:.2f}%，当前电压 {state.get('grid_voltage', 380):.1f}V",
                timestamp=timestamp
            )
        
        # Frequency alarm
        if not stability.get("frequency_stable", True):
            deviation = stability.get("frequency_deviation_hz", 0)
            severity = "critical" if deviation > 0.5 else "warning"
            self._generate_alarm(
                alarm_code="ALM_FREQUENCY",
                alarm_name="频率偏差告警",
                severity=severity,
                module="grid",
                message=f"电网频率偏差 {deviation:.3f}Hz，当前频率 {state.get('grid_frequency', 50):.3f}Hz",
                timestamp=timestamp
            )
        
        # Phase angle alarm
        if not stability.get("phase_stable", True):
            deviation = stability.get("phase_deviation_deg", 0)
            self._generate_alarm(
                alarm_code="ALM_PHASE",
                alarm_name="相角偏差告警",
                severity="warning",
                module="grid",
                message=f"相角偏差 {deviation:.2f}°",
                timestamp=timestamp
            )
    
    def _generate_alarm(self, alarm_code: str, alarm_name: str, severity: str, 
                        module: str, message: str, timestamp: datetime) -> None:
        """Generate an alarm and add to pending list."""
        alarm = {
            "alarm_code": alarm_code,
            "alarm_name": alarm_name,
            "severity": severity,
            "module": module,
            "message": message,
            "timestamp": timestamp.isoformat(),
            "status": "triggered"
        }
        self.pending_alarms.append(alarm)
        logger.warning(f"Alarm generated: [{severity.upper()}] {alarm_name} - {message}")
    
    def get_pending_alarms(self) -> List[Dict[str, Any]]:
        """Get and clear pending alarms."""
        alarms = self.pending_alarms.copy()
        self.pending_alarms.clear()
        return alarms
    
    def set_load_shedding_enabled(self, enabled: bool) -> None:
        """Enable or disable automatic load shedding."""
        self.load_shedding_enabled = enabled
        if not enabled:
            # Restore all shed loads
            for load_id in self.shed_loads:
                self.set_load_state(load_id, True)
            self.shed_loads.clear()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current system state (thread-safe)."""
        with self._state_lock:
            return self.current_state.copy() if self.current_state else {}
    
    def get_state_history(self, count: int = 60) -> List[Dict[str, Any]]:
        """Get recent state history (thread-safe)."""
        with self._state_lock:
            return list(self.state_history[-count:])
    
    def get_simulation_stats(self) -> Dict[str, Any]:
        """Get simulation statistics."""
        with self._state_lock:
            return {
                "running": self.running,
                "step_count": self.simulation_step_count,
                "start_time": self.simulation_start_time.isoformat() if self.simulation_start_time else None,
                "last_update": self.last_update.isoformat() if self.last_update else None,
                "history_size": len(self.state_history)
            }
    
    def set_load_state(self, load_id: int, is_on: bool) -> bool:
        """Set load on/off state."""
        if load_id in self.load_simulators:
            self.load_simulators[load_id].set_state(is_on)
            return True
        return False
    
    def set_battery_power(self, battery_id: int, power: float) -> bool:
        """Set battery power command (manual mode)."""
        if battery_id in self.battery_simulators:
            self.battery_simulators[battery_id].set_power(power)
            # Enable manual mode for this battery
            self.battery_manual_mode[battery_id] = True
            self.battery_manual_power[battery_id] = power
            return True
        return False
    
    def set_battery_auto(self, battery_id: int) -> bool:
        """Set battery back to auto mode."""
        if battery_id in self.battery_simulators:
            self.battery_manual_mode[battery_id] = False
            self.battery_manual_power.pop(battery_id, None)
            return True
        return False
    
    def set_grid_mode(self, mode: str) -> bool:
        """Set grid connection mode."""
        if self.grid_simulator:
            return self.grid_simulator.set_mode(mode)
        return False
    
    def set_strategy(self, strategy_type: str, params: Dict[str, Any]) -> None:
        """Set control strategy."""
        self.ems.set_strategy(strategy_type, params)
    
    def update_battery_soc_limits(self, battery_id: int, min_soc: float, max_soc: float) -> bool:
        """Update battery SOC limits dynamically."""
        with self._state_lock:
            if battery_id in self.battery_simulators:
                self.battery_simulators[battery_id].update_soc_limits(min_soc, max_soc)
                logger.info(f"Updated battery {battery_id} SOC limits: min={min_soc}, max={max_soc}")
                return True
            return False


# Global engine instance
engine = MicrogridEngine()
