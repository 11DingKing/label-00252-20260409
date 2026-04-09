"""Grid schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GridConnectionBase(BaseModel):
    """Grid connection base schema."""
    name: str = Field(..., max_length=100)
    max_import: float = Field(..., gt=0)
    max_export: float = Field(..., gt=0)
    connection_type: str = Field(default="bidirectional", pattern="^(import_only|export_only|bidirectional)$")
    is_connected: bool = True


class GridConnectionUpdate(BaseModel):
    """Grid connection update schema."""
    name: Optional[str] = Field(None, max_length=100)
    max_import: Optional[float] = Field(None, gt=0)
    max_export: Optional[float] = Field(None, gt=0)
    connection_type: Optional[str] = Field(None, pattern="^(import_only|export_only|bidirectional)$")
    is_connected: Optional[bool] = None


class GridConnectionResponse(GridConnectionBase):
    """Grid connection response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GridDataResponse(BaseModel):
    """Grid data response schema."""
    id: int
    grid_id: int
    power: float
    voltage: float
    frequency: float
    phase_angle: float
    mode: str
    timestamp: datetime

    class Config:
        from_attributes = True


class GridRealtimeData(BaseModel):
    """Grid realtime data schema."""
    grid_id: int
    name: str
    power: float
    voltage: float
    frequency: float
    phase_angle: float
    mode: str
    max_import: float
    max_export: float
    is_connected: bool
    connection_type: str = "bidirectional"


class GridModeRequest(BaseModel):
    """Grid mode change request schema."""
    mode: str = Field(..., pattern="^(grid_connected|islanded)$")


class GridExportRequest(BaseModel):
    """Grid export settings request schema."""
    max_export: float = Field(..., ge=0)
    enabled: bool = True
