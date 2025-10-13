"""
Maintenance Service Router - Sistema de Manutenção e Serviços Públicos
Gerencia ordens de serviço, manutenções, reclamações e equipes
"""
import os
import sys
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session

# Add shared modules to path
sys.path.insert(0, '/app/shared')

# Import shared modules with error handling
try:
    from auth import verify_token
    from utils import UserRole, generate_protocol_number
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    # Create minimal fallbacks for development
    def verify_token(token):
        return {"id": 1, "name": "Test User", "email": "test@test.com", "role": "maintenance_manager"}
    
    class UserRole:
        CITIZEN = "citizen"
        OPERATOR = "operator"
        MAINTENANCE_MANAGER = "maintenance_manager"
        FINANCIAL_MANAGER = "financial_manager"
        CRISIS_MANAGER = "crisis_manager"
        SUPPORT_AGENT = "support_agent"
    
    def generate_protocol_number():
        return f"PROT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

from database import get_db
from database_models import (
    ServiceOrder, Maintenance, Complaint, ServiceEvaluation, Team
)
from schemas.maintenance import (
    ServiceOrderCreate, ServiceOrderResponse, ServiceOrderUpdate, ServiceOrderAssign, ServiceOrderProgress,
    MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate,
    ComplaintCreate, ComplaintResponse, ComplaintUpdate, PublicComplaintCreate, PublicComplaintResponse,
    ServiceEvaluationCreate, ServiceEvaluationResponse,
    TeamCreate, TeamResponse, TeamUpdate,
    ReportFilters, MaintenanceReportResponse, TeamPerformanceReport, SystemMetrics,
    ServiceOrderSearch, ComplaintSearch, MaintenanceSearch,
    ServiceOrderStatus, AlertLevel, ComplaintCategory, ComplaintStatus
)

# 🔗 Chain of Responsibility - Importar cadeia de processamento
try:
    from business.maintenance_chain import (
        create_standard_service_order_chain,
        create_emergency_only_chain,
        ServiceOrderRequest,
        ServiceOrderType as ChainServiceOrderType
    )
    CHAIN_ENABLED = True
    print("✅ Chain of Responsibility habilitado para Maintenance")
except ImportError as e:
    print(f"⚠️ Chain of Responsibility não disponível: {e}")
    CHAIN_ENABLED = False

router = APIRouter()

# Security
security = HTTPBearer()

# 🔗 Inicializar cadeias de processamento
if CHAIN_ENABLED:
    service_order_chain = create_standard_service_order_chain()
    emergency_chain = create_emergency_only_chain()

