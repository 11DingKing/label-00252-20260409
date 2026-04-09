"""PV system schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PVSystemBase(BaseModel):
    """PV system base schema."""
    name: str = Field(..., max_length=100)
    capacity_kw: float = Field(..., gt=0)
    efficiency: float = Field(default=0.18, ge=0, le=1)
    panel_area: float = Field(..., gt=0)
    is_active: bool = True


class PVSystemCreate(PVSystemBase):
    """PV system create schema."""
    pass


class PVSystemUpdate(BaseModel):
    """PV system update schema."""
    name: Optional[str] = Field(None, max_length=100)
    capacity_kw: Optional[float] = Field(None, gt=0)
    efficiency: Optional[float] = Field(None, ge=0, le=1)
    panel_area: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class PVSystemResponse(PVSystemBase):
    """PV system response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PVDataResponse(BaseModel):
    """PV data response schema."""
    id: int
    pv_id: int
    irradiance: float
    temperature: float
    power_output: float
    voltage: float
    current: float
    timestamp: datetime

    class Config:
        from_attributes = True


class PVRealtimeData(BaseModel):
    """PV realtime data schema."""
    pv_id: int
    name: str
    irradiance: float
    temperature: float
    power_output: float
    voltage: float
    current: float
    efficiency: float
    capacity_kw: float
    utilization: float
