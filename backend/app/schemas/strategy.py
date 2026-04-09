"""Control strategy schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class StrategyBase(BaseModel):
    """Strategy base schema."""
    name: str = Field(..., max_length=100)
    strategy_type: str = Field(..., pattern="^(economic|green|stability|custom)$")
    parameters: Dict[str, Any]
    is_default: bool = False
    is_active: bool = True


class StrategyCreate(StrategyBase):
    """Strategy create schema."""
    pass


class StrategyUpdate(BaseModel):
    """Strategy update schema."""
    name: Optional[str] = Field(None, max_length=100)
    strategy_type: Optional[str] = Field(None, pattern="^(economic|green|stability|custom)$")
    parameters: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class StrategyResponse(StrategyBase):
    """Strategy response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
