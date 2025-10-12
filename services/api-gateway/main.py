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
    from utils import ServiceRegistry
    # Create service registry instance
    service_registry = ServiceRegistry()
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    # Fallback function
    def verify_token(token: str):
        return {"sub": "fallback_user", "user_id": "1", "role": "user"}
    
    # Fallback service registry
    class ServiceRegistry:
        def get_service_url(self, service_name: str) -> str:
            fallback_urls = {
                "auth": "http://auth-service:8001",
                "billing": "http://billing-service:8004",
                "support": "http://support-service:8000"
            }
            return fallback_urls.get(service_name, "http://localhost:8000")
    
    service_registry = ServiceRegistry()

app = FastAPI(
    title="SADAE API Gateway",
    description="API Gateway for SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # broadened for local dev to avoid CORS blocks
    allow_credentials=False,
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

# Redirect legacy support routes to proper prefixed routes
@app.get("/tickets")
async def redirect_tickets():
    """Redirect legacy /tickets to /support/tickets"""
    raise HTTPException(status_code=301, detail="Moved to /support/tickets", headers={"Location": "/support/tickets"})

@app.get("/agent-dashboard")
async def redirect_agent_dashboard():
    """Redirect legacy /agent-dashboard to /support/agent-dashboard"""
    raise HTTPException(status_code=301, detail="Moved to /support/agent-dashboard", headers={"Location": "/support/agent-dashboard"})

@app.post("/tickets")
async def redirect_post_tickets():
    """Redirect legacy POST /tickets to /support/tickets"""
    raise HTTPException(status_code=301, detail="Moved to /support/tickets", headers={"Location": "/support/tickets"})

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
async def get_bills(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get bills"""
    # Verify token first
    verify_token(credentials.credentials)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('billing')}/bills",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.post("/billing/contests")
async def create_bill_contest(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Contest a bill"""
    # Verify token first
    verify_token(credentials.credentials)
    
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('billing')}/contests",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {credentials.credentials}"
            }
        )
        return response.json()

@app.put("/billing/contests/{contest_id}/resolve")
async def resolve_bill_contest(
    contest_id: str, 
    resolution: str, 
    approved: bool,
    new_amount: float = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Resolve a bill contest"""
    # Verify token first
    verify_token(credentials.credentials)
    
    params = {
        "resolution": resolution,
        "approved": str(approved).lower()
    }
    if new_amount is not None:
        params["new_amount"] = str(new_amount)
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{service_registry.get_service_url('billing')}/contests/{contest_id}/resolve",
            params=params,
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.get("/billing/contests")
async def get_contests(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all contests"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('billing')}/contests",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.post("/billing/debt-negotiations")
async def create_debt_negotiation(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a debt negotiation"""
    # Verify token first
    verify_token(credentials.credentials)
    
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('billing')}/negotiations",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {credentials.credentials}"
            }
        )
        return response.json()

@app.put("/billing/debt-negotiations/{negotiation_id}/resolve")
async def resolve_debt_negotiation(
    negotiation_id: str, 
    approved: bool,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Resolve a debt negotiation"""
    # Verify token first
    verify_token(credentials.credentials)
    
    params = {
        "approved": str(approved).lower()
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{service_registry.get_service_url('billing')}/debt-negotiations/{negotiation_id}/resolve",
            params=params,
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.get("/billing/negotiations")
async def get_negotiations(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all negotiations"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('billing')}/negotiations",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.post("/billing/negotiations")
async def create_negotiation(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create new negotiation"""
    body = await request.body()
    print(f"🔍 API Gateway - Creating negotiation with body: {body}")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('billing')}/negotiations",
            headers={"Authorization": f"Bearer {credentials.credentials}", "Content-Type": "application/json"},
            content=body
        )
        print(f"🔍 API Gateway - Response status: {response.status_code}")
        print(f"🔍 API Gateway - Response text: {response.text}")
        if response.status_code == 422:
            raise HTTPException(status_code=422, detail=response.text)
        return response.json()

@app.post("/billing/payments")
async def process_payment(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Process payment"""
    body = await request.body()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('billing')}/payments",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {credentials.credentials}"
            }
        )
        return response.json()

# Support routes
@app.get("/support/tickets")
async def get_support_tickets(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get support tickets"""
    verify_token(credentials.credentials)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/tickets",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.post("/support/tickets")
async def create_support_ticket(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create support ticket"""
    verify_token(credentials.credentials)
    
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('support')}/tickets",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {credentials.credentials}"
            }
        )
        return response.json()

@app.get("/support/tickets/{ticket_id}")
async def get_support_ticket(ticket_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get specific support ticket"""
    verify_token(credentials.credentials)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.put("/support/tickets/{ticket_id}")
async def update_support_ticket(ticket_id: int, request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update support ticket"""
    verify_token(credentials.credentials)
    
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{service_registry.get_service_url('support')}/tickets/{ticket_id}",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {credentials.credentials}"
            }
        )
        return response.json()

@app.get("/support/tickets/{ticket_id}/messages")
async def get_ticket_messages(ticket_id: int, include_internal: bool = False, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get ticket messages"""
    verify_token(credentials.credentials)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/tickets/{ticket_id}/messages",
            params={"include_internal": include_internal},
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.post("/support/tickets/{ticket_id}/messages")
async def create_ticket_message(ticket_id: int, request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create ticket message"""
    verify_token(credentials.credentials)
    
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('support')}/tickets/{ticket_id}/messages",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {credentials.credentials}"
            }
        )
        return response.json()

@app.get("/support/knowledge-base")
async def get_knowledge_base(category: str = None, featured_only: bool = False):
    """Get knowledge base articles (public)"""
    async with httpx.AsyncClient() as client:
        params = {}
        if category:
            params["category"] = category
        if featured_only:
            params["featured_only"] = featured_only
            
        response = await client.get(
            f"{service_registry.get_service_url('support')}/knowledge-base",
            params=params
        )
        return response.json()

@app.get("/support/knowledge-base/{article_id}")
async def get_knowledge_article(article_id: int):
    """Get knowledge base article (public)"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/knowledge-base/{article_id}"
        )
        return response.json()

@app.get("/support/dashboard")
async def get_support_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get support dashboard stats"""
    verify_token(credentials.credentials)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/dashboard",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.get("/support/agent-dashboard")
async def get_agent_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get agent dashboard stats"""
    verify_token(credentials.credentials)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('support')}/agent-dashboard",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
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
