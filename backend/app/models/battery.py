"""Battery storage system models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base, TimestampMixin


class BatterySystem(Base, TimestampMixin):
    """Battery storage system configuration model."""
    __tablename__ = "battery_systems"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    capacity_kwh = Column(Float, nullable=False)  # 容量 kWh
    max_charge_rate = Column(Float, nullable=False)  # 最大充电功率 kW
    max_discharge_rate = Column(Float, nullable=False)  # 最大放电功率 kW
    charge_efficiency = Column(Float, default=0.95, nullable=False)  # 充电效率
    discharge_efficiency = Column(Float, default=0.95, nullable=False)  # 放电效率
    min_soc = Column(Float, default=0.1, nullable=False)  # 最小SOC
    max_soc = Column(Float, default=0.9, nullable=False)  # 最大SOC
    is_active = Column(Boolean, default=True, nullable=False)
    
    data = relationship("BatteryData", back_populates="battery_system")


class BatteryData(Base):
    """Battery system real-time data model."""
    __tablename__ = "battery_data"
    
    id = Column(Integer, primary_key=True, index=True)
    battery_id = Column(Integer, ForeignKey("battery_systems.id"), nullable=False)
    soc = Column(Float, nullable=False)  # 荷电状态 0-1
    power = Column(Float, nullable=False)  # 功率 kW (正=放电, 负=充电)
    voltage = Column(Float, nullable=False)  # 电压 V
    current = Column(Float, nullable=False)  # 电流 A
    temperature = Column(Float, nullable=False)  # 温度 °C
    status = Column(String(20), nullable=False)  # idle, charging, discharging
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    battery_system = relationship("BatterySystem", back_populates="data")
