"""Authentication schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    """User info schema."""
    id: int
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


LoginResponse.model_rebuild()
