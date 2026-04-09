"""System configuration API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.config import SystemConfig, ConfigHistory
from app.models.user import User, OperationLog
from app.schemas.config import ConfigUpdate, ConfigResponse, ConfigHistoryResponse
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.security import get_current_user, get_current_admin
from app.core.logging import get_logger
from app.api.deps import get_client_ip

router = APIRouter(prefix="/api/config", tags=["System Configuration"])
logger = get_logger(__name__)


@router.get("", response_model=ResponseModel[List[ConfigResponse]])
async def get_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all system configurations."""
    configs = db.query(SystemConfig).all()
    return ResponseModel(data=[ConfigResponse.model_validate(c) for c in configs])


@router.put("/{config_key}", response_model=ResponseModel[ConfigResponse])
async def update_config(
    request: Request,
    config_key: str,
    config_data: ConfigUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a system configuration (admin only)."""
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    old_value = config.config_value
    
    # Record history
    history = ConfigHistory(
        config_id=config.id,
        old_value=old_value,
        new_value=config_data.config_value,
        changed_by=current_user.id
    )
    db.add(history)
    
    # Update config
    config.config_value = config_data.config_value
    if config_data.description is not None:
        config.description = config_data.description
    
    log = OperationLog(
        user_id=current_user.id,
        action="update",
        module="config",
        detail=f"Updated config {config_key}: {old_value} -> {config_data.config_value}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(config)
    
    logger.info(f"Config {config_key} updated by {current_user.username}")
    
    return ResponseModel(data=ConfigResponse.model_validate(config))


@router.get("/history", response_model=PaginatedResponse[ConfigHistoryResponse])
async def get_config_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get configuration change history (admin only)."""
    query = db.query(ConfigHistory).join(SystemConfig)
    
    total = query.count()
    records = query.order_by(ConfigHistory.changed_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for record in records:
        data = ConfigHistoryResponse.model_validate(record)
        data.config_key = record.config.config_key
        result.append(data)
    
    return PaginatedResponse(
        data=result,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/thresholds")
async def get_thresholds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get voltage and frequency thresholds for grid status monitoring."""
    config_keys = ["voltage_nominal", "frequency_nominal", "voltage_tolerance", "frequency_tolerance"]
    configs = db.query(SystemConfig).filter(SystemConfig.config_key.in_(config_keys)).all()
    
    config_dict = {c.config_key: c for c in configs}
    
    def get_config_value(key, default):
        if key in config_dict:
            config = config_dict[key]
            if config.config_type == "float":
                return float(config.config_value)
            elif config.config_type == "int":
                return int(config.config_value)
            return config.config_value
        return default
    
    voltage_nominal = get_config_value("voltage_nominal", 380.0)
    frequency_nominal = get_config_value("frequency_nominal", 50.0)
    voltage_tolerance = get_config_value("voltage_tolerance", 0.05)
    frequency_tolerance = get_config_value("frequency_tolerance", 0.004)
    
    return ResponseModel(data={
        "voltage": {
            "nominal": voltage_nominal,
            "tolerance": voltage_tolerance,
            "min": voltage_nominal * (1 - voltage_tolerance),
            "max": voltage_nominal * (1 + voltage_tolerance)
        },
        "frequency": {
            "nominal": frequency_nominal,
            "tolerance": frequency_tolerance,
            "min": frequency_nominal - frequency_tolerance,
            "max": frequency_nominal + frequency_tolerance
        }
    })
