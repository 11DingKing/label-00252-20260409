"""Alarm schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AlarmBase(BaseModel):
    """Alarm base schema."""
    alarm_code: str = Field(..., max_length=20)
    alarm_name: str = Field(..., max_length=100)
    severity: str = Field(..., pattern="^(info|warning|critical)$")
    module: str = Field(..., pattern="^(pv|wind|battery|load|grid|system)$")
    condition_expr: str = Field(..., max_length=255)
    is_active: bool = True


class AlarmCreate(AlarmBase):
    """Alarm create schema."""
    pass


class AlarmUpdate(BaseModel):
    """Alarm update schema."""
    alarm_name: Optional[str] = Field(None, max_length=100)
    severity: Optional[str] = Field(None, pattern="^(info|warning|critical)$")
    condition_expr: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class AlarmResponse(AlarmBase):
    """Alarm response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlarmHistoryResponse(BaseModel):
    """Alarm history response schema."""
    id: int
    alarm_id: int
    alarm_code: Optional[str] = None
    alarm_name: Optional[str] = None
    severity: Optional[str] = None
    module: Optional[str] = None
    status: str
    message: Optional[str]
    acknowledged_by: Optional[int]
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    cleared_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlarmAcknowledgeRequest(BaseModel):
    """Alarm acknowledge request schema."""
    message: Optional[str] = None
