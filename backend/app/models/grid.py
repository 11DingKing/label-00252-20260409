"""Grid connection models."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base, TimestampMixin


class GridConnection(Base, TimestampMixin):
    """Grid connection configuration model."""
    __tablename__ = "grid_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    max_import = Column(Float, nullable=False)  # 最大购电功率 kW
    max_export = Column(Float, nullable=False)  # 最大售电功率 kW
    connection_type = Column(String(50), default="bidirectional", nullable=False)  # import_only, export_only, bidirectional
    is_connected = Column(Boolean, default=True, nullable=False)  # 并网状态
    
    data = relationship("GridData", back_populates="grid_connection")


class GridData(Base):
    """Grid real-time data model."""
    __tablename__ = "grid_data"
    
    id = Column(Integer, primary_key=True, index=True)
    grid_id = Column(Integer, ForeignKey("grid_connections.id"), nullable=False)
    power = Column(Float, nullable=False)  # 功率 kW (正=购电, 负=售电)
    voltage = Column(Float, nullable=False)  # 电压 V
    frequency = Column(Float, nullable=False)  # 频率 Hz
    phase_angle = Column(Float, default=0.0, nullable=False)  # 相角 度
    mode = Column(String(20), nullable=False)  # grid_connected, islanded
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    grid_connection = relationship("GridConnection", back_populates="data")
