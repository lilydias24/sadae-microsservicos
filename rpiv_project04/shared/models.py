from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Enums
class UserRole(str, Enum):
    OPERATOR = "operator"
    CITIZEN = "citizen"
    CRISIS_MANAGER = "crise"
    MAINTENANCE_MANAGER = "maintenance_manager"
    FINANCIAL_MANAGER = "financial_manager"
    SUPPORT_AGENT = "support_agent"

class SensorType(str, Enum):
    PRESSURE = "pressure"
    FLOW = "flow"
    WATER_QUALITY = "water_quality"
    PRECIPITATION = "precipitation"
    RIVER_LEVEL = "river_level"

class AlertLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISCARDED = "discarded"
    IN_TREATMENT = "in_treatment"
    RESOLVED = "resolved"

class ServiceOrderStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class BillStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CONTESTED = "contested"
    CANCELLED = "cancelled"

# Pydantic Models for API
class UserBase(BaseModel):
    email: str
    name: str
    role: UserRole
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SensorReading(BaseModel):
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    location: str
    timestamp: datetime
    
class AnomalyBase(BaseModel):
    sensor_id: str
    sensor_type: SensorType
    value: float
    threshold_value: float
    severity: AlertLevel
    description: str
    location: str

class AnomalyCreate(AnomalyBase):
    pass

class AnomalyResponse(AnomalyBase):
    id: int
    status: AnomalyStatus
    created_at: datetime
    updated_at: Optional[datetime]
    operator_id: Optional[int]
    
    class Config:
        from_attributes = True

class ServiceOrderBase(BaseModel):
    title: str
    description: str
    priority: AlertLevel
    location: str
    anomaly_id: Optional[int] = None

class ServiceOrderCreate(ServiceOrderBase):
    pass

class ServiceOrderResponse(ServiceOrderBase):
    id: int
    status: ServiceOrderStatus
    created_at: datetime
    updated_at: Optional[datetime]
    assigned_to: Optional[str]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ComplaintBase(BaseModel):
    title: str
    description: str
    location: str
    category: str

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintResponse(ComplaintBase):
    id: int
    citizen_id: int
    status: str
    protocol_number: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class BillBase(BaseModel):
    customer_id: int
    amount: float
    consumption: float
    due_date: datetime
    billing_period_start: datetime
    billing_period_end: datetime

class BillCreate(BillBase):
    pass

class BillResponse(BillBase):
    id: int
    status: BillStatus
    created_at: datetime
    paid_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    recipient_id: int
    title: str
    message: str
    type: str
    channel: str  # email, sms, push

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: int
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
