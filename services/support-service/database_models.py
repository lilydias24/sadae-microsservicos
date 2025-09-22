"""
Database models for Support Service
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CLIENT = "waiting_client"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketCategory(str, enum.Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    COMPLAINT = "complaint"
    REQUEST = "request"
    INFORMATION = "information"
    EMERGENCY = "emergency"

class MessageType(str, enum.Enum):
    CLIENT = "client"
    AGENT = "agent"
    SYSTEM = "system"

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(TicketCategory), nullable=False)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN)
    
    # User information
    client_user_id = Column(Integer, nullable=False, index=True)
    client_name = Column(String(100), nullable=False)
    client_email = Column(String(100), nullable=False)
    client_phone = Column(String(20))
    
    # Agent information
    assigned_agent_id = Column(Integer, index=True)
    assigned_agent_name = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    
    # Satisfaction
    satisfaction_rating = Column(Integer)  # 1-5 scale
    satisfaction_comment = Column(Text)
    
    # Related data
    related_bill_id = Column(Integer)
    related_order_id = Column(Integer)
    
    # Relationships
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    message_type = Column(SQLEnum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    
    # Author information
    author_user_id = Column(Integer)
    author_name = Column(String(100), nullable=False)
    author_email = Column(String(100))
    
    # Metadata
    is_internal = Column(Boolean, default=False)  # Internal notes for agents
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("Ticket", back_populates="messages")

class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    uploaded_by_user_id = Column(Integer, nullable=False)
    uploaded_by_name = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("Ticket", back_populates="attachments")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(SQLEnum(TicketCategory), nullable=False)
    tags = Column(String(500))  # Comma-separated tags for search
    
    # SEO and search
    slug = Column(String(250), unique=True, index=True, nullable=False)
    meta_description = Column(String(160))
    keywords = Column(String(500))
    
    # Publishing
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Author information
    created_by_user_id = Column(Integer, nullable=False)
    created_by_name = Column(String(100), nullable=False)
    updated_by_user_id = Column(Integer)
    updated_by_name = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

class SupportAgent(Base):
    __tablename__ = "support_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20))
    
    # Agent settings
    is_active = Column(Boolean, default=True)
    max_concurrent_tickets = Column(Integer, default=10)
    specialties = Column(String(500))  # Comma-separated categories
    
    # Performance metrics
    total_tickets_handled = Column(Integer, default=0)
    average_response_time = Column(Integer, default=0)  # Minutes
    average_resolution_time = Column(Integer, default=0)  # Minutes
    satisfaction_average = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True))

class TicketEscalation(Base):
    __tablename__ = "ticket_escalations"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    
    escalated_from_agent_id = Column(Integer)
    escalated_from_agent_name = Column(String(100))
    escalated_to_agent_id = Column(Integer, nullable=False)
    escalated_to_agent_name = Column(String(100), nullable=False)
    
    reason = Column(Text, nullable=False)
    escalated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("Ticket")

class SupportMetrics(Base):
    __tablename__ = "support_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Daily metrics
    total_tickets = Column(Integer, default=0)
    new_tickets = Column(Integer, default=0)
    resolved_tickets = Column(Integer, default=0)
    closed_tickets = Column(Integer, default=0)
    
    average_response_time = Column(Integer, default=0)  # Minutes
    average_resolution_time = Column(Integer, default=0)  # Minutes
    average_satisfaction = Column(Float, default=0.0)
    
    # Category breakdown
    billing_tickets = Column(Integer, default=0)
    technical_tickets = Column(Integer, default=0)
    complaint_tickets = Column(Integer, default=0)
    emergency_tickets = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())