async def verify_user_token(authorization: str) -> dict:
    """Verify JWT token and return user info"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    token = authorization.split(" ")[1]
    user = verify_token(token)  
    return user

# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "maintenance-service",
        "timestamp": datetime.now().isoformat()
    }

# ==================== SERVICE ORDER MANAGEMENT ====================

@router.post("/orders", response_model=ServiceOrderResponse)
async def create_service_order(
    order_data: ServiceOrderCreate,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    🔗 Create service order with Chain of Responsibility processing
    
    A cadeia processa automaticamente:
    - Classificação por tipo (emergência tem prioridade)
    - Avaliação de urgência e prioridade
    - Alocação de equipe adequada
    - Estimativa de recursos (tempo, materiais, custo)
    - Auto-aprovação baseada em regras de negócio
    """
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if user["role"] != UserRole.MAINTENANCE_MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas gerentes de manutenção podem criar ordens de serviço"
        )
    
    # 🔗 CHAIN OF RESPONSIBILITY - Processamento automático da ordem
    processing_result = None
    order_number = generate_protocol_number()
    
    if CHAIN_ENABLED:
        try:
            # Mapear tipo de ordem para enum da cadeia
            type_map = {
                "preventive": ChainServiceOrderType.PREVENTIVE,
                "corrective": ChainServiceOrderType.CORRECTIVE,
                "emergency": ChainServiceOrderType.EMERGENCY,
                "installation": ChainServiceOrderType.INSTALLATION,
                "inspection": ChainServiceOrderType.INSPECTION,
                "meter_reading": ChainServiceOrderType.METER_READING,
                "meter_replacement": ChainServiceOrderType.METER_REPLACEMENT,
                "network_expansion": ChainServiceOrderType.NETWORK_EXPANSION
            }
            order_type = type_map.get(order_data.order_type, ChainServiceOrderType.CORRECTIVE)
            
            # Criar requisição para a cadeia
            chain_request = ServiceOrderRequest(
                order_type=order_type,
                description=order_data.description,
                location=order_data.location,
                latitude=order_data.latitude,
                longitude=order_data.longitude,
                reported_issue=order_data.description,
                affects_water_supply=getattr(order_data, 'affects_water_supply', False),
                affects_multiple_customers=getattr(order_data, 'affects_multiple_customers', False),
                estimated_affected_customers=getattr(order_data, 'estimated_affected_customers', 0),
                has_safety_risk=getattr(order_data, 'has_safety_risk', False),
                requires_street_closure=getattr(order_data, 'requires_street_closure', False),
                requires_special_equipment=getattr(order_data, 'requires_special_equipment', False)
            )
            
            # Processar na cadeia
            processing_result = service_order_chain.handle(chain_request)
            order_number = processing_result.data['order_number']
            
            print(f"🔗 Chain processing - Order: {order_number}, Priority: {processing_result.data['priority']}, Approved: {processing_result.data['approved']}")
            
        except Exception as e:
            print(f"⚠️ Erro no processamento da cadeia: {e}")
            # Em caso de erro, continua com processamento manual
    
    protocol_number = order_number
    
    # Usar dados processados pela cadeia ou valores padrão
    if processing_result and processing_result.success:
        # Dados da cadeia
        assigned_team = processing_result.data.get('assigned_team')
        estimated_cost = processing_result.data.get('estimated_cost', 0)
        estimated_duration = processing_result.data.get('estimated_duration_hours', 0)
        max_response_time = processing_result.data.get('max_response_time_hours', 24)
        auto_approved = processing_result.data.get('approved', False)
        processing_notes = processing_result.data.get('notes', [])
        
        # Mapear prioridade da cadeia para o modelo
        chain_priority = processing_result.data.get('priority', 'medium')
        priority_map = {
            'critical': AlertLevel.CRITICAL,
            'urgent': AlertLevel.HIGH,
            'high': AlertLevel.HIGH,
            'medium': AlertLevel.MEDIUM,
            'low': AlertLevel.LOW
        }
        calculated_priority = priority_map.get(chain_priority, AlertLevel.MEDIUM)
    else:
        # Valores padrão
        assigned_team = None
        estimated_cost = 0
        estimated_duration = 0
        max_response_time = 24
        auto_approved = False
        processing_notes = []
        calculated_priority = order_data.priority
    
    service_order = ServiceOrder(
        title=order_data.title,
        description=order_data.description,
        priority=calculated_priority,
        location=order_data.location,
        anomaly_id=order_data.anomaly_id,
        protocol_number=protocol_number,
        created_by=user["id"],
        created_by_name=user["name"],
        status=ServiceOrderStatus.OPEN if not auto_approved else ServiceOrderStatus.ASSIGNED,
        assigned_team=assigned_team,
        estimated_cost=estimated_cost,
        estimated_duration_hours=estimated_duration
    )
    
    # Adicionar notas de processamento
    if processing_notes:
        service_order.notes = "\n".join([f"🔗 {note}" for note in processing_notes])
    
    db.add(service_order)
    db.commit()
    db.refresh(service_order)
    
    # Send notification to available teams
    if assigned_team:
        background_tasks.add_task(notify_specific_team, service_order, assigned_team)
    else:
        background_tasks.add_task(notify_available_teams, service_order)
    
    return service_order

