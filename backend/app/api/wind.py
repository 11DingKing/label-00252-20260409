"""Wind system API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.models.wind import WindSystem, WindData
from app.models.user import User, OperationLog
from app.schemas.wind import WindSystemCreate, WindSystemUpdate, WindSystemResponse, WindDataResponse, WindRealtimeData
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.api.deps import get_client_ip, get_engine

router = APIRouter(prefix="/api/wind", tags=["Wind System"])
logger = get_logger(__name__)


@router.get("/systems", response_model=ResponseModel[List[WindSystemResponse]])
async def get_wind_systems(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all wind systems."""
    systems = db.query(WindSystem).all()
    return ResponseModel(data=[WindSystemResponse.model_validate(s) for s in systems])


@router.post("/systems", response_model=ResponseModel[WindSystemResponse])
async def create_wind_system(
    request: Request,
    system_data: WindSystemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new wind system."""
    system = WindSystem(**system_data.model_dump())
    db.add(system)
    
    log = OperationLog(
        user_id=current_user.id,
        action="create",
        module="wind",
        detail=f"Created wind system: {system_data.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(system)
    
    logger.info(f"Wind system {system_data.name} created by {current_user.username}")
    
    return ResponseModel(data=WindSystemResponse.model_validate(system))


@router.get("/systems/{system_id}", response_model=ResponseModel[WindSystemResponse])
async def get_wind_system(
    system_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wind system by ID."""
    system = db.query(WindSystem).filter(WindSystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="Wind system not found")
    
    return ResponseModel(data=WindSystemResponse.model_validate(system))


@router.put("/systems/{system_id}", response_model=ResponseModel[WindSystemResponse])
async def update_wind_system(
    request: Request,
    system_id: int,
    system_data: WindSystemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update wind system configuration."""
    system = db.query(WindSystem).filter(WindSystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="Wind system not found")
    
    update_data = system_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(system, key, value)
    
    log = OperationLog(
        user_id=current_user.id,
        action="update",
        module="wind",
        detail=f"Updated wind system: {system.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(system)
    
    logger.info(f"Wind system {system.name} updated by {current_user.username}")
    
    return ResponseModel(data=WindSystemResponse.model_validate(system))


@router.get("/systems/{system_id}/data", response_model=PaginatedResponse[WindDataResponse])
async def get_wind_data(
    system_id: int,
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wind system historical data."""
    query = db.query(WindData).filter(WindData.wind_id == system_id)
    
    if start_time:
        query = query.filter(WindData.timestamp >= start_time)
    if end_time:
        query = query.filter(WindData.timestamp <= end_time)
    
    total = query.count()
    data = query.order_by(WindData.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        data=[WindDataResponse.model_validate(d) for d in data],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/realtime", response_model=ResponseModel[List[WindRealtimeData]])
async def get_wind_realtime(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time wind data from simulation."""
    engine = get_engine()
    state = engine.get_current_state()
    
    systems = db.query(WindSystem).filter(WindSystem.is_active == True).all()
    result = []
    
    for system in systems:
        wind_data = state.get("wind", {}).get(system.id, {})
        result.append(WindRealtimeData(
            wind_id=system.id,
            name=system.name,
            wind_speed=wind_data.get("wind_speed", 0),
            wind_direction=wind_data.get("wind_direction", 0),
            power_output=wind_data.get("power_output", 0),
            rotor_speed=wind_data.get("rotor_speed", 0),
            capacity_kw=system.capacity_kw,
            utilization=wind_data.get("utilization", 0)
        ))
    
    return ResponseModel(data=result)
