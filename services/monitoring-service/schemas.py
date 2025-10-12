from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import SensorType, AlertLevel, AnomalyStatus

class SensorBase(BaseModel):
    id: str
    name: str
    sensor_type: SensorType
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    unit: str
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None

class SensorCreate(SensorBase):
    pass

class SensorResponse(SensorBase):
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SensorReadingBase(BaseModel):
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    location: str
    timestamp: datetime

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReadingResponse(SensorReadingBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

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
    operator_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ObservationBase(BaseModel):
    sensor_id: str
    text: str
    timestamp: datetime

class ObservationCreate(ObservationBase):
    pass

class ObservationResponse(ObservationBase):
    id: int
    operator_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class LeakReportBase(BaseModel):
    location: str
    description: str
    reporter_name: str
    reporter_contact: str

class LeakReportCreate(LeakReportBase):
    pass

class LeakReportResponse(LeakReportBase):
    id: int
    protocol_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReportFilters(BaseModel):
    sensor_type: Optional[SensorType] = None
    sensor_id: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


