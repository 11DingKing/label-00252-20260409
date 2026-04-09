"""Common schemas."""
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List
from datetime import datetime

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """Standard API response model."""
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    success: bool = True
    message: str = "Success"
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class TimeRangeQuery(BaseModel):
    """Time range query parameters."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
