"""Control strategy models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base, TimestampMixin


class ControlStrategy(Base, TimestampMixin):
    """Control strategy configuration model."""
    __tablename__ = "control_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    strategy_type = Column(String(50), nullable=False)  # economic, green, stability, custom
    parameters = Column(JSON, nullable=False)  # 策略参数
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
