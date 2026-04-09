"""Load schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoadBase(BaseModel):
    """Load base schema."""
    name: str = Field(..., max_length=100)
    load_type: str = Field(..., pattern="^(office|production|lighting|hvac|ev_charger|other)$")
    rated_power: float = Field(..., gt=0)
    priority: int = Field(default=3, ge=1, le=5)
    is_controllable: bool = True
    is_active: bool = True


class LoadCreate(LoadBase):
    """Load create schema."""
    pass


class LoadUpdate(BaseModel):
    """Load update schema."""
    name: Optional[str] = Field(None, max_length=100)
    load_type: Optional[str] = Field(None, pattern="^(office|production|lighting|hvac|ev_charger|other)$")
    rated_power: Optional[float] = Field(None, gt=0)
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_controllable: Optional[bool] = None
    is_active: Optional[bool] = None


class LoadResponse(LoadBase):
    """Load response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoadDataResponse(BaseModel):
    """Load data response schema."""
    id: int
    load_id: int
    power: float
    voltage: float
    current: float
    power_factor: float
    is_on: bool
    timestamp: datetime

    class Config:
        from_attributes = True


class LoadRealtimeData(BaseModel):
    """Load realtime data schema."""
    load_id: int
    name: str
    load_type: str
    power: float
    voltage: float
    current: float
    power_factor: float
    rated_power: float
    priority: int
    is_on: bool
    is_controllable: bool
    is_active: bool
    utilization: float


class LoadControlRequest(BaseModel):
    """Load control request schema."""
    is_on: bool
