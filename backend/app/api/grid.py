"""Grid management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.models.grid import GridConnection, GridData
from app.models.user import User, OperationLog
from app.schemas.grid import (
    GridConnectionUpdate, GridConnectionResponse, 
    GridDataResponse, GridRealtimeData, GridModeRequest, GridExportRequest
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.api.deps import get_client_ip, get_engine

router = APIRouter(prefix="/api/grid", tags=["Grid Management"])
logger = get_logger(__name__)


@router.get("/status", response_model=ResponseModel[GridRealtimeData])
async def get_grid_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current grid status."""
    engine = get_engine()
    state = engine.get_current_state()
    grid_data = state.get("grid", {})
    
    grid = db.query(GridConnection).first()
    if not grid:
        raise HTTPException(status_code=404, detail="Grid connection not found")
    
    return ResponseModel(data=GridRealtimeData(
        grid_id=grid.id,
        name=grid.name,
        power=grid_data.get("power", 0),
        voltage=grid_data.get("voltage", 380),
        frequency=grid_data.get("frequency", 50),
        phase_angle=grid_data.get("phase_angle", 0),
        mode=grid_data.get("mode", "grid_connected"),
        max_import=grid.max_import,
        max_export=grid.max_export,
        is_connected=grid_data.get("is_connected", True),
        connection_type=grid.connection_type
    ))


@router.post("/mode", response_model=ResponseModel)
async def set_grid_mode(
    request: Request,
    mode_request: GridModeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Switch between grid-connected and islanded mode."""
    engine = get_engine()
    success = engine.set_grid_mode(mode_request.mode)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to change grid mode")
    
    grid = db.query(GridConnection).first()
    if grid:
        grid.is_connected = (mode_request.mode == "grid_connected")
    
    log = OperationLog(
        user_id=current_user.id,
        action="control",
        module="grid",
        detail=f"Changed grid mode to: {mode_request.mode}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Grid mode changed to {mode_request.mode} by {current_user.username}")
    
    return ResponseModel(message=f"Grid mode changed to {mode_request.mode}")


@router.get("/data", response_model=PaginatedResponse[GridDataResponse])
async def get_grid_data(
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get grid historical data."""
    grid = db.query(GridConnection).first()
    if not grid:
        raise HTTPException(status_code=404, detail="Grid connection not found")
    
    query = db.query(GridData).filter(GridData.grid_id == grid.id)
    
    if start_time:
        query = query.filter(GridData.timestamp >= start_time)
    if end_time:
        query = query.filter(GridData.timestamp <= end_time)
    
    total = query.count()
    data = query.order_by(GridData.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(
        data=[GridDataResponse.model_validate(d) for d in data],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/realtime", response_model=ResponseModel[GridRealtimeData])
async def get_grid_realtime(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time grid data."""
    return await get_grid_status(current_user, db)


@router.post("/export", response_model=ResponseModel)
async def set_grid_export(
    request: Request,
    export_request: GridExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Configure grid export (feed-in) settings."""
    grid = db.query(GridConnection).first()
    if not grid:
        raise HTTPException(status_code=404, detail="Grid connection not found")
    
    grid.max_export = export_request.max_export
    if not export_request.enabled:
        grid.connection_type = "import_only"
    else:
        grid.connection_type = "bidirectional"
    
    log = OperationLog(
        user_id=current_user.id,
        action="config",
        module="grid",
        detail=f"Set grid export to {export_request.max_export} kW, enabled: {export_request.enabled}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Grid export settings updated by {current_user.username}")
    
    return ResponseModel(message="Grid export settings updated")


@router.put("/config", response_model=ResponseModel[GridConnectionResponse])
async def update_grid_config(
    request: Request,
    config: GridConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update grid connection configuration."""
    grid = db.query(GridConnection).first()
    if not grid:
        raise HTTPException(status_code=404, detail="Grid connection not found")
    
    update_data = config.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(grid, key, value)
    
    log = OperationLog(
        user_id=current_user.id,
        action="config",
        module="grid",
        detail=f"Updated grid configuration",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(grid)
    
    logger.info(f"Grid configuration updated by {current_user.username}")
    
    return ResponseModel(data=GridConnectionResponse.model_validate(grid))
