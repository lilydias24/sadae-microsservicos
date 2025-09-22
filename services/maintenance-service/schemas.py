from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import ServiceOrderStatus, AlertLevel

class ServiceOrderBase(BaseModel):
    title: str
    description: str
    priority: AlertLevel
    location: str
    anomaly_id: Optional[int] = None

class ServiceOrderCreate(ServiceOrderBase):
    pass

class ServiceOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[AlertLevel] = None
    location: Optional[str] = None
    status: Optional[ServiceOrderStatus] = None
    assigned_team: Optional[str] = None

class ServiceOrderResponse(ServiceOrderBase):
    id: int
    protocol_number: str
    status: ServiceOrderStatus
    created_by: int
    assigned_team: Optional[str]
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]
    complaint_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MaintenanceBase(BaseModel):
    service_order_id: Optional[int] = None
    title: str
    description: str
    team_name: str
    location: str
    completion_date: datetime
    duration_hours: Optional[float] = None
    cost: Optional[float] = None
    materials_used: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceResponse(MaintenanceBase):
    id: int
    registered_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComplaintBase(BaseModel):
    title: str
    description: str
    category: str
    location: str
    citizen_name: str
    citizen_contact: str

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintResponse(ComplaintBase):
    id: int
    protocol_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ServiceEvaluationBase(BaseModel):
    service_order_id: int
    rating: int  # 1-5 stars
    comment: Optional[str] = None
    evaluator_name: Optional[str] = None
    evaluator_contact: Optional[str] = None

class ServiceEvaluationCreate(ServiceEvaluationBase):
    pass

class ServiceEvaluationResponse(ServiceEvaluationBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    specialization: Optional[str] = None
    members_count: int = 0

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReportFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_name: Optional[str] = None
    location: Optional[str] = None
    service_type: Optional[str] = None

class MaintenanceReportResponse(BaseModel):
    report_id: str
    filters: ReportFilters
    summary: Dict[str, Any]
    team_statistics: Dict[str, Dict[str, Any]]
    interventions: List[MaintenanceResponse]
    generated_at: datetime
    generated_by: str
