from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import sys
import os

# Adicionar o diretório shared ao path
sys.path.append('/app/shared')
from database import Base

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # billing, technical, complaint, request, information, emergency
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, urgent
    status = Column(String(30), nullable=False, default="open")  # open, in_progress, waiting_client, resolved, closed
    client_id = Column(Integer, nullable=False)
    client_name = Column(String(100), nullable=False)
    client_email = Column(String(100), nullable=False)
    assigned_agent_id = Column(Integer, nullable=True)
    assigned_agent_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 stars
    
    # Relationships
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    message_type = Column(String(20), nullable=False)  # client, agent, system
    content = Column(Text, nullable=False)
    author_id = Column(Integer, nullable=True)
    author_name = Column(String(100), nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal notes for agents
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="messages")

class KnowledgeBaseArticle(Base):
    __tablename__ = "knowledge_base_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    author_id = Column(Integer, nullable=False)
    author_name = Column(String(100), nullable=False)
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SupportAgent(Base):
    __tablename__ = "support_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)
    specialties = Column(String(200), nullable=True)  # JSON array of specialties
    is_active = Column(Boolean, default=True)
    max_concurrent_tickets = Column(Integer, default=10)
    current_ticket_count = Column(Integer, default=0)
    total_tickets_resolved = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)  # in hours
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)