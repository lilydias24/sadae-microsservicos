"""
Support Service Router - Sistema de Atendimento ao Cliente
Gerencia tickets, base de conhecimento e atendimento
"""
import os
import sys
import uuid
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

# Add shared modules to path
sys.path.insert(0, '/app/shared')

# Import shared modules with error handling
try:
    from auth import verify_token
    from utils import UserRole, generate_protocol_number
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    # Create minimal fallbacks for development
    async def verify_token(token):
        return {"id": 1, "name": "Test User", "email": "test@test.com", "role": "citizen"}
    
    class UserRole:
        CITIZEN = "citizen"
        OPERATOR = "operator"
        MANAGER = "manager"
        MAINTENANCE_MANAGER = "maintenance_manager"
        FINANCIAL_MANAGER = "financial_manager"
        CRISIS_MANAGER = "crisis_manager"
        SUPPORT_AGENT = "support_agent"
    
    def generate_protocol_number():
        return f"PROT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

from database import get_db
from database_models import (
    SupportTicket, TicketMessage, KnowledgeBaseArticle, SupportAgent
)
from schemas.support import (
    TicketCreate, TicketUpdate, TicketResponse, TicketAssign, TicketClose, TicketSatisfaction,
    MessageCreate, MessageResponse, AttachmentResponse,
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    SupportAgentCreate, SupportAgentUpdate, SupportAgentResponse,
    EscalationCreate, EscalationResponse,
    TicketMetrics, CategoryMetrics, DashboardMetrics,
    TicketSearch, KnowledgeBaseSearch, BulkTicketUpdate, BulkTicketAssign,
    KnowledgeBaseFeedback, PublicTicketCreate, PublicTicketResponse,
    TicketStatus, TicketPriority, TicketCategory, MessageType
)
from business.ai_support import AISupportAssistant

router = APIRouter()

# Security
security = HTTPBearer()

# ==================== WEBSOCKET CHAT MANAGER ====================

class ChatConnectionManager:
    """Gerenciador de conexões WebSocket para chat de tickets"""
    
    def __init__(self):
        # ticket_id -> List[WebSocket]
        self.active_connections: Dict[int, List[Dict[str, Any]]] = {}
    
    async def connect(self, websocket: WebSocket, ticket_id: int, user_id: int, user_name: str, user_role: str):
        """Conectar WebSocket ao ticket"""
        await websocket.accept()
        
        connection_info = {
            "websocket": websocket,
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "connected_at": datetime.now()
        }
        
        if ticket_id not in self.active_connections:
            self.active_connections[ticket_id] = []
        
        self.active_connections[ticket_id].append(connection_info)
        print(f"✅ WebSocket conectado - Ticket {ticket_id}, User {user_id} ({user_name})")
        print(f"   Total de conexões no ticket: {len(self.active_connections[ticket_id])}")
    
    def disconnect(self, websocket: WebSocket, ticket_id: int):
        """Desconectar WebSocket do ticket"""
        if ticket_id in self.active_connections:
            self.active_connections[ticket_id] = [
                conn for conn in self.active_connections[ticket_id]
                if conn["websocket"] != websocket
            ]
            
            # Remover ticket se não houver mais conexões
            if not self.active_connections[ticket_id]:
                del self.active_connections[ticket_id]
            
            print(f"🔌 WebSocket desconectado - Ticket {ticket_id}")
    
    async def send_to_ticket(self, ticket_id: int, message: dict):
        """Enviar mensagem para todos conectados no ticket"""
        if ticket_id not in self.active_connections:
            return
        
        disconnected = []
        message_json = json.dumps(message)
        
        for conn in self.active_connections[ticket_id]:
            try:
                await conn["websocket"].send_text(message_json)
            except Exception as e:
                print(f"❌ Erro ao enviar mensagem WebSocket: {e}")
                disconnected.append(conn)
        
        # Remover conexões desconectadas
        for conn in disconnected:
            self.disconnect(conn["websocket"], ticket_id)
    
    async def send_to_user(self, ticket_id: int, user_id: int, message: dict):
        """Enviar mensagem para usuário específico no ticket"""
        if ticket_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        
        for conn in self.active_connections[ticket_id]:
            if conn["user_id"] == user_id:
                try:
                    await conn["websocket"].send_text(message_json)
                except Exception as e:
                    print(f"❌ Erro ao enviar mensagem para usuário: {e}")
                    self.disconnect(conn["websocket"], ticket_id)

# Instância global do gerenciador
chat_manager = ChatConnectionManager()

