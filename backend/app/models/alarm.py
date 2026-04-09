"""Alarm models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base, TimestampMixin


class Alarm(Base, TimestampMixin):
    """Alarm configuration model."""
    __tablename__ = "alarms"
    
    id = Column(Integer, primary_key=True, index=True)
    alarm_code = Column(String(20), unique=True, nullable=False)
    alarm_name = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, critical
    module = Column(String(50), nullable=False)  # pv, wind, battery, load, grid
    condition_expr = Column(String(255), nullable=False)  # 触发条件表达式
    is_active = Column(Boolean, default=True, nullable=False)
    
    history = relationship("AlarmHistory", back_populates="alarm")


class AlarmHistory(Base):
    """Alarm history model."""
    __tablename__ = "alarm_history"
    
    id = Column(Integer, primary_key=True, index=True)
    alarm_id = Column(Integer, ForeignKey("alarms.id"), nullable=False)
    status = Column(String(20), nullable=False)  # triggered, acknowledged, cleared
    message = Column(Text, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    triggered_at = Column(DateTime, default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    cleared_at = Column(DateTime, nullable=True)
    
    alarm = relationship("Alarm", back_populates="history")
