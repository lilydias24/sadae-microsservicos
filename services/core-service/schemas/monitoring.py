"""
Monitoring Service Schemas - Pydantic models for monitoring operations
Handles sensors, readings, anomalies, observations and leak reports
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

# Enums for monitoring
class SensorType(str, Enum):
    FLOW = "flow"
    PRESSURE = "pressure"
    QUALITY = "quality"
    LEVEL = "level"
    TEMPERATURE = "temperature"
    PH = "ph"
    TURBIDITY = "turbidity"
    CHLORINE = "chlorine"
    LEAK = "leak"

class AlertLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class AnomalyStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"

class LeakReportStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    REJECTED = "rejected"

# ==================== SENSOR SCHEMAS ====================

class SensorBase(BaseModel):
    id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    sensor_type: SensorType
    location: str = Field(..., min_length=1, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    unit: str = Field(..., min_length=1, max_length=20)
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None

class SensorCreate(SensorBase):
    installation_date: Optional[datetime] = None
    manufacturer: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    calibration_date: Optional[datetime] = None
    maintenance_interval_days: Optional[int] = Field(None, ge=1, le=365)

class SensorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    is_active: Optional[bool] = None
    calibration_date: Optional[datetime] = None
    maintenance_interval_days: Optional[int] = Field(None, ge=1, le=365)

class SensorResponse(SensorBase):
    is_active: bool = True
    installation_date: Optional[datetime] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    calibration_date: Optional[datetime] = None
    maintenance_interval_days: Optional[int] = None
    last_reading: Optional[datetime] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ==================== SENSOR READING SCHEMAS ====================

class SensorReadingBase(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=50)
    sensor_type: SensorType
    value: float
    unit: str = Field(..., min_length=1, max_length=20)
    location: str = Field(..., min_length=1, max_length=500)
    timestamp: datetime

class SensorReadingCreate(SensorReadingBase):
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    battery_level: Optional[float] = Field(None, ge=0, le=100)
    signal_strength: Optional[float] = Field(None, ge=0, le=100)
    raw_data: Optional[Dict[str, Any]] = None

class SensorReadingResponse(SensorReadingBase):
    id: int
    quality_score: Optional[float] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None
    is_anomaly: bool = False
    anomaly_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SensorReadingBatch(BaseModel):
    readings: List[SensorReadingCreate] = Field(..., max_items=1000)

# ==================== ANOMALY SCHEMAS ====================

class AnomalyBase(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=50)
    sensor_type: SensorType
    value: float
    threshold_value: float
    severity: AlertLevel
    description: str = Field(..., min_length=5, max_length=1000)
    location: str = Field(..., min_length=1, max_length=500)

class AnomalyCreate(AnomalyBase):
    reading_id: Optional[int] = None
    detection_method: Optional[str] = Field(None, max_length=50)  # "automatic", "manual", "threshold"
    additional_data: Optional[Dict[str, Any]] = None

class AnomalyUpdate(BaseModel):
    status: Optional[AnomalyStatus] = None
    severity: Optional[AlertLevel] = None
    description: Optional[str] = Field(None, min_length=5, max_length=1000)
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    assigned_operator_id: Optional[int] = None

class AnomalyResponse(AnomalyBase):
    id: int
    status: AnomalyStatus = AnomalyStatus.PENDING
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    assigned_operator_id: Optional[int] = None
    reading_id: Optional[int] = None
    detection_method: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    additional_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ==================== OBSERVATION SCHEMAS ====================

class ObservationBase(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=50)
    text: str = Field(..., min_length=5, max_length=2000)
    timestamp: datetime

class ObservationCreate(ObservationBase):
    observation_type: Optional[str] = Field(None, max_length=50)  # "maintenance", "inspection", "issue"
    severity: Optional[AlertLevel] = AlertLevel.LOW
    photos: Optional[List[str]] = None
    action_required: bool = False

class ObservationUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=5, max_length=2000)
    observation_type: Optional[str] = Field(None, max_length=50)
    severity: Optional[AlertLevel] = None
    action_required: Optional[bool] = None
    follow_up_notes: Optional[str] = Field(None, max_length=1000)

class ObservationResponse(ObservationBase):
    id: int
    operator_id: int
    operator_name: Optional[str] = None
    observation_type: Optional[str] = None
    severity: AlertLevel = AlertLevel.LOW
    photos: Optional[List[str]] = None
    action_required: bool = False
    follow_up_notes: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ==================== LEAK REPORT SCHEMAS ====================

class LeakReportBase(BaseModel):
    location: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10, max_length=2000)
    reporter_name: str = Field(..., min_length=2, max_length=100)
    reporter_contact: str = Field(..., min_length=5, max_length=200)

class LeakReportCreate(LeakReportBase):
    reporter_email: Optional[str] = None
    urgency_level: AlertLevel = AlertLevel.MEDIUM
    estimated_size: Optional[str] = Field(None, max_length=50)  # "small", "medium", "large"
    water_flow_stopped: bool = False
    photos: Optional[List[str]] = None

class LeakReportUpdate(BaseModel):
    status: Optional[LeakReportStatus] = None
    assigned_team: Optional[str] = Field(None, max_length=100)
    investigation_notes: Optional[str] = Field(None, max_length=2000)
    resolution_notes: Optional[str] = Field(None, max_length=2000)
    estimated_repair_cost: Optional[float] = Field(None, ge=0)
    actual_repair_cost: Optional[float] = Field(None, ge=0)

class LeakReportResponse(LeakReportBase):
    id: int
    protocol_number: str
    status: LeakReportStatus = LeakReportStatus.PENDING
    urgency_level: AlertLevel = AlertLevel.MEDIUM
    estimated_size: Optional[str] = None
    water_flow_stopped: bool = False
    assigned_team: Optional[str] = None
    investigation_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    estimated_repair_cost: Optional[float] = None
    actual_repair_cost: Optional[float] = None
    photos: Optional[List[str]] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PublicLeakReportCreate(BaseModel):
    location: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10, max_length=2000)
    reporter_name: str = Field(..., min_length=2, max_length=100)
    reporter_contact: str = Field(..., min_length=5, max_length=200)
    reporter_email: Optional[str] = None
    urgency_level: AlertLevel = AlertLevel.MEDIUM

class PublicLeakReportResponse(BaseModel):
    protocol_number: str
    status: LeakReportStatus
    created_at: datetime
    updated_at: datetime

# ==================== THRESHOLD MANAGEMENT ====================

class ThresholdUpdate(BaseModel):
    sensor_type: SensorType
    min: float
    max: float
    
    @validator('max')
    def max_must_be_greater_than_min(cls, v, values):
        if 'min' in values and v <= values['min']:
            raise ValueError('max must be greater than min')
        return v

class SensorThresholds(BaseModel):
    sensor_id: str
    sensor_type: SensorType
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    auto_adjust: bool = False
    adjustment_factor: Optional[float] = Field(None, ge=0.1, le=2.0)

# ==================== REAL-TIME DATA SCHEMAS ====================

class RealTimeReading(BaseModel):
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    location: str
    timestamp: datetime
    quality_score: Optional[float] = None
    is_anomaly: bool = False

class WebSocketMessage(BaseModel):
    type: str  # "sensor_reading", "anomaly_detected", "system_alert"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

# ==================== REPORT SCHEMAS ====================

class ReportFilters(BaseModel):
    sensor_type: Optional[SensorType] = None
    sensor_id: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    anomaly_status: Optional[AnomalyStatus] = None
    severity: Optional[AlertLevel] = None

class SensorReportResponse(BaseModel):
    report_id: str
    filters: ReportFilters
    summary: Dict[str, Any]
    sensor_statistics: Dict[str, Dict[str, Any]]
    readings: List[SensorReadingResponse]
    anomalies: List[AnomalyResponse]
    generated_at: datetime
    generated_by: str

class SystemHealthReport(BaseModel):
    total_sensors: int
    active_sensors: int
    offline_sensors: int
    sensors_with_anomalies: int
    total_readings_today: int
    average_reading_interval: float  # minutes
    system_uptime: float  # percentage
    data_quality_score: float  # 0-1

class AlertsReport(BaseModel):
    total_anomalies: int
    pending_anomalies: int
    critical_anomalies: int
    resolved_anomalies: int
    false_positives: int
    average_resolution_time: float  # hours
    anomalies_by_type: Dict[str, int]
    anomalies_by_location: Dict[str, int]

# ==================== SEARCH SCHEMAS ====================

class SensorSearch(BaseModel):
    query: Optional[str] = None
    sensor_type: Optional[SensorType] = None
    location: Optional[str] = None
    active_only: bool = True
    needs_maintenance: Optional[bool] = None
    skip: int = 0
    limit: int = 100

class AnomalySearch(BaseModel):
    query: Optional[str] = None
    status: Optional[List[AnomalyStatus]] = None
    severity: Optional[List[AlertLevel]] = None
    sensor_type: Optional[SensorType] = None
    sensor_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    assigned_operator: Optional[int] = None
    skip: int = 0
    limit: int = 100

class LeakReportSearch(BaseModel):
    query: Optional[str] = None
    status: Optional[List[LeakReportStatus]] = None
    urgency: Optional[List[AlertLevel]] = None
    location: Optional[str] = None
    assigned_team: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 100

# ==================== ANALYTICS SCHEMAS ====================

class SensorAnalytics(BaseModel):
    sensor_id: str
    readings_count: int
    avg_value: float
    min_value: float
    max_value: float
    anomalies_count: int
    uptime_percentage: float
    data_quality_score: float
    trend: str  # "increasing", "decreasing", "stable"

class LocationAnalytics(BaseModel):
    location: str
    sensors_count: int
    readings_count: int
    anomalies_count: int
    leak_reports_count: int
    avg_sensor_value: float
    risk_score: float  # 0-1, higher means more risk

class SystemAnalytics(BaseModel):
    time_period: str
    total_readings: int
    data_coverage: float  # percentage
    system_reliability: float  # percentage
    anomaly_rate: float  # percentage
    response_time: float  # average hours
    top_problematic_sensors: List[str]
    top_problematic_locations: List[str]