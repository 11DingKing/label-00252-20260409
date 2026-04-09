"""Wind system schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WindSystemBase(BaseModel):
    """Wind system base schema."""
    name: str = Field(..., max_length=100)
    capacity_kw: float = Field(..., gt=0)
    cut_in_speed: float = Field(default=3.0, ge=0)
    rated_speed: float = Field(default=12.0, gt=0)
    cut_out_speed: float = Field(default=25.0, gt=0)
    is_active: bool = True


class WindSystemCreate(WindSystemBase):
    """Wind system create schema."""
    pass


class WindSystemUpdate(BaseModel):
    """Wind system update schema."""
    name: Optional[str] = Field(None, max_length=100)
    capacity_kw: Optional[float] = Field(None, gt=0)
    cut_in_speed: Optional[float] = Field(None, ge=0)
    rated_speed: Optional[float] = Field(None, gt=0)
    cut_out_speed: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class WindSystemResponse(WindSystemBase):
    """Wind system response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WindDataResponse(BaseModel):
    """Wind data response schema."""
    id: int
    wind_id: int
    wind_speed: float
    wind_direction: float
    power_output: float
    rotor_speed: float
    timestamp: datetime

    class Config:
        from_attributes = True


class WindRealtimeData(BaseModel):
    """Wind realtime data schema."""
    wind_id: int
    name: str
    wind_speed: float
    wind_direction: float
    power_output: float
    rotor_speed: float
    capacity_kw: float
    utilization: float