@router.get("/orders", response_model=List[ServiceOrderResponse])
async def get_service_orders(
    status: Optional[ServiceOrderStatus] = None,
    priority: Optional[AlertLevel] = None,
    team: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get service orders with filters"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    query = db.query(ServiceOrder)
    
    # Apply user role filters
    if user["role"] == UserRole.CITIZEN:
        query = query.filter(ServiceOrder.created_by == user["id"])
    
    # Apply filters
    if status:
        query = query.filter(ServiceOrder.status == status)
    if priority:
        query = query.filter(ServiceOrder.priority == priority)
    if team:
        query = query.filter(ServiceOrder.assigned_team == team)
    
    orders = query.order_by(desc(ServiceOrder.created_at)).offset(skip).limit(limit).all()
    return orders

@router.get("/orders/{order_id}", response_model=ServiceOrderResponse)
async def get_service_order(
    order_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get service order by ID"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordem de serviço não encontrada")
    
    # Citizens can only see their own orders
    if user["role"] == UserRole.CITIZEN and order.created_by != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    
    return order

@router.put("/orders/{order_id}", response_model=ServiceOrderResponse)
async def update_service_order(
    order_id: int,
    order_update: ServiceOrderUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update service order"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if user["role"] not in [UserRole.MAINTENANCE_MANAGER, UserRole.OPERATOR]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordem de serviço não encontrada")
    
    # Update fields
    for field, value in order_update.dict(exclude_unset=True).items():
        setattr(order, field, value)
    
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    
    return order

# ==================== MAINTENANCE MANAGEMENT ====================

@router.post("/maintenances", response_model=MaintenanceResponse)
async def register_maintenance(
    maintenance_data: MaintenanceCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Register completed maintenance"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if user["role"] not in [UserRole.MAINTENANCE_MANAGER, UserRole.OPERATOR]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    maintenance = Maintenance(
        service_order_id=maintenance_data.service_order_id,
        title=maintenance_data.title,
        description=maintenance_data.description,
        team_name=maintenance_data.team_name,
        location=maintenance_data.location,
        completion_date=maintenance_data.completion_date,
        duration_hours=maintenance_data.duration_hours,
        cost=maintenance_data.cost,
        materials_used=maintenance_data.materials_used,
        equipment_used=maintenance_data.equipment_used,
        work_type=maintenance_data.work_type,
        registered_by=user["id"],
        registered_by_name=user["name"]
    )
    
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    
    return maintenance

@router.get("/maintenances", response_model=List[MaintenanceResponse])
async def get_maintenances(
    team: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get maintenance records"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    query = db.query(Maintenance)
    
    if team:
        query = query.filter(Maintenance.team_name == team)
    
    maintenances = query.order_by(desc(Maintenance.completion_date)).offset(skip).limit(limit).all()
    return maintenances

# ==================== COMPLAINT MANAGEMENT ====================

@router.post("/public/complaints", response_model=PublicComplaintResponse)
async def create_public_complaint(
    complaint_data: PublicComplaintCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create public complaint (no authentication required)"""
    
    protocol_number = generate_protocol_number()
    
    complaint = Complaint(
        title=complaint_data.title,
        description=complaint_data.description,
        category=complaint_data.category,
        location=complaint_data.location,
        citizen_name=complaint_data.citizen_name,
        citizen_contact=complaint_data.citizen_contact,
        citizen_email=complaint_data.citizen_email,
        protocol_number=protocol_number,
        status=ComplaintStatus.PENDING
    )
    
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    
    # Create service order if needed for urgent categories
    if complaint.category in [ComplaintCategory.WATER_LEAK, ComplaintCategory.INFRASTRUCTURE]:
        background_tasks.add_task(create_service_order_from_complaint, complaint)
    
    return PublicComplaintResponse(
        protocol_number=complaint.protocol_number,
        title=complaint.title,
        status=complaint.status,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at
    )

@router.get("/public/complaints/{protocol_number}")
async def get_public_complaint_status(
    protocol_number: str,
    db: Session = Depends(get_db)
):
    """Get complaint status by protocol number"""
    
    complaint = db.query(Complaint).filter(Complaint.protocol_number == protocol_number).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reclamação não encontrada")
    
    return PublicComplaintResponse(
        protocol_number=complaint.protocol_number,
        title=complaint.title,
        status=complaint.status,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at
    )

@router.get("/complaints", response_model=List[ComplaintResponse])
async def get_complaints(
    status: Optional[ComplaintStatus] = None,
    category: Optional[ComplaintCategory] = None,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get complaints (staff only)"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if user["role"] not in [UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    query = db.query(Complaint)
    
    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    
    complaints = query.order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()
    return complaints

# ==================== TEAM MANAGEMENT ====================

@router.post("/teams", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create maintenance team"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if user["role"] != UserRole.MAINTENANCE_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Check if team name already exists
    existing = db.query(Team).filter(Team.name == team_data.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nome da equipe já existe")
    
    team = Team(
        name=team_data.name,
        description=team_data.description,
        specialization=team_data.specialization,
        members_count=team_data.members_count,
        max_concurrent_orders=team_data.max_concurrent_orders,
        supervisor_name=team_data.supervisor_name,
        supervisor_contact=team_data.supervisor_contact,
        work_areas=team_data.work_areas,
        equipment=team_data.equipment
    )
    
    db.add(team)
    db.commit()
    db.refresh(team)
    
    return team

@router.get("/teams", response_model=List[TeamResponse])
async def get_teams(
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get maintenance teams"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    query = db.query(Team)
    if active_only:
        query = query.filter(Team.is_active == True)
    
    teams = query.offset(skip).limit(limit).all()
    
    # Calculate current workload for each team
    for team in teams:
        current_workload = db.query(ServiceOrder).filter(
            ServiceOrder.assigned_team == team.name,
            ServiceOrder.status.in_([ServiceOrderStatus.ASSIGNED, ServiceOrderStatus.IN_PROGRESS])
        ).count()
        team.current_workload = current_workload
    
    return teams

# ==================== DASHBOARD & METRICS ====================

@router.get("/dashboard")
async def get_maintenance_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get maintenance dashboard metrics"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if user["role"] not in [UserRole.MAINTENANCE_MANAGER, UserRole.OPERATOR]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Basic metrics for dashboard
    total_orders = db.query(ServiceOrder).count()
    open_orders = db.query(ServiceOrder).filter(ServiceOrder.status == ServiceOrderStatus.OPEN).count()
    in_progress_orders = db.query(ServiceOrder).filter(ServiceOrder.status == ServiceOrderStatus.IN_PROGRESS).count()
    completed_orders = db.query(ServiceOrder).filter(ServiceOrder.status == ServiceOrderStatus.COMPLETED).count()
    active_teams = db.query(Team).filter(Team.is_active == True).count()
    pending_complaints = db.query(Complaint).filter(Complaint.status == ComplaintStatus.PENDING).count()
    
    # Recent orders
    recent_orders = db.query(ServiceOrder).order_by(desc(ServiceOrder.created_at)).limit(10).all()
    
    return {
        "total_orders": total_orders,
        "open_orders": open_orders,
        "in_progress_orders": in_progress_orders,
        "completed_orders": completed_orders,
        "active_teams": active_teams,
        "pending_complaints": pending_complaints,
        "recent_orders": [
            {
                "id": order.id,
                "title": order.title,
                "status": order.status.value,
                "priority": order.priority.value,
                "created_at": order.created_at.isoformat()
            } for order in recent_orders
        ]
    }

# ==================== BACKGROUND TASKS ====================

async def notify_available_teams(service_order: ServiceOrder):
    """Notify available teams about new service order"""
    try:
        print(f"Notifying teams about new service order: {service_order.protocol_number}")
        # This would typically send notifications to team mobile apps or email
        # Implementation would depend on notification service
    except Exception as e:
        print(f"Error sending team notification: {e}")

async def notify_specific_team(service_order: ServiceOrder, team_name: str):
    """🔗 Notify specific team assigned by Chain of Responsibility"""
    try:
        print(f"🔗 Notifying team '{team_name}' about new service order: {service_order.protocol_number}")
        print(f"   Priority: {service_order.priority}")
        print(f"   Estimated duration: {service_order.estimated_duration_hours}h")
        print(f"   Estimated cost: R$ {service_order.estimated_cost:.2f}")
        # TODO: Integrar com notification_chain para envio multi-canal
        # from notification_chain import create_full_notification_chain, NotificationRequest
    except Exception as e:
        print(f"Error sending team notification: {e}")

async def send_status_notification(service_order: ServiceOrder, user: dict):
    """Send notification about status change"""
    try:
        print(f"Sending status notification for order {service_order.protocol_number}: {service_order.status}")
        # Implementation would depend on notification service
    except Exception as e:
        print(f"Error sending status notification: {e}")

async def create_service_order_from_complaint(complaint: Complaint):
    """Create service order from urgent complaint"""
    try:
        print(f"Creating service order from complaint: {complaint.protocol_number}")
        # Implementation would create service order automatically
    except Exception as e:
        print(f"Error creating service order from complaint: {e}")