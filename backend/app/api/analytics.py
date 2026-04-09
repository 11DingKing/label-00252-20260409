"""Analytics and reporting API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Optional

from app.db.session import get_db
from app.models.user import User
from app.models.alarm import AlarmHistory
from app.models.analytics import SystemSnapshot, EnergyAggregation
from app.schemas.analytics import (
    SystemSummary, EnergyStatistics, EfficiencyAnalysis, 
    TrendData, TrendDataPoint, HistoricalReport
)
from app.schemas.common import ResponseModel
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.api.deps import get_engine

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
logger = get_logger(__name__)


@router.get("/summary", response_model=ResponseModel[SystemSummary])
async def get_system_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current system summary."""
    engine = get_engine()
    state = engine.get_current_state()
    summary = state.get("summary", {})
    
    active_alarms = db.query(AlarmHistory).filter(
        AlarmHistory.status.in_(["triggered", "acknowledged"])
    ).count()
    
    return ResponseModel(data=SystemSummary(
        total_generation=summary.get("total_generation", 0),
        total_load=summary.get("total_load", 0),
        grid_power=summary.get("grid_power", 0),
        battery_power=summary.get("battery_power", 0),
        battery_soc=summary.get("battery_soc", 0.5),
        pv_power=summary.get("pv_power", 0),
        wind_power=summary.get("wind_power", 0),
        grid_voltage=summary.get("grid_voltage", 380),
        grid_frequency=summary.get("grid_frequency", 50),
        renewable_ratio=summary.get("renewable_ratio", 0),
        self_sufficiency=summary.get("self_sufficiency", 0),
        active_alarms=active_alarms,
        grid_mode=summary.get("grid_mode", "grid_connected")
    ))


