"""Analytics schemas."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class SystemSummary(BaseModel):
    """System summary schema."""
    total_generation: float  # kW
    total_load: float  # kW
    grid_power: float  # kW (positive=import, negative=export)
    battery_power: float  # kW
    battery_soc: float  # 0-1
    pv_power: float  # kW
    wind_power: float  # kW
    grid_voltage: float  # V
    grid_frequency: float  # Hz
    renewable_ratio: float  # 0-1
    self_sufficiency: float  # 0-1
    active_alarms: int
    grid_mode: str


class EnergyStatistics(BaseModel):
    """Energy statistics schema."""
    period: str  # hour, day, week, month
    start_time: datetime
    end_time: datetime
    pv_generation: float  # kWh
    wind_generation: float  # kWh
    total_generation: float  # kWh
    total_consumption: float  # kWh
    grid_import: float  # kWh
    grid_export: float  # kWh
    battery_charge: float  # kWh
    battery_discharge: float  # kWh
    peak_load: float  # kW
    average_load: float  # kW


class EfficiencyAnalysis(BaseModel):
    """Efficiency analysis schema."""
    pv_efficiency: float
    wind_efficiency: float
    battery_round_trip_efficiency: float
    overall_system_efficiency: float
    renewable_utilization: float
    load_factor: float


class TrendDataPoint(BaseModel):
    """Trend data point schema."""
    timestamp: datetime
    value: float


class TrendData(BaseModel):
    """Trend data schema."""
    metric: str
    unit: str
    data: List[TrendDataPoint]


class ReportRequest(BaseModel):
    """Report generation request schema."""
    report_type: str  # daily, weekly, monthly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_charts: bool = True


class ReportResponse(BaseModel):
    """Report response schema."""
    report_id: str
    report_type: str
    generated_at: datetime
    summary: SystemSummary
    energy_stats: EnergyStatistics
    efficiency: EfficiencyAnalysis


class HistoricalReport(BaseModel):
    """Historical report schema for day/week/month reports."""
    period: str  # day, week, month
    start_time: datetime
    end_time: datetime
    total_pv_generation: float  # kWh
    total_wind_generation: float  # kWh
    total_generation: float  # kWh
    total_consumption: float  # kWh
    total_grid_import: float  # kWh
    total_grid_export: float  # kWh
    net_grid_energy: float  # kWh (import - export)
    peak_load: float  # kW
    average_load: float  # kW
    average_renewable_ratio: float  # 0-1
    average_self_sufficiency: float  # 0-1
    data_points: int  # Number of data points used
