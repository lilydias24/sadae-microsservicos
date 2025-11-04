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

# Add shared modules to path (use append to keep local imports priority)
sys.path.append('/app/shared')

# Import shared modules with error handling
try:
    from auth import verify_token
    try:
        from models import UserRole
    except ImportError:
        from utils import UserRole
    from utils import generate_protocol_number
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
    ServiceOrder, Maintenance, Complaint, ServiceEvaluation, Team, TeamMember, ServiceOrderProgress
)
from schemas.maintenance import (
    ServiceOrderCreate, ServiceOrderResponse, ServiceOrderUpdate, ServiceOrderAssign, ServiceOrderProgress as ServiceOrderProgressSchema,
    MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate, ServiceOrderProgressResponse,
    ComplaintCreate, ComplaintResponse, ComplaintUpdate, PublicComplaintCreate, PublicComplaintResponse,
    ServiceEvaluationCreate, ServiceEvaluationResponse,
    TeamCreate, TeamResponse, TeamUpdate, TeamMemberCreate, TeamMemberResponse, TeamMemberUpdate,
    ReportFilters, MaintenanceReportResponse, TeamPerformanceReport, SystemMetrics,
    ServiceOrderSearch, ComplaintSearch, MaintenanceSearch,
    ServiceOrderStatus, AlertLevel, ComplaintCategory, ComplaintStatus
)

router = APIRouter()

# Security
security = HTTPBearer()

# Helper function to check user role
def has_role(user: dict, role_name: str) -> bool:
    """Check if user has the specified role"""
    user_role = user.get("role", "")
    try:
        # Try to get from UserRole enum
        expected_role = getattr(UserRole, role_name, None)
        if expected_role:
            return user_role == expected_role or user_role == expected_role.value if hasattr(expected_role, 'value') else str(expected_role)
    except:
        pass
    # Fallback to string comparison
    role_map = {
        "MAINTENANCE_MANAGER": "maintenance_manager",
        "OPERATOR": "operator",
        "FINANCIAL_MANAGER": "financial_manager",
        "CRISIS_MANAGER": "crisis_manager",
        "SUPPORT_AGENT": "support_agent",
        "CITIZEN": "citizen"
    }
    expected = role_map.get(role_name, role_name.lower())
    return user_role == expected

def has_any_role(user: dict, role_names: list) -> bool:
    """Check if user has any of the specified roles"""
    return any(has_role(user, role) for role in role_names)

