"""Logging API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.models.user import User, OperationLog
from app.schemas.user import OperationLogResponse
from app.schemas.common import PaginatedResponse
from app.core.security import get_current_user, get_current_admin

router = APIRouter(prefix="/api/logs", tags=["Logs"])


@router.get("/operation", response_model=PaginatedResponse[OperationLogResponse])
async def get_operation_logs(
    module: str = None,
    action: str = None,
    user_id: int = None,
    start_time: datetime = None,
    end_time: datetime = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get operation logs (admin only)."""
    query = db.query(OperationLog)
    
    if module:
        query = query.filter(OperationLog.module == module)
    if action:
        query = query.filter(OperationLog.action == action)
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if start_time:
        query = query.filter(OperationLog.created_at >= start_time)
    if end_time:
        query = query.filter(OperationLog.created_at <= end_time)
    
    total = query.count()
    logs = query.order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for log in logs:
        data = OperationLogResponse.model_validate(log)
        if log.user:
            data.username = log.user.username
        result.append(data)
    
    return PaginatedResponse(
        data=result,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
