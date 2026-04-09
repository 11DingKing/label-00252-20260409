"""PV system models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base, TimestampMixin


class PVSystem(Base, TimestampMixin):
    """PV system configuration model."""
    __tablename__ = "pv_systems"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    capacity_kw = Column(Float, nullable=False)  # 装机容量 kW
    efficiency = Column(Float, default=0.18, nullable=False)  # 转换效率
    panel_area = Column(Float, nullable=False)  # 面板面积 m²
    is_active = Column(Boolean, default=True, nullable=False)
    
    data = relationship("PVData", back_populates="pv_system")


class PVData(Base):
    """PV system real-time data model."""
    __tablename__ = "pv_data"
    
    id = Column(Integer, primary_key=True, index=True)
    pv_id = Column(Integer, ForeignKey("pv_systems.id"), nullable=False)
    irradiance = Column(Float, nullable=False)  # 光照强度 W/m²
    temperature = Column(Float, nullable=False)  # 环境温度 °C
    power_output = Column(Float, nullable=False)  # 输出功率 kW
    voltage = Column(Float, nullable=False)  # 电压 V
    current = Column(Float, nullable=False)  # 电流 A
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    pv_system = relationship("PVSystem", back_populates="data")
