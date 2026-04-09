"""Wind system models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base, TimestampMixin


class WindSystem(Base, TimestampMixin):
    """Wind turbine system configuration model."""
    __tablename__ = "wind_systems"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    capacity_kw = Column(Float, nullable=False)  # 装机容量 kW
    cut_in_speed = Column(Float, default=3.0, nullable=False)  # 切入风速 m/s
    rated_speed = Column(Float, default=12.0, nullable=False)  # 额定风速 m/s
    cut_out_speed = Column(Float, default=25.0, nullable=False)  # 切出风速 m/s
    is_active = Column(Boolean, default=True, nullable=False)
    
    data = relationship("WindData", back_populates="wind_system")


class WindData(Base):
    """Wind system real-time data model."""
    __tablename__ = "wind_data"
    
    id = Column(Integer, primary_key=True, index=True)
    wind_id = Column(Integer, ForeignKey("wind_systems.id"), nullable=False)
    wind_speed = Column(Float, nullable=False)  # 风速 m/s
    wind_direction = Column(Float, nullable=False)  # 风向 度
    power_output = Column(Float, nullable=False)  # 输出功率 kW
    rotor_speed = Column(Float, nullable=False)  # 转子转速 rpm
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    wind_system = relationship("WindSystem", back_populates="data")