async def verify_user_token(token: str):
    """Verify user token and return user data"""
    try:
        # ✅ IMPORTANTE: verify_token NÃO é async, então NÃO usar await
        payload = verify_token(token.replace("Bearer ", ""))
        
        # Extrair dados do payload
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        return {
            "id": int(user_id),
            "email": payload.get("email", ""),
            "role": payload.get("role", "user"),
            "name": payload.get("name", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "maintenance-service",
        "timestamp": datetime.now().isoformat()
    }

# Test endpoint without auth
@router.get("/test")
async def test_endpoint():
    """Test endpoint without authentication"""
    return {
        "message": "Test endpoint working!",
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
    """Create service order (maintenance manager only)"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if not has_role(user, "MAINTENANCE_MANAGER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas gerentes de manutenção podem criar ordens de serviço"
        )
    
    protocol_number = generate_protocol_number()
    
    service_order = ServiceOrder(
        title=order_data.title,
        description=order_data.description,
        priority=order_data.priority,
        location=order_data.location,
        anomaly_id=order_data.anomaly_id,
        protocol_number=protocol_number,
        created_by=user["id"],
        created_by_name=user["name"],
        status=ServiceOrderStatus.OPEN
    )
    
    db.add(service_order)
    db.commit()
    db.refresh(service_order)
    
    # Send notification to available teams
    background_tasks.add_task(notify_available_teams, service_order)
    
    return service_order

@router.get("/orders", response_model=List[ServiceOrderResponse])
async def get_service_orders(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    team: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get service orders with filters"""
    try:
        print(f"🔍 get_service_orders called with status={status}, priority={priority}, team={team}")
        # ✅ Esta função JÁ É async, então pode usar await
        user = await verify_user_token(f"Bearer {credentials.credentials}")
        print(f"✅ User authenticated: {user}")
        
        # Query principal
        query = db.query(ServiceOrder)
        
        # Aplicar filtros
        if status:
            query = query.filter(ServiceOrder.status == status)
        if priority:
            query = query.filter(ServiceOrder.priority == priority)
        if team:
            query = query.filter(ServiceOrder.assigned_team == team)
        
        # Executar query
        orders = query.offset(skip).limit(limit).all()
        print(f"✅ Found {len(orders)} orders")
        
        return orders
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_service_orders: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")




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
    
    if not has_any_role(user, ["MAINTENANCE_MANAGER", "OPERATOR"]):
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

@router.get("/orders/{order_id}/progress", response_model=List[ServiceOrderProgressResponse])
async def list_order_progress(
    order_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordem de serviço não encontrada")
    progress = db.query(ServiceOrderProgress).filter(ServiceOrderProgress.service_order_id == order_id).order_by(ServiceOrderProgress.created_at.asc()).all()
    return progress

@router.post("/orders/{order_id}/progress", response_model=ServiceOrderProgressResponse)
async def add_order_progress(
    order_id: int,
    body: ServiceOrderProgressSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    if not has_any_role(user, ["MAINTENANCE_MANAGER", "OPERATOR"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordem de serviço não encontrada")
    # Create progress entry
    progress = ServiceOrderProgress(
        service_order_id=order_id,
        status=body.status,
        progress_notes=body.progress_notes,
        estimated_completion=body.estimated_completion,
        created_by=user["id"],
        created_by_name=user.get("name"),
    )
    db.add(progress)
    # Update order status/timeboxes
    order.status = body.status
    if body.status == ServiceOrderStatus.IN_PROGRESS:
        if not order.started_at:
            order.started_at = datetime.now()
    if body.status == ServiceOrderStatus.COMPLETED:
        order.completed_at = datetime.now()
    if body.estimated_completion:
        order.estimated_completion = body.estimated_completion
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(progress)
    return progress
@router.put("/orders/{order_id}/assign", response_model=ServiceOrderResponse)
async def assign_service_order(
    order_id: int,
    team_name: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Assign a team to a service order"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if not has_any_role(user, ["MAINTENANCE_MANAGER", "OPERATOR"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordem de serviço não encontrada")
    
    team = db.query(Team).filter(Team.name == team_name, Team.is_active == True).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Equipe inválida ou inativa")
    
    # Validate capacity
    current_workload = db.query(ServiceOrder).filter(
        ServiceOrder.assigned_team == team.name,
        ServiceOrder.status.in_([ServiceOrderStatus.ASSIGNED, ServiceOrderStatus.IN_PROGRESS])
    ).count()
    if current_workload >= (team.max_concurrent_orders or 0):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Equipe sem capacidade disponível")
    
    order.assigned_team = team.name
    order.assigned_at = datetime.now()
    order.status = ServiceOrderStatus.ASSIGNED
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    # record progress entry
    progress = ServiceOrderProgress(
        service_order_id=order.id,
        status=ServiceOrderStatus.ASSIGNED,
        progress_notes=f"Equipe atribuída: {team.name}",
        estimated_completion=order.estimated_completion,
        created_by=user["id"],
        created_by_name=user.get("name")
    )
    db.add(progress)
    db.commit()
    
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
    
    if not has_any_role(user, ["MAINTENANCE_MANAGER", "OPERATOR"]):
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get maintenance complaints"""
    try:
        user = await verify_user_token(f"Bearer {credentials.credentials}")
        
        # Verificar permissões
        if user["role"] not in ["operator", "maintenance_manager"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
        
        query = db.query(Complaint)
        
        if status:
            query = query.filter(Complaint.status == status)
        if category:
            query = query.filter(Complaint.category == category)
        
        complaints = query.offset(skip).limit(limit).all()
        return complaints
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_complaints: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== TEAM MANAGEMENT ====================

@router.post("/teams", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create maintenance team"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if not has_role(user, "MAINTENANCE_MANAGER"):
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

@router.put("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_update: TeamUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update maintenance team"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    if not has_role(user, "MAINTENANCE_MANAGER"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada")
    
    for field, value in team_update.dict(exclude_unset=True).items():
        setattr(team, field, value)
    team.updated_at = datetime.now()
    db.commit()
    db.refresh(team)
    return team

@router.get("/teams/{team_id}/members", response_model=List[TeamMemberResponse])
async def list_team_members(
    team_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    if not has_any_role(user, ["MAINTENANCE_MANAGER", "OPERATOR"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    return members

@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: int,
    member_data: TeamMemberCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    if not has_role(user, "MAINTENANCE_MANAGER"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipe não encontrada")
    member = TeamMember(
        team_id=team_id,
        name=member_data.name,
        role=member_data.role,
        contact=member_data.contact,
        is_active=member_data.is_active,
    )
    db.add(member)
    team.members_count = (team.members_count or 0) + 1
    db.commit()
    db.refresh(member)
    return member

@router.put("/teams/{team_id}/members/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    team_id: int,
    member_id: int,
    member_update: TeamMemberUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    if not has_role(user, "MAINTENANCE_MANAGER"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    member = db.query(TeamMember).filter(TeamMember.id == member_id, TeamMember.team_id == team_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro não encontrado")
    for field, value in member_update.dict(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return member

@router.delete("/teams/{team_id}/members/{member_id}")
async def delete_team_member(
    team_id: int,
    member_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    if not has_role(user, "MAINTENANCE_MANAGER"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    member = db.query(TeamMember).filter(TeamMember.id == member_id, TeamMember.team_id == team_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro não encontrado")
    team = db.query(Team).filter(Team.id == team_id).first()
    db.delete(member)
    if team and (team.members_count or 0) > 0:
        team.members_count = team.members_count - 1
    db.commit()
    return {"success": True}

@router.get("/teams", response_model=List[TeamResponse])
async def get_teams(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100
):
    """Get maintenance teams"""
    try:
        user = await verify_user_token(f"Bearer {credentials.credentials}")
        
        query = db.query(Team)
        if active_only:
            query = query.filter(Team.is_active == True)
        
        teams = query.offset(skip).limit(limit).all()
        
        # Calculate current workload and status, include members
        for team in teams:
            current_workload = db.query(ServiceOrder).filter(
                ServiceOrder.assigned_team == team.name,
                ServiceOrder.status.in_([ServiceOrderStatus.ASSIGNED, ServiceOrderStatus.IN_PROGRESS])
            ).count()
            team.current_workload = current_workload
            team.status = (
                "available" if team.is_active and current_workload < (team.max_concurrent_orders or 0) else "busy"
            )
            
            # Fix work_areas and equipment if they are PostgreSQL array strings
            if isinstance(team.work_areas, str):
                # Convert PostgreSQL array string like '{string}' to Python list
                team.work_areas = team.work_areas.strip('{}').split(',') if team.work_areas and team.work_areas != '{}' else []
            if isinstance(team.equipment, str):
                # Convert PostgreSQL array string like '{teste}' to Python list
                team.equipment = team.equipment.strip('{}').split(',') if team.equipment and team.equipment != '{}' else []
            
            members = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.is_active == True).all()
            # Attach simple members list for response
            team.members = [
                {"id": m.id, "name": m.name, "role": m.role, "contact": m.contact, "is_active": m.is_active}
            for m in members]
        
        return teams
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_teams: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==================== DASHBOARD & METRICS ====================

@router.get("/dashboard")
async def get_maintenance_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get maintenance dashboard metrics"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if not has_any_role(user, ["MAINTENANCE_MANAGER", "OPERATOR"]):
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