from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from database_models import Sensor, SensorReading, Anomaly, LeakReport

router = APIRouter()

@router.get("/sensors")
async def get_sensors(db: Session = Depends(get_db)):
    """Get all sensors"""
    sensors = db.query(Sensor).all()
    return sensors

@router.get("/readings/realtime")
async def get_realtime_readings(db: Session = Depends(get_db)):
    """Get real-time readings"""
    readings = db.query(SensorReading).order_by(SensorReading.timestamp.desc()).limit(100).all()
    return readings

@router.post("/anomalies")
async def create_anomaly(anomaly_data: dict, db: Session = Depends(get_db)):
    """Create anomaly"""
    anomaly = Anomaly(**anomaly_data)
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly

@router.post("/public/leak-reports")
async def create_leak_report(report_data: dict, db: Session = Depends(get_db)):
    """Create leak report"""
    report = LeakReport(**report_data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report