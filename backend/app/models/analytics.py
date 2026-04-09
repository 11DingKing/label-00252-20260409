"""Analytics and aggregated data models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func
from app.db.base import Base


class SystemSnapshot(Base):
    """
    System snapshot for historical data storage.
    Stores aggregated system state at regular intervals (every minute).
    """
    __tablename__ = "system_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Generation
    pv_power = Column(Float, default=0, nullable=False)  # kW
    wind_power = Column(Float, default=0, nullable=False)  # kW
    total_generation = Column(Float, default=0, nullable=False)  # kW
    
    # Consumption
    total_load = Column(Float, default=0, nullable=False)  # kW
    
    # Battery
    battery_power = Column(Float, default=0, nullable=False)  # kW (positive=discharge)
    battery_soc = Column(Float, default=0.5, nullable=False)  # 0-1
    
    # Grid
    grid_power = Column(Float, default=0, nullable=False)  # kW (positive=import)
    grid_voltage = Column(Float, default=380, nullable=False)  # V
    grid_frequency = Column(Float, default=50, nullable=False)  # Hz
    grid_mode = Column(String(20), default="grid_connected", nullable=False)
    
    # Efficiency metrics
    renewable_ratio = Column(Float, default=0, nullable=False)  # 0-1
    self_sufficiency = Column(Float, default=0, nullable=False)  # 0-1
    
    # Strategy
    strategy = Column(String(50), default="economic", nullable=False)
    
    __table_args__ = (
        Index('idx_snapshot_timestamp', 'timestamp'),
    )


class EnergyAggregation(Base):
    """
    Aggregated energy data for reporting.
    Pre-computed hourly/daily/monthly statistics for fast queries.
    """
    __tablename__ = "energy_aggregations"
    
    id = Column(Integer, primary_key=True, index=True)
    period_type = Column(String(10), nullable=False)  # hour, day, week, month
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Energy totals (kWh)
    pv_generation = Column(Float, default=0, nullable=False)
    wind_generation = Column(Float, default=0, nullable=False)
    total_generation = Column(Float, default=0, nullable=False)
    total_consumption = Column(Float, default=0, nullable=False)
    grid_import = Column(Float, default=0, nullable=False)
    grid_export = Column(Float, default=0, nullable=False)
    battery_charge = Column(Float, default=0, nullable=False)
    battery_discharge = Column(Float, default=0, nullable=False)
    
    # Peak values (kW)
    peak_generation = Column(Float, default=0, nullable=False)
    peak_load = Column(Float, default=0, nullable=False)
    peak_grid_import = Column(Float, default=0, nullable=False)
    
    # Averages
    avg_load = Column(Float, default=0, nullable=False)
    avg_renewable_ratio = Column(Float, default=0, nullable=False)
    avg_self_sufficiency = Column(Float, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_aggregation_period', 'period_type', 'period_start'),
    )
