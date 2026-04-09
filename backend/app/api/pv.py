"""PV system API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from app.db.session import get_db
from app.models.pv import PVSystem, PVData
from app.models.user import User, OperationLog
from app.schemas.pv import PVSystemCreate, PVSystemUpdate, PVSystemResponse, PVDataResponse, PVRealtimeData
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.api.deps import get_client_ip, get_engine

router = APIRouter(prefix="/api/pv", tags=["PV System"])
logger = get_logger(__name__)


@router.get("/systems", response_model=ResponseModel[List[PVSystemResponse]])
async def get_pv_systems(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all PV systems."""
    systems = db.query(PVSystem).all()
    return ResponseModel(data=[PVSystemResponse.model_validate(s) for s in systems])


@router.post("/systems", response_model=ResponseModel[PVSystemResponse])
async def create_pv_system(
    request: Request,
    system_data: PVSystemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new PV system."""
    system = PVSystem(**system_data.model_dump())
    db.add(system)
    
    log = OperationLog(
        user_id=current_user.id,
        action="create",
        module="pv",
        detail=f"Created PV system: {system_data.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(system)
    
    logger.info(f"PV system {system_data.name} created by {current_user.username}")
    
    return ResponseModel(data=PVSystemResponse.model_validate(system))


@router.get("/systems/{system_id}", response_model=ResponseModel[PVSystemResponse])
async def get_pv_system(
    system_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get PV system by ID."""
    system = db.query(PVSystem).filter(PVSystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="PV system not found")
    
    return ResponseModel(data=PVSystemResponse.model_validate(system))


@router.put("/systems/{system_id}", response_model=ResponseModel[PVSystemResponse])
async def update_pv_system(
    request: Request,
    system_id: int,
    system_data: PVSystemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update PV system configuration."""
    system = db.query(PVSystem).filter(PVSystem.id == system_id).first()
    if not system:
        raise HTTPException(status_code=404, detail="PV system not found")
    
    update_data = system_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(system, key, value)
    
    log = OperationLog(
        user_id=current_user.id,
        action="update",
        module="pv",
        detail=f"Updated PV system: {system.name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(system)
    
    logger.info(f"PV system {system.name} updated by {current_user.username}")
    
    return ResponseModel(data=PVSystemResponse.model_validate(system))


@router.get("/systems/{system_id}/data", response_model=PaginatedResponse[PVDataResponse])
async def get_pv_data(
    system_id: int,
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get PV system historical data."""
    query = db.query(PVData).filter(PVData.pv_id == system_id)
    
    if start_time:
        query = query.filter(PVData.timestamp >= start_time)
    if end_time:
        query = query.filter(PVData.timestamp <= end_time)
    
    total = query.count()
    data = query.order_by(PVData.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        data=[PVDataResponse.model_validate(d) for d in data],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/realtime", response_model=ResponseModel[List[PVRealtimeData]])
async def get_pv_realtime(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time PV data from simulation."""
    engine = get_engine()
    state = engine.get_current_state()
    
    systems = db.query(PVSystem).filter(PVSystem.is_active == True).all()
    result = []
    
    for system in systems:
        pv_data = state.get("pv", {}).get(system.id, {})
        result.append(PVRealtimeData(
            pv_id=system.id,
            name=system.name,
            irradiance=pv_data.get("irradiance", 0),
            temperature=pv_data.get("temperature", 25),
            power_output=pv_data.get("power_output", 0),
            voltage=pv_data.get("voltage", 0),
            current=pv_data.get("current", 0),
            efficiency=system.efficiency,
            capacity_kw=system.capacity_kw,
            utilization=pv_data.get("utilization", 0)
        ))
    
    return ResponseModel(data=result)
