"""
Monitoring Service Router - Sistema de Monitoramento e Sensores
Gerencia sensores, leituras, anomalias e relatórios
"""
import os
import sys
import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, WebSocket, WebSocketDisconnect
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
    async def verify_token(token):
        return {"id": 1, "name": "Test User", "email": "test@test.com", "role": "operator"}
    
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
    Sensor, SensorReading, Anomaly, Observation, LeakReport
)
from schemas.monitoring import (
    SensorCreate, SensorResponse, SensorUpdate, SensorSearch,
    SensorReadingCreate, SensorReadingResponse, SensorReadingBatch,
    AnomalyCreate, AnomalyResponse, AnomalyUpdate, AnomalySearch,
    ObservationCreate, ObservationResponse, ObservationUpdate,
    LeakReportCreate, LeakReportResponse, LeakReportUpdate, PublicLeakReportCreate, PublicLeakReportResponse,
    LeakReportSearch, ReportFilters, SensorReportResponse, SystemHealthReport, AlertsReport,
    ThresholdUpdate, SensorThresholds, RealTimeReading, WebSocketMessage,
    SensorAnalytics, LocationAnalytics, SystemAnalytics,
    SensorType, AlertLevel, AnomalyStatus, LeakReportStatus
)

router = APIRouter()

# Security
security = HTTPBearer()

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

# Simple connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "monitoring-service",
        "timestamp": datetime.now().isoformat()
    }

# ==================== SENSOR MANAGEMENT ====================

@router.get("/sensors", response_model=List[SensorResponse])
async def get_sensors(
    sensor_type: Optional[SensorType] = None,
    location: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all sensors with filters"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    query = db.query(Sensor)
    
    if sensor_type:
        query = query.filter(Sensor.sensor_type == sensor_type)
    if location:
        query = query.filter(Sensor.location.ilike(f"%{location}%"))
    if active_only:
        query = query.filter(Sensor.is_active == True)
    
    sensors = query.offset(skip).limit(limit).all()
    return sensors

@router.get("/readings/realtime")
async def get_realtime_readings(
    sensor_type: Optional[SensorType] = None,
    location: Optional[str] = None,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get recent sensor readings"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    # Get most recent reading for each sensor
    subquery = db.query(
        SensorReading.sensor_id,
        func.max(SensorReading.timestamp).label('max_timestamp')
    ).group_by(SensorReading.sensor_id).subquery()
    
    query = db.query(SensorReading).join(
        subquery,
        and_(
            SensorReading.sensor_id == subquery.c.sensor_id,
            SensorReading.timestamp == subquery.c.max_timestamp
        )
    )
    
    # Apply filters
    if sensor_type:
        query = query.filter(SensorReading.sensor_type == sensor_type)
    if location:
        query = query.filter(SensorReading.location.ilike(f"%{location}%"))
    
    readings = query.limit(limit).all()
    
    return {
        "readings": readings,
        "timestamp": datetime.now().isoformat(),
        "count": len(readings)
    }

@router.post("/anomalies", response_model=AnomalyResponse)
async def create_anomaly(
    anomaly_data: AnomalyCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create anomaly alert (operator only)"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if user["role"] != UserRole.OPERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    anomaly = Anomaly(
        sensor_id=anomaly_data.sensor_id,
        sensor_type=anomaly_data.sensor_type,
        value=anomaly_data.value,
        threshold_value=anomaly_data.threshold_value,
        severity=anomaly_data.severity,
        description=anomaly_data.description,
        location=anomaly_data.location,
        reading_id=anomaly_data.reading_id,
        detection_method=anomaly_data.detection_method or "manual",
        additional_data=anomaly_data.additional_data,
        operator_id=user["id"],
        operator_name=user["name"],
        status=AnomalyStatus.CONFIRMED
    )
    
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    
    return anomaly

@router.get("/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies(
    status: Optional[AnomalyStatus] = None,
    severity: Optional[AlertLevel] = None,
    sensor_type: Optional[SensorType] = None,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get anomalies with filters"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    query = db.query(Anomaly)
    
    if status:
        query = query.filter(Anomaly.status == status)
    if severity:
        query = query.filter(Anomaly.severity == severity)
    if sensor_type:
        query = query.filter(Anomaly.sensor_type == sensor_type)
    
    anomalies = query.order_by(desc(Anomaly.created_at)).offset(skip).limit(limit).all()
    return anomalies

@router.post("/public/leak-reports", response_model=PublicLeakReportResponse)
async def create_leak_report(
    report_data: PublicLeakReportCreate,
    db: Session = Depends(get_db)
):
    """Create leak report (public endpoint)"""
    
    protocol_number = generate_protocol_number()
    
    leak_report = LeakReport(
        location=report_data.location,
        description=report_data.description,
        reporter_name=report_data.reporter_name,
        reporter_contact=report_data.reporter_contact,
        reporter_email=report_data.reporter_email,
        urgency_level=report_data.urgency_level,
        protocol_number=protocol_number,
        status=LeakReportStatus.PENDING
    )
    
    db.add(leak_report)
    db.commit()
    db.refresh(leak_report)
    
    return PublicLeakReportResponse(
        protocol_number=leak_report.protocol_number,
        status=leak_report.status,
        created_at=leak_report.created_at,
        updated_at=leak_report.updated_at
    )

@router.get("/public/leak-reports/{protocol_number}")
async def get_leak_report_status(
    protocol_number: str,
    db: Session = Depends(get_db)
):
    """Get leak report status by protocol number"""
    
    report = db.query(LeakReport).filter(LeakReport.protocol_number == protocol_number).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relatório não encontrado")
    
    return PublicLeakReportResponse(
        protocol_number=report.protocol_number,
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at
    )

@router.get("/dashboard")
async def get_monitoring_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get monitoring dashboard metrics"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    if user["role"] not in [UserRole.OPERATOR, UserRole.MAINTENANCE_MANAGER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Basic metrics
    total_sensors = db.query(Sensor).count()
    active_sensors = db.query(Sensor).filter(Sensor.is_active == True).count()
    
    # Anomalies
    pending_anomalies = db.query(Anomaly).filter(Anomaly.status == AnomalyStatus.PENDING).count()
    critical_anomalies = db.query(Anomaly).filter(
        Anomaly.severity == AlertLevel.CRITICAL,
        Anomaly.status.in_([AnomalyStatus.PENDING, AnomalyStatus.CONFIRMED])
    ).count()
    
    # Recent readings (last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_readings = db.query(SensorReading).filter(
        SensorReading.timestamp >= one_hour_ago
    ).count()
    
    # Leak reports
    pending_leaks = db.query(LeakReport).filter(LeakReport.status == LeakReportStatus.PENDING).count()
    
    return {
        "total_sensors": total_sensors,
        "active_sensors": active_sensors,
        "offline_sensors": total_sensors - active_sensors,
        "pending_anomalies": pending_anomalies,
        "critical_anomalies": critical_anomalies,
        "recent_readings": recent_readings,
        "pending_leaks": pending_leaks
    }