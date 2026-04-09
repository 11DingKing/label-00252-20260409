"""Battery system API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.models.battery import BatterySystem, BatteryData
from app.models.user import User, OperationLog
from app.schemas.battery import (
    BatterySystemCreate, BatterySystemUpdate, BatterySystemResponse, 
    BatteryDataResponse, BatteryRealtimeData, BatteryControlRequest
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.api.deps import get_client_ip, get_engine

router = APIRouter(prefix="/api/battery", tags=["Battery System"])
logger = get_logger(__name__)


@router.get("/systems", response_model=ResponseModel[List[BatterySystemResponse]])
async def get_battery_systems(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all battery systems."""
    systems = db.query(BatterySystem).all()
    return ResponseModel(data=[BatterySystemResponse.model_validate(s) for s in systems])


@router.post("/systems", response_model=ResponseModel[BatterySystemResponse])
async def create_battery_system(
    request: Request,
    system_data: BatterySystemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new battery system."""
    system = BatterySystem(**system_data.model_dump())
    db.add(system)
    
    log = OperationLog(
        user_id=current_user.id,
        action="create",
        module="battery",
        detail=f"Created battery system: {system_data.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(system)
    
    logger.info(f"Battery system {system_data.name} created by {current_user.username}")
    
    return ResponseModel(data=BatterySystemResponse.model_validate(system))


@router.get("/systems/{system_id}", response_model=ResponseModel[BatterySystemResponse])
async def get_battery_system(
    system_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get battery system by ID."""
    system = db.query(BatterySystem).filter(BatterySystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="Battery system not found")
    
    return ResponseModel(data=BatterySystemResponse.model_validate(system))


@router.put("/systems/{system_id}", response_model=ResponseModel[BatterySystemResponse])
async def update_battery_system(
    request: Request,
    system_id: int,
    system_data: BatterySystemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update battery system configuration."""
    system = db.query(BatterySystem).filter(BatterySystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="Battery system not found")
    
    update_data = system_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(system, key, value)
    
    log = OperationLog(
        user_id=current_user.id,
        action="update",
        module="battery",
        detail=f"Updated battery system: {system.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(system)
    
    # Update simulation engine with new SOC limits if they were changed
    if 'min_soc' in update_data or 'max_soc' in update_data:
        engine = get_engine()
        engine.update_battery_soc_limits(system_id, system.min_soc, system.max_soc)
    
    logger.info(f"Battery system {system.name} updated by {current_user.username}")
    
    return ResponseModel(data=BatterySystemResponse.model_validate(system))


@router.post("/systems/{system_id}/charge", response_model=ResponseModel)
async def set_battery_charge(
    request: Request,
    system_id: int,
    control: BatteryControlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set battery charging power (negative power value)."""
    system = db.query(BatterySystem).filter(BatterySystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="Battery system not found")
    
    engine = get_engine()
    # Charging is negative power
    power = -abs(control.power)
    success = engine.set_battery_power(system_id, power)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set battery power")
    
    log = OperationLog(
        user_id=current_user.id,
        action="control",
        module="battery",
        detail=f"Set battery {system.name} to charge at {abs(power)} kW",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Battery {system.name} set to charge at {abs(power)} kW by {current_user.username}")
    
    return ResponseModel(message=f"Battery charging at {abs(power)} kW")


@router.post("/systems/{system_id}/discharge", response_model=ResponseModel)
async def set_battery_discharge(
    request: Request,
    system_id: int,
    control: BatteryControlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set battery discharging power (positive power value)."""
    system = db.query(BatterySystem).filter(BatterySystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="Battery system not found")
    
    engine = get_engine()
    # Discharging is positive power
    power = abs(control.power)
    success = engine.set_battery_power(system_id, power)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set battery power")
    
    log = OperationLog(
        user_id=current_user.id,
        action="control",
        module="battery",
        detail=f"Set battery {system.name} to discharge at {power} kW",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Battery {system.name} set to discharge at {power} kW by {current_user.username}")
    
    return ResponseModel(message=f"Battery discharging at {power} kW")


@router.post("/systems/{system_id}/auto", response_model=ResponseModel)
async def set_battery_auto(
    request: Request,
    system_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set battery back to auto dispatch mode."""
    system = db.query(BatterySystem).filter(BatterySystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="Battery system not found")
    
    engine = get_engine()
    success = engine.set_battery_auto(system_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set battery to auto mode")
    
    log = OperationLog(
        user_id=current_user.id,
        action="control",
        module="battery",
        detail=f"Set battery {system.name} to auto dispatch mode",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Battery {system.name} set to auto mode by {current_user.username}")
    
    return ResponseModel(message=f"Battery {system.name} set to auto dispatch mode")


@router.get("/systems/{system_id}/data", response_model=PaginatedResponse[BatteryDataResponse])
async def get_battery_data(
    system_id: int,
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get battery system historical data."""
    query = db.query(BatteryData).filter(BatteryData.battery_id == system_id)
    
    if start_time:
        query = query.filter(BatteryData.timestamp >= start_time)
    if end_time:
        query = query.filter(BatteryData.timestamp <= end_time)
    
    total = query.count()
    data = query.order_by(BatteryData.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        data=[BatteryDataResponse.model_validate(d) for d in data],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/realtime", response_model=ResponseModel[List[BatteryRealtimeData]])
async def get_battery_realtime(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time battery data from simulation."""
    engine = get_engine()
    state = engine.get_current_state()
    
    systems = db.query(BatterySystem).filter(BatterySystem.is_active == True).all()
    result = []
    
    for system in systems:
        battery_data = state.get("battery", {}).get(system.id, {})
        soc = battery_data.get("soc", 0.5)
        result.append(BatteryRealtimeData(
            battery_id=system.id,
            name=system.name,
            soc=soc,
            power=battery_data.get("power", 0),
            voltage=battery_data.get("voltage", 400),
            current=battery_data.get("current", 0),
            temperature=battery_data.get("temperature", 25),
            status=battery_data.get("status", "idle"),
            capacity_kwh=system.capacity_kwh,
            available_energy=round(soc * system.capacity_kwh, 2)
        ))
    
    return ResponseModel(data=result)
