"""
Support Service - Sistema de Atendimento ao Cliente
Gerencia tickets, base de conhecimento e atendimento
"""
import os
import sys
import uuid
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, and_, or_, desc, func, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import httpx
import json
import re

# Add shared modules to path
sys.path.insert(0, '/app/shared')

# Import shared modules with error handling
try:
    from auth import verify_token
    from utils import UserRole
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    # Create minimal fallbacks for development
    async def verify_token(token):
        return {"id": 1, "name": "Test User", "email": "test@test.com", "role": "citizen"}
    
    class UserRole:
        CITIZEN = "citizen"
        OPERATOR = "operator"
        MAINTENANCE_MANAGER = "maintenance_manager"
        FINANCIAL_MANAGER = "financial_manager"
        CRISIS_MANAGER = "crisis_manager"
        SUPPORT_AGENT = "support_agent"

# Local imports
from database_models import (
    Base, Ticket, TicketMessage, TicketAttachment, KnowledgeBase, 
    SupportAgent, TicketEscalation, SupportMetrics,
    TicketStatus, TicketPriority, TicketCategory, MessageType
)
from schemas import (
    TicketCreate, TicketUpdate, TicketResponse, TicketAssign, TicketClose, TicketSatisfaction,
    MessageCreate, MessageResponse, AttachmentResponse,
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    SupportAgentCreate, SupportAgentUpdate, SupportAgentResponse,
    EscalationCreate, EscalationResponse,
    TicketMetrics, CategoryMetrics, DashboardMetrics,
    TicketSearch, KnowledgeBaseSearch, BulkTicketUpdate, BulkTicketAssign,
    KnowledgeBaseFeedback, PublicTicketCreate, PublicTicketResponse
)

