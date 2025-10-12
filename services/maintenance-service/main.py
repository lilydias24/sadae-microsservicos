from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os

# Add shared modules to path
sys.path.append('/app/shared')

from models import ServiceOrderStatus, AlertLevel, UserRole
from database import get_database_url, create_database_engine, get_session_local
from utils import generate_protocol_number, make_service_request, service_registry

from database_models import ServiceOrder, Maintenance, Complaint, ServiceEvaluation, Team, Base
from schemas import (
    ServiceOrderCreate, ServiceOrderResponse, ServiceOrderUpdate,
    MaintenanceCreate, MaintenanceResponse,
    ComplaintCreate, ComplaintResponse,
    ServiceEvaluationCreate, ServiceEvaluationResponse,
    TeamCreate, TeamResponse,
    ReportFilters, MaintenanceReportResponse
)

app = FastAPI(
    title="SADAE Maintenance Service",
    description="Maintenance and public service management for SADAE",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = get_database_url("maintenance")
engine = create_database_engine(DATABASE_URL)
SessionLocal = get_session_local(engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_user_token(authorization: str = None):
    """Verify user token with auth service"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    try:
        response = await make_service_request(
            service_registry.get_service_url("auth"),
            "/verify-token",
            method="POST",
            headers={"Authorization": authorization}
        )
        return response["user"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.get("/")
async def root():
    return {"message": "SADAE Maintenance Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "maintenance"}

# Service Order Management
@app.post("/orders", response_model=ServiceOrderResponse)
async def create_service_order(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Create service order (maintenance manager only)"""
    # Temporarily disable auth for testing
    # user = await verify_user_token(authorization)
    # if user["role"] != UserRole.MAINTENANCE_MANAGER:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error parsing JSON: {str(e)}")
    
    # Generate protocol number
    protocol_number = generate_protocol_number()
    
    service_order = ServiceOrder(
        title=body.get("title"),
        description=body.get("description"),
        priority=body.get("priority", "medium"),
        location=body.get("location"),
        protocol_number=protocol_number,
        created_by=1,  # Temporary user ID
        status=ServiceOrderStatus.OPEN
    )
    db.add(service_order)
    db.commit()
    db.refresh(service_order)
    
    # Send notification to available teams
    background_tasks.add_task(notify_available_teams, service_order)
    
    return service_order

@app.get("/orders", response_model=List[ServiceOrderResponse])
async def get_service_orders(
    request: Request,
    status: Optional[ServiceOrderStatus] = None,
    priority: Optional[AlertLevel] = None,
    assigned_team: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Get service orders with filters"""
    # Temporarily disable auth for testing
    # authorization = request.headers.get("Authorization")
    # user = await verify_user_token(authorization)
    user = {"id": 1, "role": "MAINTENANCE_MANAGER"}
    
    query = db.query(ServiceOrder)
    
    if status:
        query = query.filter(ServiceOrder.status == status)
    if priority:
        query = query.filter(ServiceOrder.priority == priority)
    if assigned_team:
        query = query.filter(ServiceOrder.assigned_team == assigned_team)
    
    # Citizens can only see their own orders
    if user["role"] == UserRole.CITIZEN:
        query = query.filter(ServiceOrder.created_by == user["id"])
    
    orders = query.order_by(ServiceOrder.created_at.desc()).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/{order_id}", response_model=ServiceOrderResponse)
async def get_service_order(
    order_id: int,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get service order by ID"""
    user = await verify_user_token(authorization)
    
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")
    
    # Citizens can only see their own orders
    if user["role"] == UserRole.CITIZEN and order.created_by != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return order

@app.put("/orders/{order_id}", response_model=ServiceOrderResponse)
async def update_service_order(
    order_id: int,
    order_update: ServiceOrderUpdate,
    background_tasks: BackgroundTasks,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Update service order (maintenance manager only)"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.MAINTENANCE_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")
    
    # Update fields
    for field, value in order_update.dict(exclude_unset=True).items():
        setattr(order, field, value)
    
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    
    # Send notifications on status changes
    if order_update.status:
        background_tasks.add_task(send_status_notification, order, user)
    
    return order

@app.put("/orders/{order_id}/assign")
async def assign_service_order(
    order_id: int,
    team_name: str,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Assign service order to team"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.MAINTENANCE_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")
    
    # Check if team exists
    team = db.query(Team).filter(Team.name == team_name, Team.is_active == True).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found or inactive")
    
    order.assigned_team = team_name
    order.status = ServiceOrderStatus.ASSIGNED
    order.assigned_at = datetime.utcnow()
    order.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Service order assigned to team {team_name}"}

# Maintenance Management
@app.post("/maintenances", response_model=MaintenanceResponse)
async def register_maintenance(
    maintenance_data: MaintenanceCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Register completed maintenance"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.MAINTENANCE_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Verify service order exists
    if maintenance_data.service_order_id:
        order = db.query(ServiceOrder).filter(ServiceOrder.id == maintenance_data.service_order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")
        
        # Update service order status to completed
        order.status = ServiceOrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()
    
    maintenance = Maintenance(
        **maintenance_data.dict(),
        registered_by=user["id"]
    )
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    
    return maintenance

@app.get("/maintenances", response_model=List[MaintenanceResponse])
async def get_maintenances(
    service_order_id: Optional[int] = None,
    team_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get maintenance records"""
    await verify_user_token(authorization)
    
    query = db.query(Maintenance)
    
    if service_order_id:
        query = query.filter(Maintenance.service_order_id == service_order_id)
    if team_name:
        query = query.filter(Maintenance.team_name == team_name)
    if start_date:
        query = query.filter(Maintenance.completion_date >= start_date)
    if end_date:
        query = query.filter(Maintenance.completion_date <= end_date)
    
    maintenances = query.order_by(Maintenance.completion_date.desc()).offset(skip).limit(limit).all()
    return maintenances

# Public Complaint System
@app.post("/public/complaints", response_model=ComplaintResponse)
async def create_complaint(
    complaint_data: ComplaintCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Create public complaint (no authentication required)"""
    
    protocol_number = generate_protocol_number()
    
    complaint = Complaint(
        **complaint_data.dict(),
        protocol_number=protocol_number,
        status="pending"
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    
    # Create service order if needed
    if complaint.category in ["water_leak", "pressure_issue", "quality_issue"]:
        background_tasks.add_task(create_service_order_from_complaint, complaint)
    
    return complaint

@app.get("/public/complaints/{protocol_number}")
async def get_complaint_status(
    protocol_number: str,
    db: Session = Depends(get_db_session)
):
    """Get complaint status by protocol number"""
    
    complaint = db.query(Complaint).filter(Complaint.protocol_number == protocol_number).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    
    return {
        "protocol_number": complaint.protocol_number,
        "title": complaint.title,
        "status": complaint.status,
        "category": complaint.category,
        "created_at": complaint.created_at,
        "updated_at": complaint.updated_at
    }

@app.get("/complaints", response_model=List[ComplaintResponse])
async def get_complaints(
    status: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get complaints (staff only)"""
    user = await verify_user_token(authorization)
    if user["role"] not in [UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    query = db.query(Complaint)
    
    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    
    complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    return complaints

@app.put("/complaints/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: int,
    new_status: str,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Update complaint status"""
    user = await verify_user_token(authorization)
    if user["role"] not in [UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    
    complaint.status = new_status
    complaint.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Complaint status updated successfully"}

# Service Evaluation
@app.post("/evaluations", response_model=ServiceEvaluationResponse)
async def create_service_evaluation(
    evaluation_data: ServiceEvaluationCreate,
    db: Session = Depends(get_db_session)
):
    """Create service evaluation (public endpoint)"""
    
    # Verify service order exists and is completed
    if evaluation_data.service_order_id:
        order = db.query(ServiceOrder).filter(ServiceOrder.id == evaluation_data.service_order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service order not found")
        if order.status != ServiceOrderStatus.COMPLETED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service order not completed yet")
    
    # Check if evaluation already exists
    existing = db.query(ServiceEvaluation).filter(
        ServiceEvaluation.service_order_id == evaluation_data.service_order_id
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Evaluation already exists for this service")
    
    evaluation = ServiceEvaluation(**evaluation_data.dict())
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    return evaluation

@app.get("/evaluations")
async def get_service_evaluations(
    service_order_id: Optional[int] = None,
    min_rating: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get service evaluations (staff only)"""
    user = await verify_user_token(authorization)
    if user["role"] not in [UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    query = db.query(ServiceEvaluation)
    
    if service_order_id:
        query = query.filter(ServiceEvaluation.service_order_id == service_order_id)
    if min_rating:
        query = query.filter(ServiceEvaluation.rating >= min_rating)
    
    evaluations = query.order_by(ServiceEvaluation.created_at.desc()).offset(skip).limit(limit).all()
    return {"evaluations": evaluations}

# Team Management
@app.post("/teams", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db_session)
):
    """Create maintenance team"""
    # Temporarily disable auth for testing
    # authorization = request.headers.get("Authorization")
    # user = await verify_user_token(authorization)
    # if user["role"] != UserRole.MAINTENANCE_MANAGER:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Check if team name already exists
    existing = db.query(Team).filter(Team.name == team_data.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team name already exists")
    
    team = Team(**team_data.dict())
    db.add(team)
    db.commit()
    db.refresh(team)
    
    return team

@app.get("/teams", response_model=List[TeamResponse])
async def get_teams(
    active_only: bool = True,
    db: Session = Depends(get_db_session)
):
    """Get maintenance teams"""
    # Temporarily disable auth for testing
    # authorization = request.headers.get("Authorization")
    # await verify_user_token(authorization)
    
    query = db.query(Team)
    if active_only:
        query = query.filter(Team.is_active == True)
    
    teams = query.all()
    return teams

# Reports
@app.post("/reports/interventions")
async def generate_interventions_report(
    filters: ReportFilters,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Generate interventions report"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.MAINTENANCE_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Query maintenances based on filters
    query = db.query(Maintenance)
    
    if filters.start_date:
        query = query.filter(Maintenance.completion_date >= filters.start_date)
    if filters.end_date:
        query = query.filter(Maintenance.completion_date <= filters.end_date)
    if filters.team_name:
        query = query.filter(Maintenance.team_name == filters.team_name)
    if filters.location:
        query = query.filter(Maintenance.location.ilike(f"%{filters.location}%"))
    
    maintenances = query.order_by(Maintenance.completion_date.desc()).all()
    
    # Calculate statistics
    total_interventions = len(maintenances)
    total_cost = sum(m.cost for m in maintenances if m.cost)
    total_duration = sum(m.duration_hours for m in maintenances if m.duration_hours)
    
    avg_cost = total_cost / total_interventions if total_interventions > 0 else 0
    avg_duration = total_duration / total_interventions if total_interventions > 0 else 0
    
    # Group by team
    team_stats = {}
    for maintenance in maintenances:
        team = maintenance.team_name
        if team not in team_stats:
            team_stats[team] = {"count": 0, "total_cost": 0, "total_duration": 0}
        
        team_stats[team]["count"] += 1
        team_stats[team]["total_cost"] += maintenance.cost or 0
        team_stats[team]["total_duration"] += maintenance.duration_hours or 0
    
    return MaintenanceReportResponse(
        report_id=generate_protocol_number(),
        filters=filters,
        summary={
            "total_interventions": total_interventions,
            "total_cost": round(total_cost, 2),
            "average_cost": round(avg_cost, 2),
            "total_duration_hours": round(total_duration, 2),
            "average_duration_hours": round(avg_duration, 2),
            "period": {
                "start": filters.start_date,
                "end": filters.end_date
            }
        },
        team_statistics=team_stats,
        interventions=maintenances[:100],  # Limit for performance
        generated_at=datetime.utcnow(),
        generated_by=user["name"]
    )

# Background tasks
async def notify_available_teams(service_order: ServiceOrder):
    """Notify available teams about new service order"""
    try:
        # This would typically send notifications to team mobile apps or email
        print(f"Notifying teams about new service order: {service_order.protocol_number}")
        
        # Send notification via notification service
        notification_data = {
            "title": f"New Service Order: {service_order.title}",
            "message": f"Priority: {service_order.priority}, Location: {service_order.location}",
            "type": "service_order",
            "channel": "push"
        }
        
        # This would send to all maintenance managers
        await make_service_request(
            service_registry.get_service_url("notification"),
            "/notifications/broadcast",
            method="POST",
            data=notification_data
        )
    except Exception as e:
        print(f"Error sending team notification: {e}")

async def send_status_notification(service_order: ServiceOrder, user: dict):
    """Send notification about status change"""
    try:
        if service_order.created_by:
            notification_data = {
                "recipient_id": service_order.created_by,
                "title": f"Service Order Update: {service_order.protocol_number}",
                "message": f"Status changed to: {service_order.status}",
                "type": "status_update",
                "channel": "email"
            }
            
            await make_service_request(
                service_registry.get_service_url("notification"),
                "/notifications",
                method="POST",
                data=notification_data
            )
    except Exception as e:
        print(f"Error sending status notification: {e}")

async def create_service_order_from_complaint(complaint: Complaint):
    """Create service order from complaint"""
    try:
        # Map complaint categories to service order priorities
        priority_map = {
            "water_leak": AlertLevel.HIGH,
            "pressure_issue": AlertLevel.MEDIUM,
            "quality_issue": AlertLevel.HIGH,
            "other": AlertLevel.LOW
        }
        
        order_data = {
            "title": f"Complaint: {complaint.title}",
            "description": f"Auto-generated from complaint {complaint.protocol_number}: {complaint.description}",
            "priority": priority_map.get(complaint.category, AlertLevel.MEDIUM),
            "location": complaint.location,
            "complaint_id": complaint.id
        }
        
        # This would create the service order through the API
        print(f"Creating service order from complaint: {complaint.protocol_number}")
        
    except Exception as e:
        print(f"Error creating service order from complaint: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