def verify_user_token(token: str) -> dict:
    """Verify JWT token and return user info
    
    Args:
        token: JWT token (without 'Bearer ' prefix) or full 'Bearer token' string
    
    Returns:
        dict with keys: id, name, email, role
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    
    payload = verify_token(token)
    
    # Normalize user data from JWT payload
    user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID do usuário não encontrado no payload"
        )
    
    # Convert to int if it's a string (required for database)
    if isinstance(user_id, str):
        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: ID do usuário não é um número válido: {user_id}"
            )
    
    return {
        "id": int(user_id),  # Ensure it's always an int
        "name": payload.get("name") or payload.get("username") or payload.get("full_name") or "Usuário",
        "email": payload.get("email") or "",
        "role": payload.get("role") or "citizen"
    }

def generate_ticket_number(db: Session) -> str:
    """Generate unique sequential ticket number in format TK001, TK002, etc."""
    # Find all tickets with TK prefix to get the highest number
    tickets_with_tk = db.query(SupportTicket).filter(
        SupportTicket.ticket_number.like('TK%')
    ).all()
    
    max_number = 0
    
    if tickets_with_tk:
        for ticket in tickets_with_tk:
            try:
                # Extract number from formats like TK001, TK002, etc.
                if ticket.ticket_number.startswith("TK"):
                    # Remove "TK" prefix and convert to int
                    number_str = ticket.ticket_number[2:].lstrip('0') or '0'
                    number = int(number_str)
                    max_number = max(max_number, number)
            except (ValueError, AttributeError):
                # Skip tickets with invalid format
                continue
    
    # If no TK tickets found, check if there are any tickets at all
    # and use the highest ID as fallback
    if max_number == 0:
        last_ticket = db.query(SupportTicket).order_by(SupportTicket.id.desc()).first()
        if last_ticket:
            # Use ticket ID as starting point
            max_number = last_ticket.id
    
    # Get next number
    next_number = max_number + 1
    
    # Format as TK001, TK002, etc. (padded to 3 digits minimum, can grow)
    # For numbers > 999, it will be TK1000, TK1001, etc.
    if next_number < 1000:
        return f"TK{next_number:03d}"
    else:
        return f"TK{next_number}"

def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    # Simple slug generation without external dependency
    base_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    base_slug = re.sub(r'\s+', '-', base_slug.strip())
    base_slug = base_slug[:100]  # Max length
    return f"{base_slug}-{uuid.uuid4().hex[:8]}"

# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "support-service",
        "timestamp": datetime.now().isoformat()
    }

# ==================== TICKET MANAGEMENT ====================

@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create new support ticket"""
    try:
        user = verify_user_token(f"Bearer {credentials.credentials}")
        
        print(f"🔍 Creating ticket for user: id={user['id']}, name={user['name']}, email={user['email']}")
        print(f"📦 Ticket data: title={ticket_data.title[:50]}, category={ticket_data.category}, priority={ticket_data.priority}")
        
        # Generate ticket number (needs db session for sequential numbering)
        ticket_number = generate_ticket_number(db)
        print(f"🎫 Generated ticket number: {ticket_number}")
        
        ticket = SupportTicket(
            ticket_number=ticket_number,
            title=ticket_data.title,
            description=ticket_data.description,
            category=ticket_data.category,
            priority=ticket_data.priority,
            client_id=user["id"],
            client_name=user["name"],
            client_email=user["email"],
            client_phone=ticket_data.client_phone,
            related_bill_id=ticket_data.related_bill_id,
            related_order_id=ticket_data.related_order_id
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        print(f"✅ Ticket created: {ticket.ticket_number} (ID: {ticket.id})")
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error creating ticket: {e}")
        print(f"❌ Traceback: {error_trace}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar ticket: {str(e)}"
        )

@router.get("/tickets", response_model=List[TicketResponse])
async def get_tickets(
    status: Optional[TicketStatus] = None,
    category: Optional[TicketCategory] = None,
    priority: Optional[TicketPriority] = None,
    assigned_agent_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get tickets with filters"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    query = db.query(SupportTicket)
    
    # Apply filters based on user role
    user_role = user.get("role", "")
    if user_role == "citizen" or user_role == UserRole.CITIZEN:
        query = query.filter(SupportTicket.client_id == user["id"])
    elif user_role in ["operator", "support_agent"]:
        # Operators and support agents should not see closed tickets in chat
        # Filter out closed tickets unless explicitly requested via status filter
        if status != TicketStatus.CLOSED:
            query = query.filter(SupportTicket.status != TicketStatus.CLOSED)
    elif user_role in ["manager"] or user_role == UserRole.MANAGER:
        # Managers can see all tickets
        pass
    
    # Apply additional filters
    if status:
        query = query.filter(SupportTicket.status == status)
    if category:
        query = query.filter(SupportTicket.category == category)
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    if assigned_agent_id:
        query = query.filter(SupportTicket.assigned_agent_id == assigned_agent_id)
    
    tickets = query.order_by(desc(SupportTicket.created_at)).offset(skip).limit(limit).all()
    return tickets

@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get ticket by ID"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    return ticket

@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update ticket"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_id != user["id"]:
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

@router.post("/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    assign_data: TicketAssign,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Assign ticket to agent"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    # Only operators and managers can assign tickets
    if user["role"] not in [UserRole.MANAGER, UserRole.MANAGER, UserRole.MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
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

@router.post("/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    close_data: TicketClose,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Close ticket with resolution"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN:
        # Citizens can only close their own tickets
        if ticket.client_id != user["id"]:
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

@router.post("/tickets/{ticket_id}/satisfaction")
async def rate_ticket(
    ticket_id: int,
    satisfaction_data: TicketSatisfaction,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Rate ticket satisfaction - only once per ticket"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    # Only citizens can evaluate tickets
    user_role = user.get("role", "")
    if user_role != "citizen" and user_role != UserRole.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Apenas cidadãos podem avaliar atendimentos"
        )
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Only the ticket creator can rate it
    if ticket.client_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    # Can only rate closed or resolved tickets
    if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket deve estar resolvido ou fechado")
    
    # Check if ticket already has a rating (only allow one evaluation per ticket)
    if ticket.satisfaction_rating is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Este ticket já foi avaliado. Cada ticket só pode ser avaliado uma vez."
        )
    
    ticket.satisfaction_rating = satisfaction_data.satisfaction_rating
    ticket.satisfaction_comment = satisfaction_data.satisfaction_comment
    
    db.commit()
    db.refresh(ticket)
    
    return {
        "message": "Avaliação registrada com sucesso",
        "satisfaction_rating": ticket.satisfaction_rating,
        "satisfaction_comment": ticket.satisfaction_comment
    }

# ==================== TICKET MESSAGES ====================

@router.get("/tickets/{ticket_id}/messages", response_model=List[MessageResponse])
async def get_ticket_messages(
    ticket_id: int,
    include_internal: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get ticket messages"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    query = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id)
    
    # Citizens cannot see internal messages
    if user["role"] == UserRole.CITIZEN or not include_internal:
        query = query.filter(TicketMessage.is_internal == False)
    
    messages = query.order_by(TicketMessage.created_at).all()
    return messages

async def generate_ai_response_async(
    ticket_id: int,
    user_message: str,
    db: Session
):
    """Generate and save AI response asynchronously"""
    try:
        # Get fresh database session
        from database import SessionLocal
        db_session = SessionLocal()
        
        try:
            ticket = db_session.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
            if not ticket:
                return
            
            # Get knowledge base articles
            kb_articles = db_session.query(KnowledgeBaseArticle).filter(
                KnowledgeBaseArticle.is_published == True
            ).all()
            
            # Convert to dict format for AI assistant
            kb_data = []
            for article in kb_articles:
                kb_data.append({
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'category': article.category,
                    'tags': article.tags.split(',') if article.tags else [],
                    'keywords': article.keywords.split(',') if article.keywords else [],
                    'is_published': article.is_published,
                    'is_featured': article.is_featured
                })
            
            # Get conversation history
            messages = db_session.query(TicketMessage).filter(
                TicketMessage.ticket_id == ticket_id
            ).order_by(TicketMessage.created_at).all()
            
            conversation_history = []
            for msg in messages:
                conversation_history.append({
                    'message_type': msg.message_type,
                    'content': msg.content,
                    'author_name': msg.author_name,
                    'created_at': msg.created_at.isoformat()
                })
            
            # Prepare ticket context
            ticket_context = {
                'id': ticket.id,
                'title': ticket.title,
                'description': ticket.description,
                'category': ticket.category,
                'priority': ticket.priority,
                'status': ticket.status
            }
            
            # Initialize AI assistant
            ai_assistant = AISupportAssistant()
            
            # Generate AI response
            ai_response = ai_assistant.generate_response(
                user_message=user_message,
                ticket_context=ticket_context,
                knowledge_base=kb_data,
                conversation_history=conversation_history
            )
            
            # Log para debug
            confidence = ai_response.get('confidence', 0)
            should_escalate = ai_assistant.should_escalate_to_agent(
                user_message,
                confidence,
                conversation_history
            )
            
            print(f"🤖 IA Response - Ticket {ticket_id}: confidence={confidence:.2f}, should_escalate={should_escalate}, has_response={bool(ai_response.get('response'))}")
            
            # Only send AI response if confidence is high enough and should not escalate
            # Reduzido threshold para 0.3 para ser mais permissivo
            if (ai_response.get('response') and 
                confidence >= 0.3 and
                not should_escalate):
                
                # Create AI response message
                ai_message = TicketMessage(
                    ticket_id=ticket_id,
                    message_type=MessageType.AGENT,
                    content=ai_response.get('response'),
                    author_user_id=None,  # System/AI
                    author_name="Assistente Virtual",
                    author_email=None,
                    is_internal=False
                )
                
                db_session.add(ai_message)
                
                # Update ticket status
                if ticket.status == TicketStatus.OPEN:
                    ticket.status = TicketStatus.IN_PROGRESS
                
                db_session.commit()
                db_session.refresh(ai_message)
                
                # Enviar resposta da IA via WebSocket
                await chat_manager.send_to_ticket(ticket_id, {
                    "type": "new_message",
                    "data": {
                        "id": ai_message.id,
                        "ticket_id": ticket_id,
                        "message_type": ai_message.message_type,
                        "content": ai_message.content,
                        "author_user_id": ai_message.author_user_id,
                        "author_name": ai_message.author_name,
                        "author_email": ai_message.author_email,
                        "is_internal": ai_message.is_internal,
                        "created_at": ai_message.created_at.isoformat()
                    }
                })
                
                print(f"✅ IA Response sent for ticket {ticket_id}")
            else:
                # Low confidence or should escalate - still try to send a helpful response
                if ai_response.get('response') and confidence >= 0.2:
                    # Send response even with low confidence, but mark it
                    ai_message = TicketMessage(
                        ticket_id=ticket_id,
                        message_type=MessageType.AGENT,
                        content=f"{ai_response.get('response')}\n\n*Se precisar de mais ajuda, nossa equipe entrará em contato em breve.*",
                        author_user_id=None,
                        author_name="Assistente Virtual",
                        author_email=None,
                        is_internal=False
                    )
                    db_session.add(ai_message)
                    db_session.commit()
                    db_session.refresh(ai_message)
                    
                    # Enviar resposta da IA via WebSocket
                    await chat_manager.send_to_ticket(ticket_id, {
                        "type": "new_message",
                        "data": {
                            "id": ai_message.id,
                            "ticket_id": ticket_id,
                            "message_type": ai_message.message_type,
                            "content": ai_message.content,
                            "author_user_id": ai_message.author_user_id,
                            "author_name": ai_message.author_name,
                            "author_email": ai_message.author_email,
                            "is_internal": ai_message.is_internal,
                            "created_at": ai_message.created_at.isoformat()
                        }
                    })
                    
                    print(f"⚠️ IA Response sent with low confidence ({confidence:.2f}) for ticket {ticket_id}")
                else:
                    # Very low confidence - notify that agent will respond
                    escalation_message = TicketMessage(
                        ticket_id=ticket_id,
                        message_type=MessageType.SYSTEM,
                        content="Sua mensagem foi recebida. Nossa equipe de atendimento entrará em contato em breve.",
                        author_user_id=None,
                        author_name="Sistema",
                        author_email=None,
                        is_internal=False
                    )
                    db_session.add(escalation_message)
                    db_session.commit()
                    db_session.refresh(escalation_message)
                    
                    # Enviar mensagem de escalação via WebSocket
                    await chat_manager.send_to_ticket(ticket_id, {
                        "type": "new_message",
                        "data": {
                            "id": escalation_message.id,
                            "ticket_id": ticket_id,
                            "message_type": escalation_message.message_type,
                            "content": escalation_message.content,
                            "author_user_id": escalation_message.author_user_id,
                            "author_name": escalation_message.author_name,
                            "author_email": escalation_message.author_email,
                            "is_internal": escalation_message.is_internal,
                            "created_at": escalation_message.created_at.isoformat()
                        }
                    })
                    
                    print(f"📞 Escalated to agent for ticket {ticket_id} (confidence too low: {confidence:.2f})")
                
        finally:
            db_session.close()
    except Exception as e:
        print(f"Error generating AI response: {e}")
        import traceback
        traceback.print_exc()

@router.post("/tickets/{ticket_id}/messages", response_model=MessageResponse)
async def create_ticket_message(
    ticket_id: int,
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Add message to ticket"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_id != user["id"]:
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
    
    # Enviar mensagem via WebSocket para todos conectados no ticket
    await chat_manager.send_to_ticket(ticket_id, {
        "type": "new_message",
        "data": {
            "id": message.id,
            "ticket_id": ticket_id,
            "message_type": message.message_type,
            "content": message.content,
            "author_user_id": message.author_user_id,
            "author_name": message.author_name,
            "author_email": message.author_email,
            "is_internal": message.is_internal,
            "created_at": message.created_at.isoformat()
        }
    })
    
    # If message is from a client, trigger AI response in background
    if message_type == MessageType.CLIENT and not message_data.is_internal:
        background_tasks.add_task(
            generate_ai_response_async,
            ticket_id,
            message_data.content,
            db
        )
    
    return message

# ==================== WEBSOCKET CHAT ENDPOINT ====================

@router.websocket("/tickets/{ticket_id}/ws")
async def chat_websocket(websocket: WebSocket, ticket_id: int):
    """WebSocket endpoint para chat em tempo real do ticket"""
    # Obter token da query string ou headers
    token = None
    query_params = websocket.query_params
    
    if "token" in query_params:
        token = query_params["token"]
    else:
        # Tentar obter do header Authorization
        headers = dict(websocket.headers)
        auth_header = headers.get("authorization") or headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        await websocket.close(code=1008, reason="Token não fornecido")
        return
    
    try:
        # Verificar token e obter usuário
        user = await verify_token(token)
        user_id = user.get("id")
        user_name = user.get("name", "Usuário")
        user_role = user.get("role", "citizen")
        
        # Verificar se ticket existe e usuário tem acesso
        from database import SessionLocal
        db = SessionLocal()
        try:
            ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
            if not ticket:
                await websocket.close(code=1008, reason="Ticket não encontrado")
                return
            
            # Verificar permissões
            if user_role == UserRole.CITIZEN and ticket.client_id != user_id:
                await websocket.close(code=1008, reason="Acesso negado")
                return
            
            # Conectar ao chat manager
            await chat_manager.connect(websocket, ticket_id, user_id, user_name, user_role)
            
            # Enviar mensagem de confirmação
            await websocket.send_text(json.dumps({
                "type": "connected",
                "data": {
                    "ticket_id": ticket_id,
                    "user_id": user_id,
                    "user_name": user_name,
                    "message": "Conectado ao chat"
                }
            }))
            
            # Loop principal: receber e processar mensagens
            while True:
                try:
                    # Receber mensagem do cliente
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Processar diferentes tipos de mensagem
                    if message_data.get("type") == "ping":
                        # Responder ping para manter conexão viva
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    elif message_data.get("type") == "typing":
                        # Indicador de digitação - enviar para outros participantes
                        await chat_manager.send_to_ticket(ticket_id, {
                            "type": "typing",
                            "data": {
                                "user_id": user_id,
                                "user_name": user_name,
                                "is_typing": message_data.get("is_typing", False)
                            }
                        })
                    elif message_data.get("type") == "message":
                        # Criar mensagem via endpoint HTTP (que já envia via WebSocket)
                        # Isso garante que a mensagem seja salva no DB
                        from fastapi import Request
                        # Nota: Não podemos chamar endpoint HTTP diretamente aqui
                        # Então vamos criar a mensagem diretamente e enviar via WS
                        message = TicketMessage(
                            ticket_id=ticket_id,
                            message_type=MessageType.CLIENT if user_role == UserRole.CITIZEN else MessageType.AGENT,
                            content=message_data.get("content", ""),
                            author_user_id=user_id,
                            author_name=user_name,
                            author_email=user.get("email"),
                            is_internal=False
                        )
                        db.add(message)
                        db.commit()
                        db.refresh(message)
                        
                        # Enviar via WebSocket
                        await chat_manager.send_to_ticket(ticket_id, {
                            "type": "new_message",
                            "data": {
                                "id": message.id,
                                "ticket_id": ticket_id,
                                "message_type": message.message_type,
                                "content": message.content,
                                "author_user_id": message.author_user_id,
                                "author_name": message.author_name,
                                "author_email": message.author_email,
                                "is_internal": message.is_internal,
                                "created_at": message.created_at.isoformat()
                            }
                        })
                        
                        # Se for mensagem de cliente, disparar resposta da IA
                        if user_role == UserRole.CITIZEN:
                            from fastapi import BackgroundTasks
                            background_tasks = BackgroundTasks()
                            background_tasks.add_task(
                                generate_ai_response_async,
                                ticket_id,
                                message_data.get("content", ""),
                                db
                            )
                            # Executar em background (simplificado)
                            import asyncio
                            asyncio.create_task(generate_ai_response_async(
                                ticket_id,
                                message_data.get("content", ""),
                                db
                            ))
                
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"message": "Formato de mensagem inválido"}
                    }))
                except Exception as e:
                    print(f"❌ Erro ao processar mensagem WebSocket: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"message": "Erro ao processar mensagem"}
                    }))
        
        finally:
            db.close()
    
    except Exception as e:
        print(f"❌ Erro na conexão WebSocket: {e}")
        try:
            await websocket.close(code=1011, reason="Erro interno")
        except:
            pass
    finally:
        # Desconectar do manager
        chat_manager.disconnect(websocket, ticket_id)

