"""User schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """User base schema."""
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(default="operator", pattern="^(admin|operator|viewer)$")
    is_active: bool = True


class UserCreate(UserBase):
    """User create schema."""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """User update schema."""
    role: Optional[str] = Field(None, pattern="^(admin|operator|viewer)$")
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(UserBase):
    """User response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OperationLogResponse(BaseModel):
    """Operation log response schema."""
    id: int
    user_id: Optional[int]
    username: Optional[str] = None
    action: str
    module: str
    detail: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
