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
import json

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
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    
    user = verify_token(token)
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
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    ticket = SupportTicket(
        ticket_number=generate_ticket_number(),
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
    if user["role"] == UserRole.CITIZEN:
        query = query.filter(SupportTicket.client_id == user["id"])
    elif user["role"] in [UserRole.MANAGER, UserRole.MANAGER, UserRole.MANAGER]:
        # These roles can see all tickets
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
    """Rate ticket satisfaction"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket não encontrado")
    
    # Only the ticket creator can rate it
    if ticket.client_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    # Can only rate closed or resolved tickets
    if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket deve estar resolvido ou fechado")
    
    ticket.satisfaction_rating = satisfaction_data.satisfaction_rating
    ticket.satisfaction_comment = satisfaction_data.satisfaction_comment
    
    db.commit()
    
    return {"message": "Avaliação registrada com sucesso"}

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

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get dashboard metrics"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    # Only support agents, operators and managers can see dashboard
    if user["role"] not in [UserRole.SUPPORT_AGENT, UserRole.MANAGER, UserRole.MANAGER, UserRole.MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Ticket metrics
    total_tickets = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.OPEN).count()
    in_progress_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.IN_PROGRESS).count()
    resolved_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.RESOLVED).count()
    closed_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.CLOSED).count()
    
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
        setattr(category_metrics, category.value, count)
    
    # Recent tickets
    recent_tickets = db.query(SupportTicket).order_by(desc(SupportTicket.created_at)).limit(10).all()
    
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
    ticket = SupportTicket(
        ticket_number=generate_ticket_number(),
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
