"""Data persistence service for storing simulation data to database."""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import SessionLocal
from app.models.pv import PVData
from app.models.wind import WindData
from app.models.battery import BatteryData
from app.models.load import LoadData
from app.models.grid import GridData
from app.models.analytics import SystemSnapshot, EnergyAggregation
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataPersistenceService:
    """
    Service for persisting simulation data to database.
    
    Features:
    - Batch inserts for efficiency
    - Configurable persistence interval
    - Automatic aggregation computation
    """
    
    def __init__(self, persist_interval: int = 60):
        """
        Initialize persistence service.
        
        Args:
            persist_interval: Seconds between database writes (default 60s = 1 minute)
        """
        self.persist_interval = persist_interval
        self.last_persist_time: Optional[datetime] = None
        self.pending_snapshots: list = []
        self.running = False
    
    def should_persist(self, timestamp: datetime) -> bool:
        """Check if it's time to persist data."""
        if self.last_persist_time is None:
            return True
        return (timestamp - self.last_persist_time).total_seconds() >= self.persist_interval
    
    def add_snapshot(self, state: Dict[str, Any]) -> None:
        """Add a state snapshot to pending list."""
        self.pending_snapshots.append(state)
    
    def persist_snapshot(self, state: Dict[str, Any], db: Session) -> None:
        """Persist a single system snapshot to database."""
        try:
            timestamp_str = state.get("timestamp")
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = datetime.now()
            
            summary = state.get("summary", {})
            
            snapshot = SystemSnapshot(
                timestamp=timestamp,
                pv_power=summary.get("pv_power", 0),
                wind_power=summary.get("wind_power", 0),
                total_generation=summary.get("total_generation", 0),
                total_load=summary.get("total_load", 0),
                battery_power=summary.get("battery_power", 0),
                battery_soc=summary.get("battery_soc", 0.5),
                grid_power=summary.get("grid_power", 0),
                grid_voltage=summary.get("grid_voltage", 380),
                grid_frequency=summary.get("grid_frequency", 50),
                grid_mode=summary.get("grid_mode", "grid_connected"),
                renewable_ratio=summary.get("renewable_ratio", 0),
                self_sufficiency=summary.get("self_sufficiency", 0),
                strategy=summary.get("strategy", "economic")
            )
            db.add(snapshot)
            
            # Persist detailed component data
            self._persist_component_data(state, timestamp, db)
            
            db.commit()
            self.last_persist_time = timestamp
            
        except Exception as e:
            logger.error(f"Failed to persist snapshot: {e}")
            db.rollback()
    
    def _persist_component_data(self, state: Dict[str, Any], timestamp: datetime, db: Session) -> None:
        """Persist detailed component data."""
        # PV data
        pv_data = state.get("pv", {})
        for pv_id, data in pv_data.items():
            db.add(PVData(
                pv_id=int(pv_id),
                irradiance=data.get("irradiance", 0),
                temperature=data.get("temperature", 25),
                power_output=data.get("power_output", 0),
                voltage=data.get("voltage", 0),
                current=data.get("current", 0),
                timestamp=timestamp
            ))
        
        # Wind data
        wind_data = state.get("wind", {})
        for wind_id, data in wind_data.items():
            db.add(WindData(
                wind_id=int(wind_id),
                wind_speed=data.get("wind_speed", 0),
                wind_direction=data.get("wind_direction", 0),
                power_output=data.get("power_output", 0),
                rotor_speed=data.get("rotor_speed", 0),
                timestamp=timestamp
            ))
        
        # Battery data
        battery_data = state.get("battery", {})
        for battery_id, data in battery_data.items():
            db.add(BatteryData(
                battery_id=int(battery_id),
                soc=data.get("soc", 0.5),
                power=data.get("power", 0),
                voltage=data.get("voltage", 0),
                current=data.get("current", 0),
                temperature=data.get("temperature", 25),
                status=data.get("status", "idle"),
                timestamp=timestamp
            ))
        
        # Load data
        load_data = state.get("load", {})
        for load_id, data in load_data.items():
            db.add(LoadData(
                load_id=int(load_id),
                power=data.get("power", 0),
                voltage=data.get("voltage", 380),
                current=data.get("current", 0),
                power_factor=data.get("power_factor", 0.95),
                is_on=data.get("is_on", True),
                timestamp=timestamp
            ))
        
        # Grid data
        grid_data = state.get("grid", {})
        if grid_data:
            db.add(GridData(
                grid_id=1,  # Assuming single grid connection
                power=grid_data.get("power", 0),
                voltage=grid_data.get("voltage", 380),
                frequency=grid_data.get("frequency", 50),
                phase_angle=grid_data.get("phase_angle", 0),
                mode=grid_data.get("mode", "grid_connected"),
                timestamp=timestamp
            ))
    
    def compute_hourly_aggregation(self, hour_start: datetime, db: Session) -> None:
        """Compute and store hourly aggregation."""
        hour_end = hour_start + timedelta(hours=1)
        
        # Query snapshots for this hour
        snapshots = db.query(SystemSnapshot).filter(
            SystemSnapshot.timestamp >= hour_start,
            SystemSnapshot.timestamp < hour_end
        ).all()
        
        if not snapshots:
            return
        
        # Calculate aggregates
        count = len(snapshots)
        interval_hours = self.persist_interval / 3600  # Convert seconds to hours
        
        pv_gen = sum(s.pv_power for s in snapshots) * interval_hours
        wind_gen = sum(s.wind_power for s in snapshots) * interval_hours
        total_gen = sum(s.total_generation for s in snapshots) * interval_hours
        total_cons = sum(s.total_load for s in snapshots) * interval_hours
        
        grid_import = sum(s.grid_power for s in snapshots if s.grid_power > 0) * interval_hours
        grid_export = sum(abs(s.grid_power) for s in snapshots if s.grid_power < 0) * interval_hours
        
        battery_charge = sum(abs(s.battery_power) for s in snapshots if s.battery_power < 0) * interval_hours
        battery_discharge = sum(s.battery_power for s in snapshots if s.battery_power > 0) * interval_hours
        
        peak_gen = max(s.total_generation for s in snapshots)
        peak_load = max(s.total_load for s in snapshots)
        peak_import = max(s.grid_power for s in snapshots) if any(s.grid_power > 0 for s in snapshots) else 0
        
        avg_load = sum(s.total_load for s in snapshots) / count
        avg_renewable = sum(s.renewable_ratio for s in snapshots) / count
        avg_self_suff = sum(s.self_sufficiency for s in snapshots) / count
        
        # Check if aggregation already exists
        existing = db.query(EnergyAggregation).filter(
            EnergyAggregation.period_type == "hour",
            EnergyAggregation.period_start == hour_start
        ).first()
        
        if existing:
            # Update existing
            existing.pv_generation = pv_gen
            existing.wind_generation = wind_gen
            existing.total_generation = total_gen
            existing.total_consumption = total_cons
            existing.grid_import = grid_import
            existing.grid_export = grid_export
            existing.battery_charge = battery_charge
            existing.battery_discharge = battery_discharge
            existing.peak_generation = peak_gen
            existing.peak_load = peak_load
            existing.peak_grid_import = peak_import
            existing.avg_load = avg_load
            existing.avg_renewable_ratio = avg_renewable
            existing.avg_self_sufficiency = avg_self_suff
        else:
            # Create new
            aggregation = EnergyAggregation(
                period_type="hour",
                period_start=hour_start,
                period_end=hour_end,
                pv_generation=pv_gen,
                wind_generation=wind_gen,
                total_generation=total_gen,
                total_consumption=total_cons,
                grid_import=grid_import,
                grid_export=grid_export,
                battery_charge=battery_charge,
                battery_discharge=battery_discharge,
                peak_generation=peak_gen,
                peak_load=peak_load,
                peak_grid_import=peak_import,
                avg_load=avg_load,
                avg_renewable_ratio=avg_renewable,
                avg_self_sufficiency=avg_self_suff
            )
            db.add(aggregation)
        
        db.commit()
        logger.info(f"Computed hourly aggregation for {hour_start}")
    
    def compute_daily_aggregation(self, day_start: datetime, db: Session) -> None:
        """Compute and store daily aggregation from hourly data."""
        day_end = day_start + timedelta(days=1)
        
        # Query hourly aggregations for this day
        hourly = db.query(EnergyAggregation).filter(
            EnergyAggregation.period_type == "hour",
            EnergyAggregation.period_start >= day_start,
            EnergyAggregation.period_start < day_end
        ).all()
        
        if not hourly:
            return
        
        count = len(hourly)
        
        # Sum energy values
        pv_gen = sum(h.pv_generation for h in hourly)
        wind_gen = sum(h.wind_generation for h in hourly)
        total_gen = sum(h.total_generation for h in hourly)
        total_cons = sum(h.total_consumption for h in hourly)
        grid_import = sum(h.grid_import for h in hourly)
        grid_export = sum(h.grid_export for h in hourly)
        battery_charge = sum(h.battery_charge for h in hourly)
        battery_discharge = sum(h.battery_discharge for h in hourly)
        
        # Peak values
        peak_gen = max(h.peak_generation for h in hourly)
        peak_load = max(h.peak_load for h in hourly)
        peak_import = max(h.peak_grid_import for h in hourly)
        
        # Averages
        avg_load = sum(h.avg_load for h in hourly) / count
        avg_renewable = sum(h.avg_renewable_ratio for h in hourly) / count
        avg_self_suff = sum(h.avg_self_sufficiency for h in hourly) / count
        
        # Check if exists
        existing = db.query(EnergyAggregation).filter(
            EnergyAggregation.period_type == "day",
            EnergyAggregation.period_start == day_start
        ).first()
        
        if existing:
            existing.pv_generation = pv_gen
            existing.wind_generation = wind_gen
            existing.total_generation = total_gen
            existing.total_consumption = total_cons
            existing.grid_import = grid_import
            existing.grid_export = grid_export
            existing.battery_charge = battery_charge
            existing.battery_discharge = battery_discharge
            existing.peak_generation = peak_gen
            existing.peak_load = peak_load
            existing.peak_grid_import = peak_import
            existing.avg_load = avg_load
            existing.avg_renewable_ratio = avg_renewable
            existing.avg_self_sufficiency = avg_self_suff
        else:
            aggregation = EnergyAggregation(
                period_type="day",
                period_start=day_start,
                period_end=day_end,
                pv_generation=pv_gen,
                wind_generation=wind_gen,
                total_generation=total_gen,
                total_consumption=total_cons,
                grid_import=grid_import,
                grid_export=grid_export,
                battery_charge=battery_charge,
                battery_discharge=battery_discharge,
                peak_generation=peak_gen,
                peak_load=peak_load,
                peak_grid_import=peak_import,
                avg_load=avg_load,
                avg_renewable_ratio=avg_renewable,
                avg_self_sufficiency=avg_self_suff
            )
            db.add(aggregation)
        
        db.commit()
        logger.info(f"Computed daily aggregation for {day_start.date()}")


# Global instance
persistence_service = DataPersistenceService(persist_interval=60)
