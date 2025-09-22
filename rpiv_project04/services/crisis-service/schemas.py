from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Critical Events
class CriticalEventBase(BaseModel):
    event_type: str = Field(..., description="Type of critical event")
    description: str = Field(..., description="Event description")
    severity: str = Field(..., description="Severity level")
    location: str = Field(..., description="Event location")
    coordinates: Optional[Dict[str, float]] = None
    affected_population: Optional[int] = None

class CriticalEventCreate(CriticalEventBase):
    sensor_data: Optional[Dict[str, Any]] = None

class CriticalEventResponse(CriticalEventBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Civil Defense Alerts
class CivilDefenseAlertCreate(BaseModel):
    message: str = Field(..., description="Alert message")
    urgency_level: str = Field(..., description="Urgency level")
    affected_areas: List[str] = Field(..., description="Affected areas")
    recommended_actions: List[str] = Field(..., description="Recommended actions")

class CivilDefenseAlertResponse(BaseModel):
    id: int
    event_id: int
    message: str
    urgency_level: str
    affected_areas: List[str]
    recommended_actions: List[str]
    sent_by: int
    sent_at: datetime
    acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Evacuation Routes
class EvacuationRouteBase(BaseModel):
    name: str = Field(..., description="Route name")
    area: str = Field(..., description="Area covered")
    start_point: Dict[str, Any] = Field(..., description="Starting point")
    end_point: Dict[str, Any] = Field(..., description="End point")
    waypoints: Optional[List[Dict[str, Any]]] = None
    distance_km: Optional[float] = None
    estimated_time: Optional[int] = None
    capacity: Optional[int] = None
    accessibility: Optional[str] = None

class EvacuationRouteResponse(EvacuationRouteBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RouteRecalculationRequest(BaseModel):
    affected_area: str = Field(..., description="Area affected by crisis")
    blocked_points: List[Dict[str, Any]] = Field(default=[], description="Blocked locations")
    safe_zones: List[Dict[str, Any]] = Field(..., description="Safe evacuation zones")
    max_routes: int = Field(default=5, description="Maximum number of routes to calculate")

# Simulations
class SimulationBase(BaseModel):
    name: str = Field(..., description="Simulation name")
    scenario_type: str = Field(..., description="Type of crisis scenario")
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(..., description="Simulation parameters")
    duration_days: int = Field(..., description="Simulation duration in days")
    affected_areas: List[str] = Field(..., description="Areas to simulate")

class SimulationCreate(SimulationBase):
    pass

class SimulationResponse(SimulationBase):
    id: int
    status: str
    results: Optional[Dict[str, Any]] = None
    created_by: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Mitigation Plans
class MitigationPlanBase(BaseModel):
    name: str = Field(..., description="Plan name")
    description: Optional[str] = None
    scenario_type: str = Field(..., description="Crisis scenario type")
    priority: str = Field(default="medium", description="Plan priority")
    estimated_cost: Optional[float] = None
    implementation_time: Optional[int] = None
    effectiveness_score: Optional[float] = None

class MitigationPlanCreate(MitigationPlanBase):
    simulation_id: Optional[int] = None

class MitigationPlanResponse(MitigationPlanBase):
    id: int
    simulation_id: Optional[int] = None
    status: str
    created_by: int
    created_at: datetime
    approved_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Mitigation Actions
class MitigationActionBase(BaseModel):
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Action description")
    action_type: str = Field(..., description="Type of action")
    responsible_entity: Optional[str] = None
    trigger_condition: Optional[str] = None
    estimated_cost: Optional[float] = None
    duration_hours: Optional[int] = None
    priority: int = Field(default=1, description="Execution priority")

class MitigationActionCreate(MitigationActionBase):
    pass

class MitigationActionResponse(MitigationActionBase):
    id: int
    plan_id: int
    status: str
    
    class Config:
        from_attributes = True
