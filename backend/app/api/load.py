"""Load management API endpoints."""
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.models.load import Load, LoadData
from app.models.config import SystemConfig
from app.models.user import User, OperationLog
from app.schemas.load import (
    LoadCreate, LoadUpdate, LoadResponse, 
    LoadDataResponse, LoadRealtimeData, LoadControlRequest
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.api.deps import get_client_ip, get_engine

router = APIRouter(prefix="/api/loads", tags=["Load Management"])
logger = get_logger(__name__)


@router.get("/realtime", response_model=ResponseModel[List[LoadRealtimeData]])
async def get_loads_realtime(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time load data from simulation."""
    engine = get_engine()
    state = engine.get_current_state()
    
    loads = db.query(Load).filter(Load.is_active == True).all()
    result = []
    
    for load in loads:
        load_data = state.get("load", {}).get(load.id, {})
        
        # Get is_on state from simulator directly if available
        is_on = True
        if load.id in engine.load_simulators:
            is_on = engine.load_simulators[load.id].is_on
        elif load_data:
            is_on = load_data.get("is_on", True)
        
        power = load_data.get("power", 0) if is_on else 0
        
        result.append(LoadRealtimeData(
            load_id=load.id,
            name=load.name,
            load_type=load.load_type,
            power=power,
            voltage=load_data.get("voltage", 380),
            current=load_data.get("current", 0) if is_on else 0,
            power_factor=load_data.get("power_factor", 0.95),
            rated_power=load.rated_power,
            priority=load.priority,
            is_on=is_on,
            is_controllable=load.is_controllable,
            is_active=load.is_active,
            utilization=round(power / load.rated_power, 4) if load.rated_power > 0 else 0
        ))
    
    return ResponseModel(data=result)


# Default load strategy
DEFAULT_LOAD_STRATEGY = {
    "load_shedding": True,
    "power_limit": 1200
}


def get_load_strategy_from_db(db: Session) -> dict:
    """Get load strategy from database."""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == "load_strategy").first()
    if config:
        try:
            return json.loads(config.config_value)
        except json.JSONDecodeError:
            return DEFAULT_LOAD_STRATEGY.copy()
    return DEFAULT_LOAD_STRATEGY.copy()


def save_load_strategy_to_db(db: Session, strategy: dict, user_id: int = None):
    """Save load strategy to database."""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == "load_strategy").first()
    if config:
        config.config_value = json.dumps(strategy)
    else:
        config = SystemConfig(
            config_key="load_strategy",
            config_value=json.dumps(strategy),
            config_type="json",
            description="负载管理策略配置"
        )
        db.add(config)
    db.commit()


@router.get("/strategy", response_model=ResponseModel)
async def get_load_strategy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get load management strategy settings."""
    strategy = get_load_strategy_from_db(db)
    return ResponseModel(data=strategy)


@router.post("/strategy", response_model=ResponseModel)
async def set_load_strategy(
    request: Request,
    strategy: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set load management strategy settings."""
    current_strategy = get_load_strategy_from_db(db)
    
    if "load_shedding" in strategy:
        current_strategy["load_shedding"] = strategy["load_shedding"]
    if "power_limit" in strategy:
        current_strategy["power_limit"] = strategy["power_limit"]
    
    save_load_strategy_to_db(db, current_strategy, current_user.id)
    
    log = OperationLog(
        user_id=current_user.id,
        action="config",
        module="load",
        detail=f"Updated load strategy: shedding={current_strategy['load_shedding']}, limit={current_strategy['power_limit']}kW",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Load strategy updated by {current_user.username}")
    
    return ResponseModel(message="Load strategy updated successfully")


@router.get("", response_model=ResponseModel[List[LoadResponse]])
async def get_loads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all loads."""
    loads = db.query(Load).all()
    return ResponseModel(data=[LoadResponse.model_validate(l) for l in loads])


@router.post("", response_model=ResponseModel[LoadResponse])
async def create_load(
    request: Request,
    load_data: LoadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new load."""
    load = Load(**load_data.model_dump())
    db.add(load)
    
    log = OperationLog(
        user_id=current_user.id,
        action="create",
        module="load",
        detail=f"Created load: {load_data.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(load)
    
    logger.info(f"Load {load_data.name} created by {current_user.username}")
    
    return ResponseModel(data=LoadResponse.model_validate(load))


@router.get("/{load_id}", response_model=ResponseModel[LoadResponse])
async def get_load(
    load_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get load by ID."""
    load = db.query(Load).filter(Load.id == load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    
    return ResponseModel(data=LoadResponse.model_validate(load))


@router.put("/{load_id}", response_model=ResponseModel[LoadResponse])
async def update_load(
    request: Request,
    load_id: int,
    load_data: LoadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update load configuration."""
    load = db.query(Load).filter(Load.id == load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    
    update_data = load_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(load, key, value)
    
    log = OperationLog(
        user_id=current_user.id,
        action="update",
        module="load",
        detail=f"Updated load: {load.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(load)
    
    logger.info(f"Load {load.name} updated by {current_user.username}")
    
    return ResponseModel(data=LoadResponse.model_validate(load))


@router.delete("/{load_id}", response_model=ResponseModel)
async def delete_load(
    request: Request,
    load_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a load."""
    load = db.query(Load).filter(Load.id == load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    
    name = load.name
    db.delete(load)
    
    log = OperationLog(
        user_id=current_user.id,
        action="delete",
        module="load",
        detail=f"Deleted load: {name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Load {name} deleted by {current_user.username}")
    
    return ResponseModel(message="Load deleted successfully")


@router.post("/{load_id}/control", response_model=ResponseModel)
async def control_load(
    request: Request,
    load_id: int,
    control: LoadControlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Control load on/off state."""
    load = db.query(Load).filter(Load.id == load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    
    if not load.is_controllable:
        raise HTTPException(status_code=400, detail="Load is not controllable")
    
    engine = get_engine()
    
    # If load not in simulator, add it dynamically
    if load_id not in engine.load_simulators:
        from app.simulation.load_simulator import LoadSimulator
        engine.load_simulators[load_id] = LoadSimulator(
            load_id=load.id,
            name=load.name,
            load_type=load.load_type,
            rated_power=load.rated_power,
            priority=load.priority,
            is_controllable=load.is_controllable
        )
    
    success = engine.set_load_state(load_id, control.is_on)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to control load")
    
    action = "turned on" if control.is_on else "turned off"
    log = OperationLog(
        user_id=current_user.id,
        action="control",
        module="load",
        detail=f"Load {load.name} {action}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Load {load.name} {action} by {current_user.username}")
    
    return ResponseModel(message=f"Load {action} successfully")


@router.get("/{load_id}/data", response_model=PaginatedResponse[LoadDataResponse])
async def get_load_data(
    load_id: int,
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get load historical data."""
    query = db.query(LoadData).filter(LoadData.load_id == load_id)
    
    if start_time:
        query = query.filter(LoadData.timestamp >= start_time)
    if end_time:
        query = query.filter(LoadData.timestamp <= end_time)
    
    total = query.count()
    data = query.order_by(LoadData.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        data=[LoadDataResponse.model_validate(d) for d in data],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
