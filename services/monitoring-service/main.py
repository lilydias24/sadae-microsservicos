from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import json
import redis
from datetime import datetime, timedelta
import sys
import os

# Add shared modules to path
sys.path.append('/app/shared')

from models import SensorType, AlertLevel, AnomalyStatus, UserRole
from database import get_database_url, create_database_engine, get_session_local
from utils import generate_protocol_number, make_service_request, service_registry

from database_models import Sensor, SensorReading, Anomaly, Observation, LeakReport, Base
from schemas import (
    SensorCreate, SensorResponse, SensorReadingCreate, SensorReadingResponse,
    AnomalyCreate, AnomalyResponse, ObservationCreate, ObservationResponse,
    LeakReportCreate, LeakReportResponse, ReportFilters
)
from anomaly_detector import AnomalyDetector
from websocket_manager import ConnectionManager

app = FastAPI(
    title="SADAE Monitoring Service",
    description="Real-time monitoring and anomaly detection service for SADAE",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = get_database_url("monitoring")
engine = create_database_engine(DATABASE_URL)
SessionLocal = get_session_local(engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Redis setup for real-time data
redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

# WebSocket manager for real-time updates
manager = ConnectionManager()

# Anomaly detector
anomaly_detector = AnomalyDetector()

def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_user_token(authorization: str):
    """Verify user token with auth service"""
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
    return {"message": "SADAE Monitoring Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "monitoring"}

# Sensor Management
@app.post("/sensors", response_model=SensorResponse)
async def create_sensor(
    sensor_data: SensorCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create a new sensor (operator only)"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.OPERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    sensor = Sensor(**sensor_data.dict())
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    
    return sensor

@app.get("/sensors", response_model=List[SensorResponse])
async def get_sensors(
    sensor_type: Optional[SensorType] = None,
    location: Optional[str] = None,
    active_only: bool = True,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get all sensors"""
    await verify_user_token(authorization)
    
    query = db.query(Sensor)
    
    if sensor_type:
        query = query.filter(Sensor.sensor_type == sensor_type)
    if location:
        query = query.filter(Sensor.location.ilike(f"%{location}%"))
    if active_only:
        query = query.filter(Sensor.is_active == True)
    
    sensors = query.all()
    return sensors

@app.get("/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor(
    sensor_id: str,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get sensor by ID"""
    await verify_user_token(authorization)
    
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    
    return sensor

# Real-time Monitoring
@app.get("/readings/realtime")
async def get_realtime_readings(
    sensor_type: Optional[SensorType] = None,
    location: Optional[str] = None,
    authorization: str = Depends(lambda request: request.headers.get("Authorization"))
):
    """Get real-time sensor readings from Redis cache"""
    await verify_user_token(authorization)
    
    # Get all sensor readings from Redis
    pattern = "sensor:*:latest"
    keys = redis_client.keys(pattern)
    
    readings = []
    for key in keys:
        reading_data = redis_client.get(key)
        if reading_data:
            reading = json.loads(reading_data)
            
            # Apply filters
            if sensor_type and reading.get("sensor_type") != sensor_type:
                continue
            if location and location.lower() not in reading.get("location", "").lower():
                continue
            
            readings.append(reading)
    
    return {"readings": readings, "timestamp": datetime.utcnow().isoformat()}

@app.post("/readings", response_model=SensorReadingResponse)
async def create_sensor_reading(
    reading_data: SensorReadingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Create a new sensor reading (from sensors/IoT devices)"""
    
    # Verify sensor exists
    sensor = db.query(Sensor).filter(Sensor.id == reading_data.sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    
    # Create reading record
    reading = SensorReading(**reading_data.dict())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    
    # Store in Redis for real-time access
    redis_key = f"sensor:{reading_data.sensor_id}:latest"
    redis_data = {
        "sensor_id": reading_data.sensor_id,
        "sensor_type": reading_data.sensor_type,
        "value": reading_data.value,
        "unit": reading_data.unit,
        "location": reading_data.location,
        "timestamp": reading_data.timestamp.isoformat()
    }
    redis_client.setex(redis_key, 3600, json.dumps(redis_data))  # Expire in 1 hour
    
    # Add to anomaly detection queue
    background_tasks.add_task(detect_anomaly, reading)
    
    # Broadcast to WebSocket clients
    await manager.broadcast(json.dumps({
        "type": "sensor_reading",
        "data": redis_data
    }))
    
    return reading

@app.get("/readings/history")
async def get_readings_history(
    sensor_id: Optional[str] = None,
    sensor_type: Optional[SensorType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 1000,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get historical sensor readings"""
    await verify_user_token(authorization)
    
    query = db.query(SensorReading)
    
    if sensor_id:
        query = query.filter(SensorReading.sensor_id == sensor_id)
    if sensor_type:
        query = query.filter(SensorReading.sensor_type == sensor_type)
    if start_date:
        query = query.filter(SensorReading.timestamp >= start_date)
    if end_date:
        query = query.filter(SensorReading.timestamp <= end_date)
    
    readings = query.order_by(SensorReading.timestamp.desc()).limit(limit).all()
    return {"readings": readings}

# Anomaly Management
@app.get("/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies(
    status: Optional[AnomalyStatus] = None,
    severity: Optional[AlertLevel] = None,
    sensor_type: Optional[SensorType] = None,
    skip: int = 0,
    limit: int = 100,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get anomalies with filters"""
    await verify_user_token(authorization)
    
    query = db.query(Anomaly)
    
    if status:
        query = query.filter(Anomaly.status == status)
    if severity:
        query = query.filter(Anomaly.severity == severity)
    if sensor_type:
        query = query.filter(Anomaly.sensor_type == sensor_type)
    
    anomalies = query.order_by(Anomaly.created_at.desc()).offset(skip).limit(limit).all()
    return anomalies

@app.post("/anomalies", response_model=AnomalyResponse)
async def create_anomaly(
    anomaly_data: AnomalyCreate,
    background_tasks: BackgroundTasks,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create anomaly alert (operator only)"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.OPERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Check for existing open anomaly for same sensor
    existing = db.query(Anomaly).filter(
        Anomaly.sensor_id == anomaly_data.sensor_id,
        Anomaly.status.in_([AnomalyStatus.PENDING, AnomalyStatus.CONFIRMED])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Open anomaly already exists for sensor {anomaly_data.sensor_id}"
        )
    
    anomaly = Anomaly(
        **anomaly_data.dict(),
        operator_id=user["id"],
        status=AnomalyStatus.CONFIRMED
    )
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    
    # Send notification
    background_tasks.add_task(send_anomaly_notification, anomaly)
    
    return anomaly

@app.put("/anomalies/{anomaly_id}/status")
async def update_anomaly_status(
    anomaly_id: int,
    new_status: AnomalyStatus,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Update anomaly status"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.OPERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found")
    
    anomaly.status = new_status
    anomaly.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Anomaly status updated successfully"}

# Observations
@app.post("/observations", response_model=ObservationResponse)
async def create_observation(
    observation_data: ObservationCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create observation (operator only)"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.OPERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    observation = Observation(
        **observation_data.dict(),
        operator_id=user["id"]
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)
    
    return observation

@app.get("/observations")
async def get_observations(
    sensor_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get observations"""
    await verify_user_token(authorization)
    
    query = db.query(Observation)
    
    if sensor_id:
        query = query.filter(Observation.sensor_id == sensor_id)
    if start_date:
        query = query.filter(Observation.timestamp >= start_date)
    if end_date:
        query = query.filter(Observation.timestamp <= end_date)
    
    observations = query.order_by(Observation.timestamp.desc()).all()
    return {"observations": observations}

# Public endpoints for citizens
@app.post("/public/leak-reports", response_model=LeakReportResponse)
async def report_leak(leak_data: LeakReportCreate, db: Session = Depends(get_db_session)):
    """Report water leak (public endpoint)"""
    
    protocol_number = generate_protocol_number()
    
    leak_report = LeakReport(
        **leak_data.dict(),
        protocol_number=protocol_number,
        status="pending"
    )
    db.add(leak_report)
    db.commit()
    db.refresh(leak_report)
    
    return leak_report

@app.get("/public/leak-reports/{protocol_number}")
async def get_leak_report_status(protocol_number: str, db: Session = Depends(get_db_session)):
    """Get leak report status by protocol number"""
    
    report = db.query(LeakReport).filter(LeakReport.protocol_number == protocol_number).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    return {
        "protocol_number": report.protocol_number,
        "status": report.status,
        "location": report.location,
        "created_at": report.created_at,
        "updated_at": report.updated_at
    }

# Reports
@app.post("/reports/generate")
async def generate_sensor_report(
    filters: ReportFilters,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Generate sensor data report"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.OPERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
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
    
    return {
        "report_id": generate_protocol_number(),
        "filters": filters.dict(),
        "summary": {
            "total_readings": total_readings,
            "average_value": round(avg_value, 2),
            "min_value": min_value,
            "max_value": max_value,
            "period": {
                "start": filters.start_date,
                "end": filters.end_date
            }
        },
        "readings": readings[:1000],  # Limit to 1000 for performance
        "generated_at": datetime.utcnow(),
        "generated_by": user["name"]
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background tasks
async def detect_anomaly(reading: SensorReading):
    """Detect anomaly in sensor reading"""
    try:
        is_anomaly, severity = await anomaly_detector.detect(reading)
        
        if is_anomaly:
            db = SessionLocal()
            try:
                # Check if anomaly already exists
                existing = db.query(Anomaly).filter(
                    Anomaly.sensor_id == reading.sensor_id,
                    Anomaly.status == AnomalyStatus.PENDING
                ).first()
                
                if not existing:
                    anomaly = Anomaly(
                        sensor_id=reading.sensor_id,
                        sensor_type=reading.sensor_type,
                        value=reading.value,
                        threshold_value=anomaly_detector.get_threshold(reading.sensor_id, reading.sensor_type),
                        severity=severity,
                        description=f"Automatic anomaly detection: {reading.sensor_type} value {reading.value} exceeds threshold",
                        location=reading.location,
                        status=AnomalyStatus.PENDING
                    )
                    db.add(anomaly)
                    db.commit()
                    
                    # Broadcast anomaly alert
                    await manager.broadcast(json.dumps({
                        "type": "anomaly_detected",
                        "data": {
                            "sensor_id": reading.sensor_id,
                            "sensor_type": reading.sensor_type,
                            "value": reading.value,
                            "severity": severity,
                            "location": reading.location,
                            "timestamp": reading.timestamp.isoformat()
                        }
                    }))
            finally:
                db.close()
    except Exception as e:
        print(f"Error in anomaly detection: {e}")

async def send_anomaly_notification(anomaly: Anomaly):
    """Send notification about anomaly"""
    try:
        notification_data = {
            "recipient_id": anomaly.operator_id,
            "title": f"Anomaly Alert - {anomaly.sensor_type}",
            "message": f"Anomaly detected at {anomaly.location}: {anomaly.description}",
            "type": "anomaly_alert",
            "channel": "email"
        }
        
        await make_service_request(
            service_registry.get_service_url("notification"),
            "/notifications",
            method="POST",
            data=notification_data
        )
    except Exception as e:
        print(f"Error sending notification: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
