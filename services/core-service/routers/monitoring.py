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
    try:
        # verify_token from shared.auth is synchronous, not async
        payload = verify_token(token)
        return {
            "id": int(payload.get("sub", 1)),
            "email": payload.get("email", ""),
            "role": payload.get("role", "user"),
            "name": payload.get("name", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

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
    
    user_role = user.get("role", "")
    if user_role != "operator":
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

# ==================== OBSERVATIONS ====================

@router.post("/observations", response_model=ObservationResponse)
async def create_observation(
    observation_data: ObservationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create observation for sensor data (RF004)"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    user_role = user.get("role", "")
    if user_role != "operator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Validate text length (10-500 characters as per business rule)
    text = observation_data.text or ""
    if len(text) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A observação deve ter no mínimo 10 caracteres"
        )
    if len(text) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A observação deve ter no máximo 500 caracteres"
        )
    
    # Get reading_id from observation_data if provided, otherwise None
    reading_id = getattr(observation_data, 'reading_id', None)
    
    observation = Observation(
        sensor_id=observation_data.sensor_id,
        reading_id=reading_id,
        text=text,
        operator_id=user["id"],
        operator_name=user.get("name", "Unknown"),
        observation_type=observation_data.observation_type,
        timestamp=observation_data.timestamp or datetime.now()
    )
    
    db.add(observation)
    db.commit()
    db.refresh(observation)
    
    return observation

@router.get("/observations", response_model=List[ObservationResponse])
async def get_observations(
    sensor_id: Optional[str] = None,
    reading_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get observations with filters"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    query = db.query(Observation)
    
    if sensor_id:
        query = query.filter(Observation.sensor_id == sensor_id)
    if reading_id:
        query = query.filter(Observation.reading_id == reading_id)
    if start_date:
        query = query.filter(Observation.timestamp >= start_date)
    if end_date:
        query = query.filter(Observation.timestamp <= end_date)
    
    observations = query.order_by(desc(Observation.timestamp)).offset(skip).limit(limit).all()
    return observations

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
    
    user_role = user.get("role", "")
    allowed_roles = ["operator", "maintenance_manager"]
    if user_role not in allowed_roles:
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

# ==================== REPORTS ====================

@router.post("/reports/generate")
async def generate_sensor_report(
    filters: ReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Generate sensor data report (RF002)"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    
    # Check permissions - operator and crisis_manager roles can generate reports
    user_role = user.get("role", "")
    allowed_roles = ["operator", "crisis_manager", "manager"]
    if user_role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Validate period (max 90 days as per business rule)
    if filters.start_date and filters.end_date:
        period_days = (filters.end_date - filters.start_date).days
        if period_days > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O período máximo para geração de relatório é de 90 dias"
            )
        if period_days < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A data de início deve ser anterior à data de fim"
            )
    
    query = db.query(SensorReading)
    
    if filters.sensor_type:
        query = query.filter(SensorReading.sensor_type == filters.sensor_type)
    if filters.sensor_id:
        query = query.filter(SensorReading.sensor_id == filters.sensor_id)
    if filters.start_date:
        query = query.filter(SensorReading.timestamp >= filters.start_date)
    if filters.end_date:
        query = query.filter(SensorReading.timestamp <= filters.end_date)
    if filters.location:
        query = query.filter(SensorReading.location.ilike(f"%{filters.location}%"))
    
    readings = query.order_by(SensorReading.timestamp.desc()).all()
    
    # Generate report summary
    total_readings = len(readings)
    if total_readings > 0:
        avg_value = sum(r.value for r in readings) / total_readings
        min_value = min(r.value for r in readings)
        max_value = max(r.value for r in readings)
    else:
        avg_value = min_value = max_value = 0
    
    report_id = generate_protocol_number()
    
    return {
        "report_id": report_id,
        "filters": filters.dict(),
        "summary": {
            "total_readings": total_readings,
            "average_value": round(avg_value, 2),
            "min_value": min_value,
            "max_value": max_value,
            "period": {
                "start": filters.start_date.isoformat() if filters.start_date else None,
                "end": filters.end_date.isoformat() if filters.end_date else None
            }
        },
        "readings": [
            {
                "id": r.id,
                "sensor_id": r.sensor_id,
                "sensor_type": r.sensor_type,
                "value": r.value,
                "unit": r.unit,
                "location": r.location,
                "timestamp": r.timestamp.isoformat()
            }
            for r in readings[:1000]  # Limit to 1000 for performance
        ],
        "generated_at": datetime.now().isoformat(),
        "generated_by": user.get("name", "Unknown")
    }