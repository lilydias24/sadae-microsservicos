from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import os
import sys
import httpx
import asyncio
from datetime import datetime, timedelta
import json

# Add shared directory to path
sys.path.append('/app/shared')
from auth import get_current_user, require_roles
from database import get_db, get_db_session
from utils import send_notification

from database_models import *
from schemas import *
from crisis_analyzer import CrisisAnalyzer
from simulation_engine import SimulationEngine
from route_calculator import RouteCalculator

app = FastAPI(title="Crisis Management Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
crisis_analyzer = CrisisAnalyzer()
simulation_engine = SimulationEngine()
route_calculator = RouteCalculator()

# Database setup
DATABASE_URL = os.getenv("CRISIS_DATABASE_URL", "postgresql://user:password@crisis-db:5432/crisis_db")

@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    try:
        # Create database if it doesn't exist
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        
        # Start crisis monitoring
        asyncio.create_task(monitor_critical_events())
        
    except Exception as e:
        print(f"Startup error: {e}")

# Crisis Events Management
@app.get("/events/critical", response_model=List[CriticalEventResponse])
async def get_critical_events(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get critical events"""
    require_roles(current_user, ["crisis_manager", "operator"])
    
    query = db.query(CriticalEvent)
    if status:
        query = query.filter(CriticalEvent.status == status)
    
    events = query.offset(skip).limit(limit).all()
    return events

@app.post("/events/critical", response_model=CriticalEventResponse)
async def create_critical_event(
    event_data: CriticalEventCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a critical event"""
    require_roles(current_user, ["crisis_manager"])
    
    event = CriticalEvent(
        **event_data.dict(),
        created_by=current_user["user_id"],
        created_at=datetime.utcnow()
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Send alert to Civil Defense
    if event.severity in ["high", "critical"]:
        background_tasks.add_task(send_civil_defense_alert, event.id)
    
    return event

@app.post("/events/{event_id}/alert-civil-defense")
async def send_alert_to_civil_defense(
    event_id: int,
    alert_data: CivilDefenseAlertCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send alert to Civil Defense (RF008)"""
    require_roles(current_user, ["crisis_manager"])
    
    event = db.query(CriticalEvent).filter(CriticalEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Create alert record
    alert = CivilDefenseAlert(
        event_id=event_id,
        message=alert_data.message,
        urgency_level=alert_data.urgency_level,
        affected_areas=alert_data.affected_areas,
        recommended_actions=alert_data.recommended_actions,
        sent_by=current_user["user_id"],
        sent_at=datetime.utcnow()
    )
    
    db.add(alert)
    
    # Update event status
    event.status = "alert_sent"
    event.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Send notification (simulated)
    await send_notification(
        "civil_defense",
        f"ALERTA CRÍTICO: {alert_data.message}",
        {
            "event_id": event_id,
            "urgency": alert_data.urgency_level,
            "areas": alert_data.affected_areas
        }
    )
    
    return {"message": "Alert sent to Civil Defense successfully"}

# Route Management
@app.get("/routes/evacuation", response_model=List[EvacuationRouteResponse])
async def get_evacuation_routes(
    area: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get evacuation routes"""
    require_roles(current_user, ["crisis_manager", "operator"])
    
    query = db.query(EvacuationRoute)
    if area:
        query = query.filter(EvacuationRoute.area.contains(area))
    
    routes = query.all()
    return routes

@app.post("/routes/evacuation/recalculate")
async def recalculate_evacuation_routes(
    recalc_data: RouteRecalculationRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recalculate evacuation routes (RF009)"""
    require_roles(current_user, ["crisis_manager"])
    
    try:
        # Use route calculator to find new routes
        new_routes = await route_calculator.calculate_evacuation_routes(
            affected_area=recalc_data.affected_area,
            blocked_points=recalc_data.blocked_points,
            safe_zones=recalc_data.safe_zones
        )
        
        # Save new routes
        for route_data in new_routes:
            route = EvacuationRoute(
                name=route_data["name"],
                area=recalc_data.affected_area,
                start_point=route_data["start_point"],
                end_point=route_data["end_point"],
                waypoints=route_data["waypoints"],
                estimated_time=route_data["estimated_time"],
                capacity=route_data["capacity"],
                status="active",
                created_by=current_user["user_id"],
                created_at=datetime.utcnow()
            )
            db.add(route)
        
        db.commit()
        
        # Notify Civil Defense about new routes
        await send_notification(
            "civil_defense",
            f"Novas rotas de evacuação calculadas para {recalc_data.affected_area}",
            {"routes_count": len(new_routes)}
        )
        
        return {
            "message": "Evacuation routes recalculated successfully",
            "routes_count": len(new_routes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recalculating routes: {str(e)}")

# Simulation Management
@app.get("/simulations", response_model=List[SimulationResponse])
async def get_simulations(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get crisis simulations"""
    require_roles(current_user, ["crisis_manager"])
    
    simulations = db.query(CrisisSimulation).offset(skip).limit(limit).all()
    return simulations

@app.post("/simulations", response_model=SimulationResponse)
async def create_simulation(
    simulation_data: SimulationCreate,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create and run crisis simulation (RF020)"""
    require_roles(current_user, ["crisis_manager"])
    
    simulation = CrisisSimulation(
        name=simulation_data.name,
        scenario_type=simulation_data.scenario_type,
        parameters=simulation_data.parameters,
        duration_days=simulation_data.duration_days,
        affected_areas=simulation_data.affected_areas,
        status="running",
        created_by=current_user["user_id"],
        created_at=datetime.utcnow()
    )
    
    db.add(simulation)
    db.commit()
    db.refresh(simulation)
    
    # Run simulation in background
    background_tasks.add_task(run_simulation, simulation.id)
    
    return simulation

@app.get("/simulations/{simulation_id}/results")
async def get_simulation_results(
    simulation_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get simulation results"""
    require_roles(current_user, ["crisis_manager"])
    
    simulation = db.query(CrisisSimulation).filter(CrisisSimulation.id == simulation_id).first()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return {
        "simulation": simulation,
        "results": simulation.results,
        "status": simulation.status
    }

# Mitigation Plans
@app.get("/mitigation-plans", response_model=List[MitigationPlanResponse])
async def get_mitigation_plans(
    simulation_id: Optional[int] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get mitigation plans"""
    require_roles(current_user, ["crisis_manager"])
    
    query = db.query(MitigationPlan)
    if simulation_id:
        query = query.filter(MitigationPlan.simulation_id == simulation_id)
    
    plans = query.all()
    return plans

@app.post("/mitigation-plans", response_model=MitigationPlanResponse)
async def create_mitigation_plan(
    plan_data: MitigationPlanCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create mitigation plan (RF021)"""
    require_roles(current_user, ["crisis_manager"])
    
    # Verify simulation exists
    if plan_data.simulation_id:
        simulation = db.query(CrisisSimulation).filter(
            CrisisSimulation.id == plan_data.simulation_id
        ).first()
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
    
    plan = MitigationPlan(
        **plan_data.dict(),
        created_by=current_user["user_id"],
        created_at=datetime.utcnow()
    )
    
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return plan

@app.post("/mitigation-plans/{plan_id}/actions", response_model=MitigationActionResponse)
async def add_mitigation_action(
    plan_id: int,
    action_data: MitigationActionCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add action to mitigation plan"""
    require_roles(current_user, ["crisis_manager"])
    
    plan = db.query(MitigationPlan).filter(MitigationPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    action = MitigationAction(
        plan_id=plan_id,
        **action_data.dict()
    )
    
    db.add(action)
    db.commit()
    db.refresh(action)
    
    return action

# Background Tasks
async def monitor_critical_events():
    """Monitor sensor data for critical events"""
    while True:
        try:
            # Get latest sensor data from monitoring service
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://monitoring-service:8000/sensors/readings/latest",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    readings = response.json()
                    
                    # Analyze for critical conditions
                    critical_events = await crisis_analyzer.analyze_readings(readings)
                    
                    # Create events if found
                    if critical_events:
                        db = get_db_session("crisis")
                        for event_data in critical_events:
                            event = CriticalEvent(**event_data)
                            db.add(event)
                        db.commit()
                        db.close()
                        
        except Exception as e:
            print(f"Error monitoring critical events: {e}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

async def send_civil_defense_alert(event_id: int):
    """Send alert to Civil Defense"""
    try:
        db = get_db_session("crisis")
        event = db.query(CriticalEvent).filter(CriticalEvent.id == event_id).first()
        
        if event:
            # Simulate sending to Civil Defense system
            await send_notification(
                "civil_defense",
                f"ALERTA AUTOMÁTICO: {event.event_type} - {event.description}",
                {
                    "event_id": event_id,
                    "severity": event.severity,
                    "location": event.location
                }
            )
            
            # Update event status
            event.status = "alert_sent"
            event.updated_at = datetime.utcnow()
            db.commit()
        
        db.close()
        
    except Exception as e:
        print(f"Error sending Civil Defense alert: {e}")

async def run_simulation(simulation_id: int):
    """Run crisis simulation"""
    try:
        db = get_db_session("crisis")
        simulation = db.query(CrisisSimulation).filter(CrisisSimulation.id == simulation_id).first()
        
        if simulation:
            # Run simulation using simulation engine
            results = await simulation_engine.run_simulation(
                scenario_type=simulation.scenario_type,
                parameters=simulation.parameters,
                duration_days=simulation.duration_days,
                affected_areas=simulation.affected_areas
            )
            
            # Update simulation with results
            simulation.results = results
            simulation.status = "completed"
            simulation.completed_at = datetime.utcnow()
            db.commit()
        
        db.close()
        
    except Exception as e:
        print(f"Error running simulation: {e}")
        # Update simulation status to failed
        db = get_db_session("crisis")
        simulation = db.query(CrisisSimulation).filter(CrisisSimulation.id == simulation_id).first()
        if simulation:
            simulation.status = "failed"
            simulation.results = {"error": str(e)}
            db.commit()
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
