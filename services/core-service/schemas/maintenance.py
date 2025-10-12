"""
Maintenance Service Schemas - Pydantic models for maintenance operations
Handles service orders, maintenance records, complaints, evaluations and teams
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

# Status enums
class ServiceOrderStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class AlertLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class ComplaintCategory(str, Enum):
    WATER_LEAK = "water_leak"
    PRESSURE_ISSUE = "pressure_issue"
    QUALITY_ISSUE = "quality_issue"
    BILLING_ISSUE = "billing_issue"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"

class ComplaintStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"

# ==================== SERVICE ORDER SCHEMAS ====================

class ServiceOrderBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    priority: AlertLevel = AlertLevel.MEDIUM
    location: str = Field(..., min_length=5, max_length=500)
    anomaly_id: Optional[int] = None

class ServiceOrderCreate(ServiceOrderBase):
    pass

class ServiceOrderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    priority: Optional[AlertLevel] = None
    location: Optional[str] = Field(None, min_length=5, max_length=500)
    status: Optional[ServiceOrderStatus] = None
    assigned_team: Optional[str] = None
    notes: Optional[str] = None

class ServiceOrderResponse(ServiceOrderBase):
    id: int
    protocol_number: str
    status: ServiceOrderStatus
    created_by: int
    created_by_name: Optional[str] = None
    assigned_team: Optional[str] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    complaint_id: Optional[int] = None
    estimated_completion: Optional[datetime] = None
    actual_cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ServiceOrderAssign(BaseModel):
    team_name: str = Field(..., min_length=1, max_length=100)
    estimated_completion: Optional[datetime] = None
    notes: Optional[str] = None

class ServiceOrderProgress(BaseModel):
    status: ServiceOrderStatus
    progress_notes: str = Field(..., min_length=5, max_length=1000)
    estimated_completion: Optional[datetime] = None

# ==================== MAINTENANCE SCHEMAS ====================

class MaintenanceBase(BaseModel):
    service_order_id: Optional[int] = None
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    team_name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=5, max_length=500)
    completion_date: datetime
    duration_hours: Optional[float] = Field(None, ge=0, le=1000)
    cost: Optional[float] = Field(None, ge=0)
    materials_used: Optional[str] = None
    equipment_used: Optional[str] = None
    work_type: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    duration_hours: Optional[float] = Field(None, ge=0, le=1000)
    cost: Optional[float] = Field(None, ge=0)
    materials_used: Optional[str] = None
    equipment_used: Optional[str] = None
    work_type: Optional[str] = None

class MaintenanceResponse(MaintenanceBase):
    id: int
    registered_by: int
    registered_by_name: Optional[str] = None
    photos: Optional[List[str]] = None
    quality_check: Optional[bool] = None
    quality_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ==================== COMPLAINT SCHEMAS ====================

class ComplaintBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: ComplaintCategory
    location: str = Field(..., min_length=5, max_length=500)
    citizen_name: str = Field(..., min_length=2, max_length=100)
    citizen_contact: str = Field(..., min_length=5, max_length=200)
    citizen_email: Optional[str] = None
    urgency_level: AlertLevel = AlertLevel.MEDIUM

class ComplaintCreate(ComplaintBase):
    pass

class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatus] = None
    assigned_to: Optional[str] = None
    response_message: Optional[str] = None
    resolution_notes: Optional[str] = None

class ComplaintResponse(ComplaintBase):
    id: int
    protocol_number: str
    status: ComplaintStatus
    assigned_to: Optional[str] = None
    response_message: Optional[str] = None
    resolution_notes: Optional[str] = None
    service_order_id: Optional[int] = None
    photos: Optional[List[str]] = None
    follow_up_required: bool = False
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PublicComplaintCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: ComplaintCategory
    location: str = Field(..., min_length=5, max_length=500)
    citizen_name: str = Field(..., min_length=2, max_length=100)
    citizen_contact: str = Field(..., min_length=5, max_length=200)
    citizen_email: Optional[str] = None

class PublicComplaintResponse(BaseModel):
    protocol_number: str
    title: str
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime

# ==================== SERVICE EVALUATION SCHEMAS ====================

class ServiceEvaluationBase(BaseModel):
    service_order_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
    evaluator_name: Optional[str] = Field(None, max_length=100)
    evaluator_contact: Optional[str] = Field(None, max_length=200)
    quality_aspects: Optional[Dict[str, int]] = None  # {"timeliness": 5, "quality": 4, etc.}

class ServiceEvaluationCreate(ServiceEvaluationBase):
    
    @validator('quality_aspects')
    def validate_quality_aspects(cls, v):
        if v:
            for aspect, rating in v.items():
                if not isinstance(rating, int) or rating < 1 or rating > 5:
                    raise ValueError(f"Quality aspect '{aspect}' must have rating between 1-5")
        return v

class ServiceEvaluationResponse(ServiceEvaluationBase):
    id: int
    verified: bool = False
    moderator_notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== TEAM SCHEMAS ====================

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    specialization: Optional[str] = Field(None, max_length=200)
    members_count: int = Field(default=0, ge=0, le=50)
    max_concurrent_orders: int = Field(default=5, ge=1, le=20)
    
class TeamCreate(TeamBase):
    supervisor_name: Optional[str] = Field(None, max_length=100)
    supervisor_contact: Optional[str] = Field(None, max_length=200)
    work_areas: Optional[List[str]] = None
    equipment: Optional[List[str]] = None

class TeamUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=500)
    specialization: Optional[str] = Field(None, max_length=200)
    members_count: Optional[int] = Field(None, ge=0, le=50)
    max_concurrent_orders: Optional[int] = Field(None, ge=1, le=20)
    supervisor_name: Optional[str] = Field(None, max_length=100)
    supervisor_contact: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    work_areas: Optional[List[str]] = None
    equipment: Optional[List[str]] = None

class TeamResponse(TeamBase):
    id: int
    supervisor_name: Optional[str] = None
    supervisor_contact: Optional[str] = None
    is_active: bool = True
    current_workload: int = 0
    work_areas: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    performance_rating: Optional[float] = None
    completed_orders: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ==================== REPORT SCHEMAS ====================

class ReportFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_name: Optional[str] = None
    location: Optional[str] = None
    service_type: Optional[str] = None
    status: Optional[ServiceOrderStatus] = None
    priority: Optional[AlertLevel] = None
    category: Optional[ComplaintCategory] = None

class MaintenanceReportResponse(BaseModel):
    report_id: str
    filters: ReportFilters
    summary: Dict[str, Any]
    team_statistics: Dict[str, Dict[str, Any]]
    interventions: List[MaintenanceResponse]
    generated_at: datetime
    generated_by: str

class TeamPerformanceReport(BaseModel):
    team_name: str
    period_start: datetime
    period_end: datetime
    total_orders: int
    completed_orders: int
    average_completion_time: float
    customer_satisfaction: float
    cost_efficiency: float
    performance_score: float

class SystemMetrics(BaseModel):
    total_service_orders: int
    open_orders: int
    in_progress_orders: int
    completed_orders: int
    average_completion_time: float
    total_complaints: int
    resolved_complaints: int
    average_response_time: float
    customer_satisfaction: float
    active_teams: int

# ==================== NOTIFICATION SCHEMAS ====================

class MaintenanceNotification(BaseModel):
    type: str  # "order_created", "order_assigned", "order_completed", etc.
    service_order_id: Optional[int] = None
    complaint_id: Optional[int] = None
    team_name: Optional[str] = None
    message: str
    priority: AlertLevel = AlertLevel.MEDIUM
    recipients: List[str]  # User IDs or roles
    channels: List[str] = ["push", "email"]  # Notification channels

# ==================== SEARCH SCHEMAS ====================

class ServiceOrderSearch(BaseModel):
    query: Optional[str] = None
    status: Optional[List[ServiceOrderStatus]] = None
    priority: Optional[List[AlertLevel]] = None
    team: Optional[str] = None
    location: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 100

class ComplaintSearch(BaseModel):
    query: Optional[str] = None
    status: Optional[List[ComplaintStatus]] = None
    category: Optional[List[ComplaintCategory]] = None
    location: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 100

class MaintenanceSearch(BaseModel):
    query: Optional[str] = None
    team: Optional[str] = None
    work_type: Optional[str] = None
    location: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None
    skip: int = 0
    limit: int = 100