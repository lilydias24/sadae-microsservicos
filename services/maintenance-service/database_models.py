from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import ServiceOrderStatus, AlertLevel

Base = declarative_base()

class ServiceOrder(Base):
    __tablename__ = "service_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, nullable=False)  # AlertLevel enum
    location = Column(String, nullable=False)
    status = Column(String, default=ServiceOrderStatus.OPEN)  # ServiceOrderStatus enum
    created_by = Column(Integer, nullable=False)
    assigned_team = Column(String)
    assigned_at = Column(DateTime)
    completed_at = Column(DateTime)
    anomaly_id = Column(Integer)  # Reference to monitoring service anomaly
    complaint_id = Column(Integer)  # Reference to complaint
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Maintenance(Base):
    __tablename__ = "maintenances"
    
    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    team_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    completion_date = Column(DateTime, nullable=False)
    duration_hours = Column(Float)
    cost = Column(Float)
    materials_used = Column(Text)
    registered_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    protocol_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    location = Column(String, nullable=False)
    citizen_name = Column(String, nullable=False)
    citizen_contact = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServiceEvaluation(Base):
    __tablename__ = "service_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    evaluator_name = Column(String)
    evaluator_contact = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    specialization = Column(String)  # e.g., "plumbing", "electrical", "general"
    members_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
