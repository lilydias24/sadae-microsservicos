from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import SensorType, AlertLevel, AnomalyStatus

Base = declarative_base()

class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sensor_type = Column(String, nullable=False)  # SensorType enum
    location = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    unit = Column(String, nullable=False)
    min_threshold = Column(Float)
    max_threshold = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, ForeignKey("sensors.id"), nullable=False)
    sensor_type = Column(String, nullable=False)  # SensorType enum
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    location = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, ForeignKey("sensors.id"), nullable=False)
    sensor_type = Column(String, nullable=False)  # SensorType enum
    value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    severity = Column(String, nullable=False)  # AlertLevel enum
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, default=AnomalyStatus.PENDING)  # AnomalyStatus enum
    operator_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Observation(Base):
    __tablename__ = "observations"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, ForeignKey("sensors.id"), nullable=False)
    operator_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class LeakReport(Base):
    __tablename__ = "leak_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String, unique=True, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    reporter_name = Column(String, nullable=False)
    reporter_contact = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