# Database setup
DATABASE_URL = os.getenv("SUPPORT_DATABASE_URL", "postgresql://sadae_user:sadae_password_2024@postgres:5432/support_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Support Service",
    description="Sistema de Atendimento ao Cliente - SADAE",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # URL do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_user_token(authorization: str) -> dict:
    """Verify JWT token and return user info"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    token = authorization.split(" ")[1]
    user = await verify_token(token)
    return user

def generate_ticket_number() -> str:
    """Generate unique ticket number"""
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4()).split('-')[0].upper()
    return f"SUP-{timestamp}-{unique_id}"

def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    # Simple slug generation without external dependency
    base_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    base_slug = re.sub(r'\s+', '-', base_slug.strip())
    base_slug = base_slug[:100]  # Max length
    return f"{base_slug}-{uuid.uuid4().hex[:8]}"

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "support-service",
        "timestamp": datetime.now().isoformat()
    }

# ==================== TICKET MANAGEMENT ====================

@app.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create new support ticket"""
    user = await verify_user_token(authorization)
    
    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        title=ticket_data.title,
        description=ticket_data.description,
        category=ticket_data.category,
        priority=ticket_data.priority,
        client_user_id=user["id"],
        client_name=user["name"],
        client_email=user["email"],
        client_phone=ticket_data.client_phone,
        related_bill_id=ticket_data.related_bill_id,
        related_order_id=ticket_data.related_order_id
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    # Create initial system message
    system_message = TicketMessage(
        ticket_id=ticket.id,
        message_type=MessageType.SYSTEM,
        content=f"Ticket #{ticket.ticket_number} criado por {user['name']}",
        author_user_id=user["id"],
        author_name="Sistema",
        is_internal=False
    )
    db.add(system_message)
    db.commit()
    
    return ticket

@app.get("/tickets", response_model=List[TicketResponse])
async def get_tickets(
    status: Optional[TicketStatus] = None,
    category: Optional[TicketCategory] = None,
    priority: Optional[TicketPriority] = None,
    assigned_agent_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get tickets with filters"""
    user = await verify_user_token(authorization)
    
    query = db.query(Ticket)
    
    # Apply filters based on user role
    if user["role"] == UserRole.CITIZEN:
        query = query.filter(Ticket.client_user_id == user["id"])
    elif user["role"] in [UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER, UserRole.FINANCIAL_MANAGER]:
        # These roles can see all tickets
        pass
    
    # Apply additional filters
    if status:
        query = query.filter(Ticket.status == status)
    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if assigned_agent_id:
        query = query.filter(Ticket.assigned_agent_id == assigned_agent_id)
    
    tickets = query.order_by(desc(Ticket.created_at)).offset(skip).limit(limit).all()
    return tickets

@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get ticket by ID"""
    user = await verify_user_token(authorization)
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_user_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    return ticket

@app.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Update ticket"""
    user = await verify_user_token(authorization)
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_user_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    # Citizens can only update certain fields
    if user["role"] == UserRole.CITIZEN:
        allowed_fields = ["title", "description", "client_phone"]
        update_data = {k: v for k, v in ticket_data.dict(exclude_unset=True).items() if k in allowed_fields}
    else:
        update_data = ticket_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(ticket, field, value)
    
    # Update timestamps based on status changes
    if ticket_data.status:
        if ticket_data.status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.now()
        elif ticket_data.status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.now()
    
    db.commit()
    db.refresh(ticket)
    
    return ticket

@app.post("/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    assign_data: TicketAssign,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Assign ticket to agent"""
    user = await verify_user_token(authorization)
    
    # Only operators and managers can assign tickets
    if user["role"] not in [UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER, UserRole.FINANCIAL_MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Get agent info
    agent = db.query(SupportAgent).filter(SupportAgent.user_id == assign_data.assigned_agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente não encontrado")
    
    ticket.assigned_agent_id = agent.user_id
    ticket.assigned_agent_name = agent.name
    ticket.status = TicketStatus.IN_PROGRESS
    
    # Create assignment message
    message = TicketMessage(
        ticket_id=ticket.id,
        message_type=MessageType.SYSTEM,
        content=f"Ticket atribuído para {agent.name}",
        author_user_id=user["id"],
        author_name=user["name"],
        is_internal=True
    )
    db.add(message)
    
    db.commit()
    
    return {"message": "Ticket atribuído com sucesso"}

@app.post("/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    close_data: TicketClose,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Close ticket with resolution"""
    user = await verify_user_token(authorization)
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN:
        # Citizens can only close their own tickets
        if ticket.client_user_id != user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = datetime.now()
    if not ticket.resolved_at:
        ticket.resolved_at = datetime.now()
    
    # Create resolution message
    message = TicketMessage(
        ticket_id=ticket.id,
        message_type=MessageType.AGENT if user["role"] != UserRole.CITIZEN else MessageType.CLIENT,
        content=close_data.resolution_note,
        author_user_id=user["id"],
        author_name=user["name"],
        is_internal=False
    )
    db.add(message)
    
    db.commit()
    
    return {"message": "Ticket fechado com sucesso"}

@app.post("/tickets/{ticket_id}/satisfaction")
async def rate_ticket(
    ticket_id: int,
    satisfaction_data: TicketSatisfaction,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Rate ticket satisfaction"""
    user = await verify_user_token(authorization)
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Only the ticket creator can rate it
    if ticket.client_user_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    # Can only rate closed or resolved tickets
    if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket deve estar resolvido ou fechado")
    
    ticket.satisfaction_rating = satisfaction_data.satisfaction_rating
    ticket.satisfaction_comment = satisfaction_data.satisfaction_comment
    
    db.commit()
    
    return {"message": "Avaliação registrada com sucesso"}

# ==================== TICKET MESSAGES ====================

@app.get("/tickets/{ticket_id}/messages", response_model=List[MessageResponse])
async def get_ticket_messages(
    ticket_id: int,
    include_internal: bool = False,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get ticket messages"""
    user = await verify_user_token(authorization)
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_user_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    query = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id)
    
    # Citizens cannot see internal messages
    if user["role"] == UserRole.CITIZEN or not include_internal:
        query = query.filter(TicketMessage.is_internal == False)
    
    messages = query.order_by(TicketMessage.created_at).all()
    return messages

@app.post("/tickets/{ticket_id}/messages", response_model=MessageResponse)
async def create_ticket_message(
    ticket_id: int,
    message_data: MessageCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Add message to ticket"""
    user = await verify_user_token(authorization)
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_user_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    # Determine message type
    if user["role"] == UserRole.CITIZEN:
        message_type = MessageType.CLIENT
        # Citizens cannot create internal messages
        message_data.is_internal = False
    else:
        message_type = MessageType.AGENT
    
    message = TicketMessage(
        ticket_id=ticket_id,
        message_type=message_type,
        content=message_data.content,
        author_user_id=user["id"],
        author_name=user["name"],
        author_email=user.get("email"),
        is_internal=message_data.is_internal
    )
    
    db.add(message)
    
    # Update ticket status if needed
    if message_type == MessageType.CLIENT and ticket.status == TicketStatus.WAITING_CLIENT:
        ticket.status = TicketStatus.IN_PROGRESS
    elif message_type == MessageType.AGENT and ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    
    db.commit()
    db.refresh(message)
    
    return message

# ==================== KNOWLEDGE BASE ====================

@app.get("/knowledge-base", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_base(
    category: Optional[TicketCategory] = None,
    featured: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Get published knowledge base articles"""
    query = db.query(KnowledgeBase).filter(KnowledgeBase.is_published == True)
    
    if category:
        query = query.filter(KnowledgeBase.category == category)
    if featured is not None:
        query = query.filter(KnowledgeBase.is_featured == featured)
    if search:
        search_filter = or_(
            KnowledgeBase.title.ilike(f"%{search}%"),
            KnowledgeBase.content.ilike(f"%{search}%"),
            KnowledgeBase.tags.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    articles = query.order_by(
        desc(KnowledgeBase.is_featured),
        desc(KnowledgeBase.view_count)
    ).offset(skip).limit(limit).all()
    
    return articles

@app.get("/knowledge-base/{article_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_article(
    article_id: int,
    db: Session = Depends(get_db_session)
):
    """Get knowledge base article by ID"""
    article = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == article_id,
        KnowledgeBase.is_published == True
    ).first()
    
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado")
    
    # Increment view count
    article.view_count += 1
    db.commit()
    
    return article

@app.post("/knowledge-base", response_model=KnowledgeBaseResponse)
async def create_knowledge_article(
    article_data: KnowledgeBaseCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create knowledge base article"""
    user = await verify_user_token(authorization)
    
    # Only operators and managers can create articles
    if user["role"] not in [UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER, UserRole.FINANCIAL_MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    article = KnowledgeBase(
        title=article_data.title,
        content=article_data.content,
        category=article_data.category,
        tags=article_data.tags,
        slug=generate_slug(article_data.title),
        meta_description=article_data.meta_description,
        keywords=article_data.keywords,
        is_published=article_data.is_published,
        is_featured=article_data.is_featured,
        created_by_user_id=user["id"],
        created_by_name=user["name"],
        published_at=datetime.now() if article_data.is_published else None
    )
    
    db.add(article)
    db.commit()
    db.refresh(article)
    
    return article

@app.post("/knowledge-base/{article_id}/feedback")
async def rate_knowledge_article(
    article_id: int,
    feedback: KnowledgeBaseFeedback,
    db: Session = Depends(get_db_session)
):
    """Rate knowledge base article helpfulness"""
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado")
    
    if feedback.is_helpful:
        article.helpful_count += 1
    else:
        article.not_helpful_count += 1
    
    db.commit()
    
    return {"message": "Feedback registrado com sucesso"}

# ==================== DASHBOARD & METRICS ====================

@app.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get dashboard metrics"""
    user = await verify_user_token(authorization)
    
    # Only support agents, operators and managers can see dashboard
    if user["role"] not in [UserRole.SUPPORT_AGENT, UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER, UserRole.FINANCIAL_MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Ticket metrics
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.OPEN).count()
    in_progress_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.IN_PROGRESS).count()
    resolved_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.RESOLVED).count()
    closed_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.CLOSED).count()
    
    # Average times (in hours)
    avg_response = db.query(func.avg(
        func.extract('epoch', Ticket.updated_at - Ticket.created_at) / 3600
    )).filter(Ticket.updated_at.isnot(None)).scalar() or 0
    
    avg_resolution = db.query(func.avg(
        func.extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600
    )).filter(Ticket.resolved_at.isnot(None)).scalar() or 0
    
    # Satisfaction average
    satisfaction_avg = db.query(func.avg(Ticket.satisfaction_rating)).filter(
        Ticket.satisfaction_rating.isnot(None)
    ).scalar() or 0
    
    # Category metrics
    category_counts = db.query(
        Ticket.category, func.count(Ticket.id)
    ).group_by(Ticket.category).all()
    
    category_metrics = CategoryMetrics(
        billing=0, technical=0, complaint=0, request=0, information=0, emergency=0
    )
    for category, count in category_counts:
        setattr(category_metrics, category.value, count)
    
    # Recent tickets
    recent_tickets = db.query(Ticket).order_by(desc(Ticket.created_at)).limit(10).all()
    
    # Top agents
    top_agents = db.query(SupportAgent).order_by(
        desc(SupportAgent.satisfaction_average)
    ).limit(5).all()
    
    return DashboardMetrics(
        ticket_metrics=TicketMetrics(
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            in_progress_tickets=in_progress_tickets,
            resolved_tickets=resolved_tickets,
            closed_tickets=closed_tickets,
            average_response_time=avg_response,
            average_resolution_time=avg_resolution,
            satisfaction_average=satisfaction_avg
        ),
        category_metrics=category_metrics,
        recent_tickets=recent_tickets,
        top_agents=top_agents
    )

@app.get("/agent-dashboard")
async def get_agent_dashboard_metrics(
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get dashboard metrics specifically for support agents"""
    user = await verify_user_token(authorization)
    
    # Only support agents can access this endpoint
    if user["role"] != UserRole.SUPPORT_AGENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a atendentes")
    
    agent_id = user["id"]
    
    # Get agent's tickets
    agent_tickets = db.query(Ticket).filter(Ticket.assigned_agent_id == agent_id).all()
    
    # Agent-specific metrics
    total_assigned = len(agent_tickets)
    open_assigned = len([t for t in agent_tickets if t.status == TicketStatus.OPEN])
    in_progress_assigned = len([t for t in agent_tickets if t.status == TicketStatus.IN_PROGRESS])
    resolved_today = len([t for t in agent_tickets if t.status == TicketStatus.RESOLVED and 
                         t.updated_at and t.updated_at.date() == datetime.now().date()])
    
    # Agent's performance metrics
    agent_record = db.query(SupportAgent).filter(SupportAgent.user_id == agent_id).first()
    if not agent_record:
        agent_record = SupportAgent(
            user_id=agent_id,
            name=user["name"],
            email=user.get("email", ""),
            department="support",
            is_active=True
        )
        db.add(agent_record)
        db.commit()
    
    # Recent tickets assigned to agent
    recent_assigned = db.query(Ticket).filter(
        Ticket.assigned_agent_id == agent_id
    ).order_by(desc(Ticket.created_at)).limit(10).all()
    
    # Pending tickets (unassigned or high priority)
    pending_tickets = db.query(Ticket).filter(
        or_(
            Ticket.assigned_agent_id.is_(None),
            and_(Ticket.priority == TicketPriority.URGENT, Ticket.status != TicketStatus.RESOLVED)
        )
    ).order_by(desc(Ticket.priority), Ticket.created_at).limit(15).all()
    
    # Today's statistics
    today = datetime.now().date()
    today_tickets = db.query(Ticket).filter(
        func.date(Ticket.created_at) == today
    ).count()
    
    return {
        "agent_info": {
            "name": user["name"],
            "satisfaction_rating": agent_record.satisfaction_average or 0.0,
            "total_resolved": agent_record.tickets_resolved or 0,
            "average_response_time": agent_record.average_response_time or 0.0
        },
        "my_tickets": {
            "total_assigned": total_assigned,
            "open": open_assigned,
            "in_progress": in_progress_assigned,
            "resolved_today": resolved_today
        },
        "daily_stats": {
            "new_tickets_today": today_tickets,
            "pending_assignment": len([t for t in pending_tickets if t.assigned_agent_id is None])
        },
        "recent_assigned": [
            {
                "id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "priority": ticket.priority.value,
                "status": ticket.status.value,
                "client_name": ticket.client_name,
                "created_at": ticket.created_at.isoformat()
            } for ticket in recent_assigned
        ],
        "pending_tickets": [
            {
                "id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "priority": ticket.priority.value,
                "status": ticket.status.value,
                "client_name": ticket.client_name,
                "created_at": ticket.created_at.isoformat(),
                "assigned_agent_id": ticket.assigned_agent_id
            } for ticket in pending_tickets
        ]
    }

# ==================== PUBLIC ENDPOINTS ====================

@app.post("/public/tickets", response_model=PublicTicketResponse)
async def create_public_ticket(
    ticket_data: PublicTicketCreate,
    db: Session = Depends(get_db_session)
):
    """Create ticket without authentication (for public portal)"""
    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        title=ticket_data.title,
        description=ticket_data.description,
        category=ticket_data.category,
        client_user_id=0,  # No user ID for public tickets
        client_name=ticket_data.client_name,
        client_email=ticket_data.client_email,
        client_phone=ticket_data.client_phone
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return PublicTicketResponse(
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )

@app.get("/public/tickets/{ticket_number}", response_model=PublicTicketResponse)
async def get_public_ticket(
    ticket_number: str,
    db: Session = Depends(get_db_session)
):
    """Get public ticket status"""
    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    return PublicTicketResponse(
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)