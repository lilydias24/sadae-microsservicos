"""
Pydantic schemas for Support Service
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CLIENT = "waiting_client"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FORWARDED = "forwarded"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    COMPLAINT = "complaint"
    REQUEST = "request"
    INFORMATION = "information"
    EMERGENCY = "emergency"

class ForwardDepartment(str, Enum):
    MAINTENANCE = "maintenance"
    BILLING = "billing"
    MONITORING = "monitoring"

class MessageType(str, Enum):
    CLIENT = "client"
    AGENT = "agent"
    SYSTEM = "system"

# Ticket schemas
class TicketBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category: TicketCategory
    priority: TicketPriority = TicketPriority.MEDIUM
    client_phone: Optional[str] = None
    related_bill_id: Optional[int] = None
    related_order_id: Optional[int] = None

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_agent_id: Optional[int] = None
    client_phone: Optional[str] = None

class TicketAssign(BaseModel):
    assigned_agent_id: int

class TicketClose(BaseModel):
    resolution_note: str = Field(..., min_length=10, max_length=1000)

class TicketSatisfaction(BaseModel):
    satisfaction_rating: int = Field(..., ge=1, le=5)
    satisfaction_comment: Optional[str] = Field(None, max_length=1000)

# Ticket Forwarding schemas
class TicketForward(BaseModel):
    department: ForwardDepartment
    reason: str = Field(..., min_length=10, max_length=1000)
    location: Optional[str] = Field(None, max_length=200)  # Required for maintenance
    additional_notes: Optional[str] = Field(None, max_length=2000)

class TicketForwardResponse(BaseModel):
    ticket_id: int
    ticket_number: str
    forwarded_to: ForwardDepartment
    forwarded_at: datetime
    service_order_id: Optional[int] = None  # If forwarded to maintenance
    service_order_protocol: Optional[str] = None
    bill_contest_id: Optional[int] = None  # If forwarded to billing
    message: str

    class Config:
        from_attributes = True

class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    client_user_id: int
    client_name: str
    client_email: str
    client_phone: Optional[str]
    assigned_agent_id: Optional[int]
    assigned_agent_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    satisfaction_rating: Optional[int]
    satisfaction_comment: Optional[str]
    related_bill_id: Optional[int]
    related_order_id: Optional[int]
    # Forwarding fields
    forwarded_to_department: Optional[str] = None
    forwarded_at: Optional[datetime] = None
    forwarded_by_name: Optional[str] = None
    forwarded_service_order_id: Optional[int] = None
    forwarded_bill_contest_id: Optional[int] = None
    # Escalation fields
    escalation_level: int = 0
    sla_deadline: Optional[datetime] = None
    last_escalation_at: Optional[datetime] = None
    escalation_reason: Optional[str] = None

    class Config:
        from_attributes = True

# Message schemas
class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    is_internal: bool = False

class MessageCreate(MessageBase):
    pass

class MessageResponse(BaseModel):
    id: int
    ticket_id: int
    message_type: MessageType
    content: str
    author_user_id: Optional[int]
    author_name: str
    author_email: Optional[str]
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Attachment schemas
class AttachmentResponse(BaseModel):
    id: int
    ticket_id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    uploaded_by_user_id: int
    uploaded_by_name: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Knowledge Base schemas
class KnowledgeBaseBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=50)
    category: TicketCategory
    tags: Optional[str] = None
    meta_description: Optional[str] = Field(None, max_length=160)
    keywords: Optional[str] = Field(None, max_length=500)
    is_published: bool = True
    is_featured: bool = False

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    content: Optional[str] = Field(None, min_length=50)
    category: Optional[TicketCategory] = None
    tags: Optional[str] = None
    meta_description: Optional[str] = Field(None, max_length=160)
    keywords: Optional[str] = Field(None, max_length=500)
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    title: str
    content: str
    category: TicketCategory
    tags: Optional[str]
    slug: str
    meta_description: Optional[str]
    keywords: Optional[str]
    is_published: bool
    is_featured: bool
    view_count: int
    helpful_count: int
    not_helpful_count: int
    created_by_user_id: int
    created_by_name: str
    updated_by_user_id: Optional[int]
    updated_by_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]

    class Config:
        from_attributes = True

# Support Agent schemas
class SupportAgentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool = True
    max_concurrent_tickets: int = Field(10, ge=1, le=50)
    specialties: Optional[str] = None

class SupportAgentCreate(SupportAgentBase):
    user_id: int

class SupportAgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    max_concurrent_tickets: Optional[int] = Field(None, ge=1, le=50)
    specialties: Optional[str] = None

class SupportAgentResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    phone: Optional[str]
    is_active: bool
    max_concurrent_tickets: int
    specialties: Optional[str]
    total_tickets_handled: int
    average_response_time: int
    average_resolution_time: int
    satisfaction_average: float
    created_at: datetime
    updated_at: Optional[datetime]
    last_active_at: Optional[datetime]

    class Config:
        from_attributes = True

# Escalation schemas
class EscalationCreate(BaseModel):
    escalated_to_agent_id: int
    reason: str = Field(..., min_length=10, max_length=1000)

class EscalationResponse(BaseModel):
    id: int
    ticket_id: int
    escalated_from_agent_id: Optional[int]
    escalated_from_agent_name: Optional[str]
    escalated_to_agent_id: int
    escalated_to_agent_name: str
    reason: str
    escalated_at: datetime

    class Config:
        from_attributes = True

# Dashboard and metrics schemas
class TicketMetrics(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    average_response_time: float  # hours
    average_resolution_time: float  # hours
    satisfaction_average: float

class CategoryMetrics(BaseModel):
    billing: int
    technical: int
    complaint: int
    request: int
    information: int
    emergency: int

class DashboardMetrics(BaseModel):
    ticket_metrics: TicketMetrics
    category_metrics: CategoryMetrics
    recent_tickets: List[TicketResponse]
    top_agents: List[SupportAgentResponse]

# Search and filter schemas
class TicketSearch(BaseModel):
    query: Optional[str] = None
    status: Optional[List[TicketStatus]] = None
    category: Optional[List[TicketCategory]] = None
    priority: Optional[List[TicketPriority]] = None
    assigned_agent_id: Optional[int] = None
    client_user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class KnowledgeBaseSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[TicketCategory] = None
    tags: Optional[List[str]] = None
    is_featured: Optional[bool] = None

# Bulk operations
class BulkTicketUpdate(BaseModel):
    ticket_ids: List[int] = Field(..., min_items=1)
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent_id: Optional[int] = None

class BulkTicketAssign(BaseModel):
    ticket_ids: List[int] = Field(..., min_items=1)
    assigned_agent_id: int

# Feedback schemas
class KnowledgeBaseFeedback(BaseModel):
    is_helpful: bool

# Public schemas (for non-authenticated users)
class PublicTicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category: TicketCategory
    client_name: str = Field(..., min_length=2, max_length=100)
    client_email: EmailStr
    client_phone: Optional[str] = None

class PublicTicketResponse(BaseModel):
    ticket_number: str
    title: str
    status: TicketStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True