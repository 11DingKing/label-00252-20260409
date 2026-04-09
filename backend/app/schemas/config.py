"""System config schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConfigBase(BaseModel):
    """Config base schema."""
    config_key: str = Field(..., max_length=100)
    config_value: str
    config_type: str = Field(default="string", pattern="^(string|int|float|bool|json)$")
    description: Optional[str] = Field(None, max_length=255)


class ConfigUpdate(BaseModel):
    """Config update schema."""
    config_value: str
    description: Optional[str] = Field(None, max_length=255)


class ConfigResponse(ConfigBase):
    """Config response schema."""
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class ConfigHistoryResponse(BaseModel):
    """Config history response schema."""
    id: int
    config_id: int
    config_key: Optional[str] = None
    old_value: Optional[str]
    new_value: str
    changed_by: Optional[int]
    changed_at: datetime

    class Config:
        from_attributes = True
