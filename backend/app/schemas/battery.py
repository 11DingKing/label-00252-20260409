"""Battery system schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BatterySystemBase(BaseModel):
    """Battery system base schema."""
    name: str = Field(..., max_length=100)
    capacity_kwh: float = Field(..., gt=0)
    max_charge_rate: float = Field(..., gt=0)
    max_discharge_rate: float = Field(..., gt=0)
    charge_efficiency: float = Field(default=0.95, ge=0, le=1)
    discharge_efficiency: float = Field(default=0.95, ge=0, le=1)
    min_soc: float = Field(default=0.1, ge=0, le=1)
    max_soc: float = Field(default=0.9, ge=0, le=1)
    is_active: bool = True


class BatterySystemCreate(BatterySystemBase):
    """Battery system create schema."""
    pass


class BatterySystemUpdate(BaseModel):
    """Battery system update schema."""
    name: Optional[str] = Field(None, max_length=100)
    capacity_kwh: Optional[float] = Field(None, gt=0)
    max_charge_rate: Optional[float] = Field(None, gt=0)
    max_discharge_rate: Optional[float] = Field(None, gt=0)
    charge_efficiency: Optional[float] = Field(None, ge=0, le=1)
    discharge_efficiency: Optional[float] = Field(None, ge=0, le=1)
    min_soc: Optional[float] = Field(None, ge=0, le=1)
    max_soc: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None


class BatterySystemResponse(BatterySystemBase):
    """Battery system response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatteryDataResponse(BaseModel):
    """Battery data response schema."""
    id: int
    battery_id: int
    soc: float
    power: float
    voltage: float
    current: float
    temperature: float
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


class BatteryRealtimeData(BaseModel):
    """Battery realtime data schema."""
    battery_id: int
    name: str
    soc: float
    power: float
    voltage: float
    current: float
    temperature: float
    status: str
    capacity_kwh: float
    available_energy: float


class BatteryControlRequest(BaseModel):
    """Battery control request schema."""
    power: float = Field(..., description="Target power in kW (positive=discharge, negative=charge)")
