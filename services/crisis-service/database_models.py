from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class CriticalEvent(Base):
    __tablename__ = "critical_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)  # flood, drought, contamination, etc.
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    location = Column(String(200), nullable=False)
    coordinates = Column(JSON)  # {"lat": float, "lng": float}
    affected_population = Column(Integer)
    status = Column(String(50), default="active")  # active, resolved, alert_sent
    sensor_data = Column(JSON)  # Related sensor readings
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    alerts = relationship("CivilDefenseAlert", back_populates="event")

class CivilDefenseAlert(Base):
    __tablename__ = "civil_defense_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("critical_events.id"), nullable=False)
    message = Column(Text, nullable=False)
    urgency_level = Column(String(20), nullable=False)  # low, medium, high, immediate
    affected_areas = Column(JSON)  # List of affected areas
    recommended_actions = Column(JSON)  # List of recommended actions
    sent_by = Column(Integer, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    
    # Relationships
    event = relationship("CriticalEvent", back_populates="alerts")

class EvacuationRoute(Base):
    __tablename__ = "evacuation_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    area = Column(String(200), nullable=False)
    start_point = Column(JSON, nullable=False)  # {"lat": float, "lng": float, "name": str}
    end_point = Column(JSON, nullable=False)    # {"lat": float, "lng": float, "name": str}
    waypoints = Column(JSON)  # List of intermediate points
    distance_km = Column(Float)
    estimated_time = Column(Integer)  # Minutes
    capacity = Column(Integer)  # Number of people
    accessibility = Column(String(100))  # wheelchair, elderly, etc.
    status = Column(String(20), default="active")  # active, blocked, maintenance
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class CrisisSimulation(Base):
    __tablename__ = "crisis_simulations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    scenario_type = Column(String(100), nullable=False)  # drought, flood, contamination
    description = Column(Text)
    parameters = Column(JSON, nullable=False)  # Simulation parameters
    duration_days = Column(Integer, nullable=False)
    affected_areas = Column(JSON)  # List of affected areas
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    results = Column(JSON)  # Simulation results
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    mitigation_plans = relationship("MitigationPlan", back_populates="simulation")

class MitigationPlan(Base):
    __tablename__ = "mitigation_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    simulation_id = Column(Integer, ForeignKey("crisis_simulations.id"))
    scenario_type = Column(String(100), nullable=False)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    estimated_cost = Column(Float)
    implementation_time = Column(Integer)  # Days
    effectiveness_score = Column(Float)  # 0-100
    status = Column(String(20), default="proposed")  # proposed, approved, implemented
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    implemented_at = Column(DateTime)
    
    # Relationships
    simulation = relationship("CrisisSimulation", back_populates="mitigation_plans")
    actions = relationship("MitigationAction", back_populates="plan")

class MitigationAction(Base):
    __tablename__ = "mitigation_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("mitigation_plans.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    action_type = Column(String(100), nullable=False)  # infrastructure, operational, emergency
    responsible_entity = Column(String(200))
    trigger_condition = Column(String(500))  # When to execute this action
    estimated_cost = Column(Float)
    duration_hours = Column(Integer)
    priority = Column(Integer, default=1)  # Execution order
    status = Column(String(20), default="planned")  # planned, in_progress, completed
    
    # Relationships
    plan = relationship("MitigationPlan", back_populates="actions")