# ==================== AI SUPPORT ====================

@router.post("/tickets/{ticket_id}/ai-suggest")
async def get_ai_suggestion(
    ticket_id: int,
    message_data: MessageCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get AI-generated response suggestion for a message"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Check permissions
    if user["role"] == UserRole.CITIZEN and ticket.client_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    # Get knowledge base articles
    kb_articles = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.is_published == True
    ).all()
    
    # Convert to dict format for AI assistant
    kb_data = []
    for article in kb_articles:
        kb_data.append({
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'category': article.category,
            'tags': article.tags.split(',') if article.tags else [],
            'keywords': article.keywords.split(',') if article.keywords else [],
            'is_published': article.is_published,
            'is_featured': article.is_featured
        })
    
    # Get conversation history
    messages = db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket_id
    ).order_by(TicketMessage.created_at).all()
    
    conversation_history = []
    for msg in messages:
        conversation_history.append({
            'message_type': msg.message_type,
            'content': msg.content,
            'author_name': msg.author_name,
            'created_at': msg.created_at.isoformat()
        })
    
    # Prepare ticket context
    ticket_context = {
        'id': ticket.id,
        'title': ticket.title,
        'description': ticket.description,
        'category': ticket.category,
        'priority': ticket.priority,
        'status': ticket.status
    }
    
    # Initialize AI assistant
    ai_assistant = AISupportAssistant()
    
    # Generate AI response
    ai_response = ai_assistant.generate_response(
        user_message=message_data.content,
        ticket_context=ticket_context,
        knowledge_base=kb_data,
        conversation_history=conversation_history
    )
    
    return {
        'suggestion': ai_response.get('response'),
        'confidence': ai_response.get('confidence', 0.0),
        'relevant_articles': ai_response.get('relevant_articles', []),
        'suggestions': ai_response.get('suggestions', []),
        'should_escalate': ai_assistant.should_escalate_to_agent(
            message_data.content,
            ai_response.get('confidence', 0.0),
            conversation_history
        )
    }

