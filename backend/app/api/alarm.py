"""Alarm management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.models.alarm import Alarm, AlarmHistory
from app.models.user import User, OperationLog
from app.schemas.alarm import (
    AlarmCreate, AlarmUpdate, AlarmResponse, 
    AlarmHistoryResponse, AlarmAcknowledgeRequest
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.api.deps import get_client_ip

router = APIRouter(prefix="/api/alarms", tags=["Alarm Management"])
logger = get_logger(__name__)


@router.get("", response_model=ResponseModel[List[AlarmResponse]])
async def get_alarms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all alarm configurations."""
    alarms = db.query(Alarm).all()
    return ResponseModel(data=[AlarmResponse.model_validate(a) for a in alarms])


@router.post("", response_model=ResponseModel[AlarmResponse])
async def create_alarm(
    request: Request,
    alarm_data: AlarmCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new alarm rule."""
    existing = db.query(Alarm).filter(Alarm.alarm_code == alarm_data.alarm_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Alarm code already exists")
    
    alarm = Alarm(**alarm_data.model_dump())
    db.add(alarm)
    
    log = OperationLog(
        user_id=current_user.id,
        action="create",
        module="alarm",
        detail=f"Created alarm: {alarm_data.alarm_name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(alarm)
    
    logger.info(f"Alarm {alarm_data.alarm_name} created by {current_user.username}")
    
    return ResponseModel(data=AlarmResponse.model_validate(alarm))


@router.get("/history", response_model=PaginatedResponse[AlarmHistoryResponse])
async def get_alarm_history(
    status: str = None,
    severity: str = None,
    module: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alarm history."""
    query = db.query(AlarmHistory).join(Alarm)
    
    if status:
        query = query.filter(AlarmHistory.status == status)
    if severity:
        query = query.filter(Alarm.severity == severity)
    if module:
        query = query.filter(Alarm.module == module)
    if start_time:
        query = query.filter(AlarmHistory.triggered_at >= start_time)
    if end_time:
        query = query.filter(AlarmHistory.triggered_at <= end_time)
    
    total = query.count()
    records = query.order_by(AlarmHistory.triggered_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for record in records:
        data = AlarmHistoryResponse.model_validate(record)
        data.alarm_code = record.alarm.alarm_code
        data.alarm_name = record.alarm.alarm_name
        data.severity = record.alarm.severity
        data.module = record.alarm.module
        result.append(data)
    
    return PaginatedResponse(
        data=result,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/{alarm_history_id}/acknowledge", response_model=ResponseModel)
async def acknowledge_alarm(
    request: Request,
    alarm_history_id: int,
    ack_request: AlarmAcknowledgeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge an alarm."""
    record = db.query(AlarmHistory).filter(AlarmHistory.id == alarm_history_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Alarm record not found")
    
    if record.status != "triggered":
        raise HTTPException(status_code=400, detail="Alarm is not in triggered state")
    
    record.status = "acknowledged"
    record.acknowledged_by = current_user.id
    record.acknowledged_at = datetime.now()
    if ack_request.message:
        record.message = ack_request.message
    
    log = OperationLog(
        user_id=current_user.id,
        action="acknowledge",
        module="alarm",
        detail=f"Acknowledged alarm ID: {alarm_history_id}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    
    logger.info(f"Alarm {alarm_history_id} acknowledged by {current_user.username}")
    
    return ResponseModel(message="Alarm acknowledged")


@router.get("/active", response_model=ResponseModel[List[AlarmHistoryResponse]])
async def get_active_alarms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get currently active (uncleared) alarms."""
    records = db.query(AlarmHistory).join(Alarm).filter(
        AlarmHistory.status.in_(["triggered", "acknowledged"])
    ).order_by(AlarmHistory.triggered_at.desc()).all()
    
    result = []
    for record in records:
        data = AlarmHistoryResponse.model_validate(record)
        data.alarm_code = record.alarm.alarm_code
        data.alarm_name = record.alarm.alarm_name
        data.severity = record.alarm.severity
        data.module = record.alarm.module
        result.append(data)
    
    return ResponseModel(data=result)


@router.put("/{alarm_id}", response_model=ResponseModel[AlarmResponse])
async def update_alarm(
    request: Request,
    alarm_id: int,
    alarm_data: AlarmUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update alarm configuration."""
    alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    
    update_data = alarm_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(alarm, key, value)
    
    log = OperationLog(
        user_id=current_user.id,
        action="update",
        module="alarm",
        detail=f"Updated alarm: {alarm.alarm_name}",
        ip_address=get_client_ip(request)
    )
    db.add(log)
    db.commit()
    db.refresh(alarm)
    
    logger.info(f"Alarm {alarm.alarm_name} updated by {current_user.username}")
    
    return ResponseModel(data=AlarmResponse.model_validate(alarm))