@router.get("/energy", response_model=ResponseModel[EnergyStatistics])
async def get_energy_statistics(
    period: str = Query("day", pattern="^(hour|day|week|month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get energy statistics from database for specified period."""
    now = datetime.now()
    
    if period == "hour":
        start_time = now - timedelta(hours=1)
        return await _get_energy_from_snapshots(start_time, now, period, db)
    elif period == "day":
        start_time = now - timedelta(days=1)
        return await _get_energy_from_aggregations("hour", start_time, now, period, db)
    elif period == "week":
        start_time = now - timedelta(weeks=1)
        return await _get_energy_from_aggregations("day", start_time, now, period, db)
    else:
        start_time = now - timedelta(days=30)
        return await _get_energy_from_aggregations("day", start_time, now, period, db)


async def _get_energy_from_snapshots(
    start_time: datetime, end_time: datetime, period: str, db: Session
) -> ResponseModel[EnergyStatistics]:
    """Calculate energy statistics from raw snapshots."""
    snapshots = db.query(SystemSnapshot).filter(
        SystemSnapshot.timestamp >= start_time,
        SystemSnapshot.timestamp <= end_time
    ).order_by(SystemSnapshot.timestamp).all()
    
    if not snapshots:
        engine = get_engine()
        history = engine.get_state_history(3600)
        return _calculate_from_memory(history, start_time, end_time, period)
    
    interval_hours = 1 / 60
    pv_total = sum(s.pv_power for s in snapshots) * interval_hours
    wind_total = sum(s.wind_power for s in snapshots) * interval_hours
    load_total = sum(s.total_load for s in snapshots) * interval_hours
    grid_import = sum(s.grid_power for s in snapshots if s.grid_power > 0) * interval_hours
    grid_export = sum(abs(s.grid_power) for s in snapshots if s.grid_power < 0) * interval_hours
    battery_charge = sum(abs(s.battery_power) for s in snapshots if s.battery_power < 0) * interval_hours
    battery_discharge = sum(s.battery_power for s in snapshots if s.battery_power > 0) * interval_hours
    peak_load = max((s.total_load for s in snapshots), default=0)
    avg_load = sum(s.total_load for s in snapshots) / len(snapshots) if snapshots else 0
    
    return ResponseModel(data=EnergyStatistics(
        period=period, start_time=start_time, end_time=end_time,
        pv_generation=round(pv_total, 2), wind_generation=round(wind_total, 2),
        total_generation=round(pv_total + wind_total, 2), total_consumption=round(load_total, 2),
        grid_import=round(grid_import, 2), grid_export=round(grid_export, 2),
        battery_charge=round(battery_charge, 2), battery_discharge=round(battery_discharge, 2),
        peak_load=round(peak_load, 2), average_load=round(avg_load, 2)
    ))


async def _get_energy_from_aggregations(
    agg_type: str, start_time: datetime, end_time: datetime, period: str, db: Session
) -> ResponseModel[EnergyStatistics]:
    """Calculate energy statistics from pre-computed aggregations."""
    aggregations = db.query(EnergyAggregation).filter(
        EnergyAggregation.period_type == agg_type,
        EnergyAggregation.period_start >= start_time,
        EnergyAggregation.period_start <= end_time
    ).all()
    
    if not aggregations:
        return await _get_energy_from_snapshots(start_time, end_time, period, db)
    
    pv_total = sum(a.pv_generation for a in aggregations)
    wind_total = sum(a.wind_generation for a in aggregations)
    total_gen = sum(a.total_generation for a in aggregations)
    total_cons = sum(a.total_consumption for a in aggregations)
    grid_import = sum(a.grid_import for a in aggregations)
    grid_export = sum(a.grid_export for a in aggregations)
    battery_charge = sum(a.battery_charge for a in aggregations)
    battery_discharge = sum(a.battery_discharge for a in aggregations)
    peak_load = max((a.peak_load for a in aggregations), default=0)
    avg_load = sum(a.avg_load for a in aggregations) / len(aggregations) if aggregations else 0
    
    return ResponseModel(data=EnergyStatistics(
        period=period, start_time=start_time, end_time=end_time,
        pv_generation=round(pv_total, 2), wind_generation=round(wind_total, 2),
        total_generation=round(total_gen, 2), total_consumption=round(total_cons, 2),
        grid_import=round(grid_import, 2), grid_export=round(grid_export, 2),
        battery_charge=round(battery_charge, 2), battery_discharge=round(battery_discharge, 2),
        peak_load=round(peak_load, 2), average_load=round(avg_load, 2)
    ))


def _calculate_from_memory(history: list, start_time: datetime, end_time: datetime, period: str):
    """Fallback calculation from in-memory history."""
    pv_total = wind_total = load_total = 0
    grid_import_total = grid_export_total = 0
    battery_charge_total = battery_discharge_total = 0
    peak_load = load_sum = count = 0
    
    for state in history:
        summary = state.get("summary", {})
        pv_total += summary.get("pv_power", 0) / 3600
        wind_total += summary.get("wind_power", 0) / 3600
        load_power = summary.get("total_load", 0)
        load_total += load_power / 3600
        grid_power = summary.get("grid_power", 0)
        battery_power = summary.get("battery_power", 0)
        
        if grid_power > 0:
            grid_import_total += grid_power / 3600
        else:
            grid_export_total += abs(grid_power) / 3600
        if battery_power > 0:
            battery_discharge_total += battery_power / 3600
        else:
            battery_charge_total += abs(battery_power) / 3600
        
        peak_load = max(peak_load, load_power)
        load_sum += load_power
        count += 1
    
    avg_load = load_sum / count if count > 0 else 0
    return ResponseModel(data=EnergyStatistics(
        period=period, start_time=start_time, end_time=end_time,
        pv_generation=round(pv_total, 2), wind_generation=round(wind_total, 2),
        total_generation=round(pv_total + wind_total, 2), total_consumption=round(load_total, 2),
        grid_import=round(grid_import_total, 2), grid_export=round(grid_export_total, 2),
        battery_charge=round(battery_charge_total, 2), battery_discharge=round(battery_discharge_total, 2),
        peak_load=round(peak_load, 2), average_load=round(avg_load, 2)
    ))


@router.get("/efficiency", response_model=ResponseModel[EfficiencyAnalysis])
async def get_efficiency_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system efficiency analysis from database."""
    start_time = datetime.now() - timedelta(hours=1)
    snapshots = db.query(SystemSnapshot).filter(SystemSnapshot.timestamp >= start_time).all()
    
    engine = get_engine()
    if not snapshots:
        history = engine.get_state_history(60)
        return _calculate_efficiency_from_memory(history, engine)
    
    count = len(snapshots)
    avg_renewable = sum(s.renewable_ratio for s in snapshots) / count
    avg_self_suff = sum(s.self_sufficiency for s in snapshots) / count
    avg_load = sum(s.total_load for s in snapshots) / count
    load_factor = avg_load / 1200 if avg_load > 0 else 0
    
    pv_capacity = sum(sim.capacity_kw for sim in engine.pv_simulators.values()) or 1
    wind_capacity = sum(sim.capacity_kw for sim in engine.wind_simulators.values()) or 1
    avg_pv = sum(s.pv_power for s in snapshots) / count
    avg_wind = sum(s.wind_power for s in snapshots) / count
    
    return ResponseModel(data=EfficiencyAnalysis(
        pv_efficiency=round(avg_pv / pv_capacity, 4),
        wind_efficiency=round(avg_wind / wind_capacity, 4),
        battery_round_trip_efficiency=0.9,
        overall_system_efficiency=round(avg_renewable, 4),
        renewable_utilization=round(avg_renewable, 4),
        load_factor=round(load_factor, 4)
    ))


def _calculate_efficiency_from_memory(history: list, engine):
    """Fallback efficiency calculation from memory."""
    if not history:
        return ResponseModel(data=EfficiencyAnalysis(
            pv_efficiency=0, wind_efficiency=0, battery_round_trip_efficiency=0.9,
            overall_system_efficiency=0, renewable_utilization=0, load_factor=0
        ))
    
    pv_util_sum = wind_util_sum = renewable_ratio_sum = load_factor_sum = 0
    count = len(history)
    
    for state in history:
        for pv in state.get("pv", {}).values():
            pv_util_sum += pv.get("utilization", 0)
        for wind in state.get("wind", {}).values():
            wind_util_sum += wind.get("utilization", 0)
        summary = state.get("summary", {})
        renewable_ratio_sum += summary.get("renewable_ratio", 0)
        load_factor_sum += summary.get("total_load", 0) / 1200
    
    pv_count = count * max(1, len(engine.pv_simulators))
    wind_count = count * max(1, len(engine.wind_simulators))
    
    return ResponseModel(data=EfficiencyAnalysis(
        pv_efficiency=round(pv_util_sum / pv_count, 4) if pv_count > 0 else 0,
        wind_efficiency=round(wind_util_sum / wind_count, 4) if wind_count > 0 else 0,
        battery_round_trip_efficiency=0.9,
        overall_system_efficiency=round(renewable_ratio_sum / count, 4),
        renewable_utilization=round(renewable_ratio_sum / count, 4),
        load_factor=round(load_factor_sum / count, 4)
    ))


@router.get("/trends/{metric}", response_model=ResponseModel[TrendData])
async def get_trend_data(
    metric: str,
    period: str = Query("hour", pattern="^(hour|day|week|month)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trend data for a specific metric with configurable time period."""
    now = datetime.now()
    metric_map = {
        "pv_power": ("pv_power", "kW"), "wind_power": ("wind_power", "kW"),
        "total_generation": ("total_generation", "kW"), "total_load": ("total_load", "kW"),
        "grid_power": ("grid_power", "kW"), "battery_power": ("battery_power", "kW"),
        "battery_soc": ("battery_soc", "%"), "grid_voltage": ("grid_voltage", "V"),
        "grid_frequency": ("grid_frequency", "Hz"), "renewable_ratio": ("renewable_ratio", "%"),
    }
    
    if metric not in metric_map:
        metric = "total_generation"
    field_name, unit = metric_map[metric]
    
    if period == "hour":
        start_time = now - timedelta(hours=1)
        snapshots = db.query(SystemSnapshot).filter(
            SystemSnapshot.timestamp >= start_time
        ).order_by(SystemSnapshot.timestamp).all()
        
        if not snapshots:
            engine = get_engine()
            history = engine.get_state_history(60)
            return _get_trend_from_memory(history, metric, field_name, unit)
        
        data_points = []
        for s in snapshots:
            value = getattr(s, field_name, 0)
            if metric in ["battery_soc", "renewable_ratio"]:
                value = value * 100
            data_points.append(TrendDataPoint(timestamp=s.timestamp, value=round(value, 2)))
    else:
        if period == "day":
            start_time = now - timedelta(days=1)
            agg_type = "hour"
        elif period == "week":
            start_time = now - timedelta(weeks=1)
            agg_type = "day"
        else:
            start_time = now - timedelta(days=30)
            agg_type = "day"
        
        aggregations = db.query(EnergyAggregation).filter(
            EnergyAggregation.period_type == agg_type,
            EnergyAggregation.period_start >= start_time
        ).order_by(EnergyAggregation.period_start).all()
        
        data_points = []
        for a in aggregations:
            if field_name == "total_load":
                value = a.avg_load
            elif field_name == "renewable_ratio":
                value = a.avg_renewable_ratio * 100
            elif field_name in ["pv_power", "wind_power", "total_generation"]:
                value = getattr(a, field_name.replace("_power", "_generation"), 0)
                if agg_type == "day":
                    unit = "kWh"
            else:
                value = a.avg_load
            data_points.append(TrendDataPoint(timestamp=a.period_start, value=round(value, 2)))
    
    return ResponseModel(data=TrendData(metric=metric, unit=unit, data=data_points))


def _get_trend_from_memory(history: list, metric: str, field_name: str, unit: str):
    """Fallback trend data from memory."""
    data_points = []
    for state in history:
        timestamp_str = state.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        except:
            timestamp = datetime.now()
        value = state.get("summary", {}).get(field_name, 0)
        if metric in ["battery_soc", "renewable_ratio"]:
            value = value * 100
        data_points.append(TrendDataPoint(timestamp=timestamp, value=round(value, 2)))
    return ResponseModel(data=TrendData(metric=metric, unit=unit, data=data_points))


@router.get("/report", response_model=ResponseModel[HistoricalReport])
async def get_historical_report(
    period: str = Query("day", pattern="^(day|week|month)$"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate historical report for a specific period."""
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            report_date = datetime.now()
    else:
        report_date = datetime.now()
    
    if period == "day":
        start_time = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        agg_type = "hour"
    elif period == "week":
        start_time = (report_date - timedelta(days=report_date.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(weeks=1)
        agg_type = "day"
    else:
        start_time = report_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_time.month == 12:
            end_time = start_time.replace(year=start_time.year + 1, month=1)
        else:
            end_time = start_time.replace(month=start_time.month + 1)
        agg_type = "day"
    
    aggregations = db.query(EnergyAggregation).filter(
        EnergyAggregation.period_type == agg_type,
        EnergyAggregation.period_start >= start_time,
        EnergyAggregation.period_start < end_time
    ).order_by(EnergyAggregation.period_start).all()
    
    if not aggregations:
        return ResponseModel(data=HistoricalReport(
            period=period, start_time=start_time, end_time=end_time,
            total_pv_generation=0, total_wind_generation=0, total_generation=0,
            total_consumption=0, total_grid_import=0, total_grid_export=0,
            net_grid_energy=0, peak_load=0, average_load=0,
            average_renewable_ratio=0, average_self_sufficiency=0, data_points=0
        ))
    
    total_pv = sum(a.pv_generation for a in aggregations)
    total_wind = sum(a.wind_generation for a in aggregations)
    total_gen = sum(a.total_generation for a in aggregations)
    total_cons = sum(a.total_consumption for a in aggregations)
    total_import = sum(a.grid_import for a in aggregations)
    total_export = sum(a.grid_export for a in aggregations)
    peak_load = max(a.peak_load for a in aggregations)
    avg_load = sum(a.avg_load for a in aggregations) / len(aggregations)
    avg_renewable = sum(a.avg_renewable_ratio for a in aggregations) / len(aggregations)
    avg_self_suff = sum(a.avg_self_sufficiency for a in aggregations) / len(aggregations)
    
    return ResponseModel(data=HistoricalReport(
        period=period, start_time=start_time, end_time=end_time,
        total_pv_generation=round(total_pv, 2), total_wind_generation=round(total_wind, 2),
        total_generation=round(total_gen, 2), total_consumption=round(total_cons, 2),
        total_grid_import=round(total_import, 2), total_grid_export=round(total_export, 2),
        net_grid_energy=round(total_import - total_export, 2),
        peak_load=round(peak_load, 2), average_load=round(avg_load, 2),
        average_renewable_ratio=round(avg_renewable, 4),
        average_self_sufficiency=round(avg_self_suff, 4),
        data_points=len(aggregations)
    ))