# ==================== KNOWLEDGE BASE ====================

@router.get("/knowledge-base", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_base(
    category: Optional[TicketCategory] = None,
    featured: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get published knowledge base articles"""
    query = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.is_published == True)
    
    if category:
        query = query.filter(KnowledgeBaseArticle.category == category)
    if featured is not None:
        query = query.filter(KnowledgeBaseArticle.is_featured == featured)
    if search:
        search_filter = or_(
            KnowledgeBaseArticle.title.ilike(f"%{search}%"),
            KnowledgeBaseArticle.content.ilike(f"%{search}%"),
            KnowledgeBaseArticle.tags.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    articles = query.order_by(
        desc(KnowledgeBaseArticle.is_featured),
        desc(KnowledgeBaseArticle.view_count)
    ).offset(skip).limit(limit).all()
    
    return articles

@router.get("/knowledge-base/{article_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """Get knowledge base article by ID"""
    article = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.id == article_id,
        KnowledgeBaseArticle.is_published == True
    ).first()
    
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado")
    
    # Increment view count
    article.view_count += 1
    db.commit()
    
    return article

@router.post("/knowledge-base", response_model=KnowledgeBaseResponse)
async def create_knowledge_article(
    article_data: KnowledgeBaseCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create knowledge base article"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    # Only operators and managers can create articles
    if user["role"] not in [UserRole.MANAGER, UserRole.MANAGER, UserRole.MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    article = KnowledgeBaseArticle(
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

@router.post("/knowledge-base/{article_id}/feedback")
async def rate_knowledge_article(
    article_id: int,
    feedback: KnowledgeBaseFeedback,
    db: Session = Depends(get_db)
):
    """Rate knowledge base article helpfulness"""
    article = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artigo não encontrado")
    
    if feedback.is_helpful:
        article.helpful_count += 1
    else:
        article.not_helpful_count += 1
    
    db.commit()
    
    return {"message": "Feedback registrado com sucesso"}

# ==================== DASHBOARD & METRICS ====================

@router.get("/dashboard")
async def get_dashboard_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get dashboard metrics"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    # Only support agents, operators and managers can see dashboard
    user_role = user.get("role", "")
    allowed_roles = ["support_agent", "operator", "manager"]
    if user_role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Ticket metrics
    total_tickets = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "open").count()
    in_progress_tickets = db.query(SupportTicket).filter(SupportTicket.status == "in_progress").count()
    resolved_tickets = db.query(SupportTicket).filter(SupportTicket.status == "resolved").count()
    closed_tickets = db.query(SupportTicket).filter(SupportTicket.status == "closed").count()
    
    # Average times (in hours)
    avg_response = db.query(func.avg(
        func.extract('epoch', SupportTicket.updated_at - SupportTicket.created_at) / 3600
    )).filter(SupportTicket.updated_at.isnot(None)).scalar() or 0
    
    avg_resolution = db.query(func.avg(
        func.extract('epoch', SupportTicket.resolved_at - SupportTicket.created_at) / 3600
    )).filter(SupportTicket.resolved_at.isnot(None)).scalar() or 0
    
    # Satisfaction average
    satisfaction_avg = db.query(func.avg(SupportTicket.satisfaction_rating)).filter(
        SupportTicket.satisfaction_rating.isnot(None)
    ).scalar() or 0
    
    # Category metrics
    category_counts = db.query(
        SupportTicket.category, func.count(SupportTicket.id)
    ).group_by(SupportTicket.category).all()
    
    category_metrics = CategoryMetrics(
        billing=0, technical=0, complaint=0, request=0, information=0, emergency=0
    )
    for category, count in category_counts:
        category_str = str(category)
        if hasattr(category_metrics, category_str):
            setattr(category_metrics, category_str, count)
    
    # Priority metrics - Calculate tickets by priority
    priority_counts = db.query(
        SupportTicket.priority, func.count(SupportTicket.id)
    ).group_by(SupportTicket.priority).all()
    
    # Tickets by agent/attendant - Calculate tickets assigned to each agent
    agent_ticket_counts = db.query(
        SupportTicket.assigned_agent_id,
        SupportTicket.assigned_agent_name,
        func.count(SupportTicket.id).label('ticket_count')
    ).filter(
        SupportTicket.assigned_agent_id.isnot(None)
    ).group_by(
        SupportTicket.assigned_agent_id,
        SupportTicket.assigned_agent_name
    ).order_by(
        func.count(SupportTicket.id).desc()
    ).all()
    
    # Calculate tickets by status for each agent
    agent_stats = []
    for agent_id, agent_name, total_count in agent_ticket_counts:
        agent_tickets = db.query(SupportTicket).filter(
            SupportTicket.assigned_agent_id == agent_id
        ).all()
        
        open_count = len([t for t in agent_tickets if str(t.status) == "open"])
        in_progress_count = len([t for t in agent_tickets if str(t.status) == "in_progress"])
        resolved_count = len([t for t in agent_tickets if str(t.status) == "resolved"])
        closed_count = len([t for t in agent_tickets if str(t.status) == "closed"])
        
        # Calculate average resolution time for this agent
        agent_resolved_tickets = [t for t in agent_tickets if t.resolved_at and t.created_at]
        agent_avg_resolution = 0
        if agent_resolved_tickets:
            total_hours = sum([
                (t.resolved_at - t.created_at).total_seconds() / 3600 
                for t in agent_resolved_tickets
            ])
            agent_avg_resolution = total_hours / len(agent_resolved_tickets)
        
        agent_stats.append({
            "agent_id": agent_id,
            "agent_name": agent_name or "Não atribuído",
            "total_tickets": total_count,
            "open_tickets": open_count,
            "in_progress_tickets": in_progress_count,
            "resolved_tickets": resolved_count,
            "closed_tickets": closed_count,
            "average_resolution_time": round(agent_avg_resolution, 2)
        })
    
    # Recent tickets
    recent_tickets = db.query(SupportTicket).order_by(desc(SupportTicket.created_at)).limit(10).all()
    
    # Top agents (by satisfaction)
    top_agents = db.query(SupportAgent).order_by(
        desc(SupportAgent.satisfaction_average)
    ).limit(5).all()
    
    return {
        "ticket_metrics": {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "closed_tickets": closed_tickets,
            "average_response_time": round(float(avg_response or 0), 2),
            "average_resolution_time": round(float(avg_resolution or 0), 2),
            "satisfaction_average": round(float(satisfaction_avg or 0), 2)
        },
        "category_metrics": {
            "billing": category_metrics.billing,
            "technical": category_metrics.technical,
            "complaint": category_metrics.complaint,
            "request": category_metrics.request,
            "information": category_metrics.information,
            "emergency": category_metrics.emergency
        },
        "priority_metrics": {
            str(priority): int(count) for priority, count in priority_counts
        },
        "tickets_by_agent": agent_stats,
        "recent_tickets": [
            {
                "id": t.id,
                "ticket_number": t.ticket_number,
                "title": t.title,
                "status": str(t.status),
                "priority": str(t.priority),
                "category": str(t.category),
                "client_name": t.client_name,
                "assigned_agent_name": t.assigned_agent_name,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in recent_tickets
        ],
        "top_agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "email": agent.email,
                "satisfaction_average": float(agent.satisfaction_average or 0),
                "total_tickets_handled": agent.total_tickets_handled or 0,
                "average_response_time": agent.average_response_time or 0
            }
            for agent in top_agents
        ]
    }

@router.get("/agent-dashboard")
async def get_agent_dashboard_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get dashboard metrics specifically for support agents"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    # Only support agents can access this endpoint
    if user["role"] != UserRole.SUPPORT_AGENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a atendentes")
    
    agent_id = user["id"]
    
    # Get agent's tickets
    agent_tickets = db.query(SupportTicket).filter(SupportTicket.assigned_agent_id == agent_id).all()
    
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
    recent_assigned = db.query(SupportTicket).filter(
        SupportTicket.assigned_agent_id == agent_id
    ).order_by(desc(SupportTicket.created_at)).limit(10).all()
    
    # Pending tickets (unassigned or high priority)
    pending_tickets = db.query(SupportTicket).filter(
        or_(
            SupportTicket.assigned_agent_id.is_(None),
            and_(SupportTicket.priority == TicketPriority.URGENT, SupportTicket.status != TicketStatus.RESOLVED)
        )
    ).order_by(desc(SupportTicket.priority), SupportTicket.created_at).limit(15).all()
    
    # Today's statistics
    today = datetime.now().date()
    today_tickets = db.query(SupportTicket).filter(
        func.date(SupportTicket.created_at) == today
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

@router.post("/public/tickets", response_model=PublicTicketResponse)
async def create_public_ticket(
    ticket_data: PublicTicketCreate,
    db: Session = Depends(get_db)
):
    """Create ticket without authentication (for public portal)"""
    # Generate ticket number (needs db session for sequential numbering)
    ticket_number = generate_ticket_number(db)
    
    ticket = SupportTicket(
        ticket_number=ticket_number,
        title=ticket_data.title,
        description=ticket_data.description,
        category=ticket_data.category,
        client_id=0,  # No user ID for public tickets
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

@router.get("/public/tickets/{ticket_number}", response_model=PublicTicketResponse)
async def get_public_ticket(
    ticket_number: str,
    db: Session = Depends(get_db)
):
    """Get public ticket status"""
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_number == ticket_number).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    return PublicTicketResponse(
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at
    )

# ==================== REPORTS ====================

class SupportReportFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[int] = None

@router.post("/reports/support")
async def generate_support_report(
    filters: SupportReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Generate support tickets report"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    # Check permissions - support agents, operators and managers can generate reports
    user_role = user.get("role", "")
    allowed_roles = ["support_agent", "operator", "manager"]
    # Also check string values in case UserRole is not available
    allowed_role_strings = ["support_agent", "operator", "manager"]
    if user_role not in allowed_roles and user_role not in allowed_role_strings:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Validate period
    if filters.start_date and filters.end_date:
        period_days = (filters.end_date - filters.start_date).days
        if period_days < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A data de início deve ser anterior à data de fim"
            )
    
    # Query tickets
    query = db.query(SupportTicket)
    
    if filters.start_date:
        query = query.filter(SupportTicket.created_at >= filters.start_date)
    if filters.end_date:
        query = query.filter(SupportTicket.created_at <= filters.end_date)
    if filters.status:
        query = query.filter(SupportTicket.status == filters.status)
    if filters.category:
        query = query.filter(SupportTicket.category == filters.category)
    if filters.priority:
        query = query.filter(SupportTicket.priority == filters.priority)
    if filters.assigned_agent_id:
        query = query.filter(SupportTicket.assigned_agent_id == filters.assigned_agent_id)
    
    tickets = query.order_by(desc(SupportTicket.created_at)).all()
    
    # Calculate statistics
    total_tickets = len(tickets)
    
    # Status breakdown
    status_breakdown = {}
    for ticket in tickets:
        status_key = ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status)
        if status_key not in status_breakdown:
            status_breakdown[status_key] = {"count": 0}
        status_breakdown[status_key]["count"] += 1
    
    # Category breakdown
    category_breakdown = {}
    for ticket in tickets:
        category_key = ticket.category.value if hasattr(ticket.category, 'value') else str(ticket.category)
        if category_key not in category_breakdown:
            category_breakdown[category_key] = {"count": 0}
        category_breakdown[category_key]["count"] += 1
    
    # Priority breakdown
    priority_breakdown = {}
    for ticket in tickets:
        priority_key = ticket.priority.value if hasattr(ticket.priority, 'value') else str(ticket.priority)
        if priority_key not in priority_breakdown:
            priority_breakdown[priority_key] = {"count": 0}
        priority_breakdown[priority_key]["count"] += 1
    
    # Average response and resolution times
    total_response_time = 0
    total_resolution_time = 0
    tickets_with_response = 0
    tickets_with_resolution = 0
    
    # Agent statistics
    agent_stats = {}
    
    for ticket in tickets:
        # Response time calculation (time to first update/message)
        if ticket.updated_at and ticket.created_at:
            response_time = (ticket.updated_at - ticket.created_at).total_seconds() / 3600
            total_response_time += response_time
            tickets_with_response += 1
        
        # Resolution time calculation
        if ticket.resolved_at and ticket.created_at:
            resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            total_resolution_time += resolution_time
            tickets_with_resolution += 1
        
        # Agent statistics
        if ticket.assigned_agent_id:
            agent_id = ticket.assigned_agent_id
            agent_name = ticket.assigned_agent_name or f"Agente {agent_id}"
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "agent_name": agent_name,
                    "total_tickets": 0,
                    "resolved_tickets": 0,
                    "total_resolution_time": 0,
                    "total_response_time": 0,
                    "tickets_with_response": 0
                }
            agent_stats[agent_id]["total_tickets"] += 1
            if ticket.resolved_at:
                agent_stats[agent_id]["resolved_tickets"] += 1
                if ticket.created_at:
                    resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                    agent_stats[agent_id]["total_resolution_time"] += resolution_time
            if ticket.updated_at and ticket.created_at:
                response_time = (ticket.updated_at - ticket.created_at).total_seconds() / 3600
                agent_stats[agent_id]["total_response_time"] += response_time
                agent_stats[agent_id]["tickets_with_response"] += 1
    
    # Calculate averages for agents
    for agent_id, stats in agent_stats.items():
        if stats["total_tickets"] > 0:
            stats["resolution_rate"] = round((stats["resolved_tickets"] / stats["total_tickets"]) * 100, 2)
            if stats["resolved_tickets"] > 0:
                stats["avg_resolution_time"] = round(stats["total_resolution_time"] / stats["resolved_tickets"], 2)
            else:
                stats["avg_resolution_time"] = 0
            if stats["tickets_with_response"] > 0:
                stats["avg_response_time"] = round(stats["total_response_time"] / stats["tickets_with_response"], 2)
            else:
                stats["avg_response_time"] = 0
    
    avg_response_time = total_response_time / tickets_with_response if tickets_with_response > 0 else 0
    avg_resolution_time = total_resolution_time / tickets_with_resolution if tickets_with_resolution > 0 else 0
    
    # Resolution rate
    resolved_tickets = sum(1 for t in tickets if t.resolved_at is not None or str(t.status).lower() == 'resolved')
    resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
    
    # Satisfaction average
    satisfaction_ratings = [t.satisfaction_rating for t in tickets if t.satisfaction_rating is not None]
    avg_satisfaction = sum(satisfaction_ratings) / len(satisfaction_ratings) if satisfaction_ratings else 0
    
    # Tickets by day (for trend analysis)
    tickets_by_day = {}
    for ticket in tickets:
        day_key = ticket.created_at.date().isoformat() if ticket.created_at else None
        if day_key:
            if day_key not in tickets_by_day:
                tickets_by_day[day_key] = 0
            tickets_by_day[day_key] += 1
    
    report_id = generate_protocol_number()
    
    return {
        "report_id": report_id,
        "filters": filters.dict(),
        "summary": {
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "resolution_rate": round(resolution_rate, 2),
            "status_breakdown": status_breakdown,
            "category_breakdown": category_breakdown,
            "priority_breakdown": priority_breakdown,
            "average_response_time_hours": round(avg_response_time, 2),
            "average_resolution_time_hours": round(avg_resolution_time, 2),
            "average_satisfaction": round(avg_satisfaction, 2),
            "agent_statistics": agent_stats,
            "tickets_by_day": tickets_by_day,
            "period": {
                "start": filters.start_date.isoformat() if filters.start_date else None,
                "end": filters.end_date.isoformat() if filters.end_date else None
            }
        },
        "tickets": [
            {
                "id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "category": str(ticket.category) if ticket.category else None,
                "priority": str(ticket.priority) if ticket.priority else None,
                "status": str(ticket.status) if ticket.status else None,
                "client_name": ticket.client_name,
                "assigned_agent_id": ticket.assigned_agent_id,
                "created_at": ticket.created_at.isoformat(),
                "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
                "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                "satisfaction_rating": ticket.satisfaction_rating
            }
            for ticket in tickets[:1000]  # Limit to 1000 for performance
        ],
        "generated_at": datetime.now().isoformat(),
        "generated_by": user.get("name", "Unknown")
    }
