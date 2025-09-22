from enum import Enum

class SensorType(str, Enum):
    PRESSURE = "pressure"
    FLOW = "flow"
    WATER_QUALITY = "water_quality"
    PRECIPITATION = "precipitation"
    RIVER_LEVEL = "river_level"

class AlertLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"

class UserRole(str, Enum):
    OPERATOR = "operator"
    MAINTENANCE_MANAGER = "maintenance_manager"
    FINANCIAL_MANAGER = "financial_manager"
    CRISIS_MANAGER = "crisis_manager"
    CITIZEN = "citizen"


