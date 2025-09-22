from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import sys

# Add shared modules to path
sys.path.append('/app/shared')

try:
    from auth import verify_token
    from utils import service_registry
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    # Fallback function
    def verify_token(token: str):
        return {"sub": "fallback_user", "user_id": "1", "role": "user"}
    
    # Fallback service registry
    service_registry = {}

app = FastAPI(
    title="SADAE API Gateway",
    description="API Gateway for SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and get current user"""
    token = credentials.credentials
    payload = verify_token(token)
    return payload

@app.get("/")
async def root():
    return {"message": "SADAE API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# Authentication routes
@app.post("/auth/login")
async def login(request: Request):
    """Proxy login request to auth service"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('auth')}/login",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

@app.post("/auth/register")
async def register(request: Request):
    """Proxy register request to auth service"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('auth')}/register",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

# Monitoring routes
@app.get("/monitoring/sensors")
async def get_sensors(current_user: dict = Depends(get_current_user)):
    """Get all sensors data"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('monitoring')}/sensors",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.get("/monitoring/readings/realtime")
async def get_realtime_readings(current_user: dict = Depends(get_current_user)):
    """Get real-time sensor readings"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('monitoring')}/readings/realtime",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/monitoring/anomalies")
async def create_anomaly(request: Request, current_user: dict = Depends(get_current_user)):
    """Create anomaly alert"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('monitoring')}/anomalies",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {current_user}"
            }
        )
        return response.json()

# Maintenance routes
@app.get("/maintenance/orders")
async def get_service_orders(current_user: dict = Depends(get_current_user)):
    """Get service orders"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('maintenance')}/orders",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/maintenance/orders")
async def create_service_order(request: Request, current_user: dict = Depends(get_current_user)):
    """Create service order"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('maintenance')}/orders",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {current_user}"
            }
        )
        return response.json()

# Billing routes
@app.get("/billing/bills")
async def get_bills(current_user: dict = Depends(get_current_user)):
    """Get bills"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('billing')}/bills",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/billing/contests")
async def create_bill_contest(request: Request, current_user: dict = Depends(get_current_user)):
    """Contest a bill"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('billing')}/contests",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {current_user}"
            }
        )
        return response.json()

# Crisis management routes
@app.post("/crisis/alerts")
async def create_crisis_alert(request: Request, current_user: dict = Depends(get_current_user)):
    """Create crisis alert"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('crisis')}/alerts",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {current_user}"
            }
        )
        return response.json()

@app.post("/crisis/simulations")
async def create_simulation(request: Request, current_user: dict = Depends(get_current_user)):
    """Create crisis simulation"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('crisis')}/simulations",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {current_user}"
            }
        )
        return response.json()

# Public routes (for citizens)
@app.post("/public/complaints")
async def create_complaint(request: Request):
    """Create public complaint"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('maintenance')}/public/complaints",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

@app.post("/public/leak-reports")
async def report_leak(request: Request):
    """Report water leak"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('monitoring')}/public/leak-reports",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

# Support service routes
@app.get("/support/health")
async def support_health_check():
    """Support service health check"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://support-service:8000/health")
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

@app.get("/support/tickets")
async def get_support_tickets(current_user: dict = Depends(get_current_user)):
    """Get support tickets"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/tickets",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/support/tickets")
async def create_support_ticket(request: Request, current_user: dict = Depends(get_current_user)):
    """Create support ticket"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('support')}/tickets",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {current_user}"
            }
        )
        return response.json()

@app.get("/support/tickets/{ticket_id}")
async def get_support_ticket(ticket_id: int, current_user: dict = Depends(get_current_user)):
    """Get support ticket by ID"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/support/tickets/{ticket_id}/messages")
async def create_ticket_message(ticket_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """Add message to support ticket"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('support')}/tickets/{ticket_id}/messages",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {current_user}"
            }
        )
        return response.json()

@app.get("/support/knowledge-base")
async def get_knowledge_base():
    """Get knowledge base articles"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/knowledge-base"
        )
        return response.json()

@app.get("/support/dashboard")
async def get_support_dashboard(current_user: dict = Depends(get_current_user)):
    """Get support dashboard metrics"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/dashboard",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.get("/support/agent-dashboard")
async def get_support_agent_dashboard(current_user: dict = Depends(get_current_user)):
    """Get support agent specific dashboard metrics"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/agent-dashboard",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/public/support/tickets")
async def create_public_support_ticket(request: Request):
    """Create public support ticket"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('support')}/public/tickets",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
