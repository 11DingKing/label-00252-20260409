"""Load system models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base, TimestampMixin


class Load(Base, TimestampMixin):
    """Load configuration model."""
    __tablename__ = "loads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    load_type = Column(String(50), nullable=False)  # office, production, lighting, hvac, ev_charger
    rated_power = Column(Float, nullable=False)  # 额定功率 kW
    priority = Column(Integer, default=3, nullable=False)  # 优先级 1-5 (1最高)
    is_controllable = Column(Boolean, default=True, nullable=False)  # 是否可控
    is_active = Column(Boolean, default=True, nullable=False)
    
    data = relationship("LoadData", back_populates="load")


class LoadData(Base):
    """Load real-time data model."""
    __tablename__ = "load_data"
    
    id = Column(Integer, primary_key=True, index=True)
    load_id = Column(Integer, ForeignKey("loads.id"), nullable=False)
    power = Column(Float, nullable=False)  # 实际功率 kW
    voltage = Column(Float, nullable=False)  # 电压 V
    current = Column(Float, nullable=False)  # 电流 A
    power_factor = Column(Float, default=0.95, nullable=False)  # 功率因数
    is_on = Column(Boolean, default=True, nullable=False)  # 开关状态
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    load = relationship("Load", back_populates="data")
