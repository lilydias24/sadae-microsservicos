from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import Response
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
        def __init__(self):
            self.services = {
            "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),  
            "core": os.getenv("CORE_SERVICE_URL", "http://core-service:8000")   
        }
    
        def get_service_url(self, service_name: str) -> str:
            """Get service URL by name"""
        # ✅ Mapear todos os módulos para core service
            if service_name in ["billing", "support", "maintenance", "monitoring"]:
                return self.services.get("core")
            return self.services.get(service_name, "http://localhost:8000")
    
    service_registry = ServiceRegistry()

app = FastAPI(
    title="SADAE API Gateway",
    description="API Gateway for SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and get current user"""
    token = credentials.credentials
    payload = verify_token(token)
    return payload

async def proxy_request_to_service(
    service_name: str,
    method: str,
    endpoint: str,
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = None,
    timeout: float = 30.0
):
    """Helper function to proxy requests to services, reducing code duplication"""
    url = f"{service_registry.get_service_url(service_name)}{endpoint}"
    
    headers = {}
    if credentials:
        headers["Authorization"] = f"Bearer {credentials.credentials}"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        body = None
        if request and method.upper() in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            headers["content-type"] = "application/json"
        
        params = dict(request.query_params) if request else {}
        
        if method.upper() == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = await client.post(url, content=body, headers=headers, params=params)
        elif method.upper() == "PUT":
            response = await client.put(url, content=body, headers=headers, params=params)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers, params=params)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
        
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json() if response.text else {}

@app.get("/")
async def root():
    return {"message": "SADAE API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

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
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            auth_url = service_registry.get_service_url('auth')
            print(f"🔍 Proxying login to: {auth_url}/login")
            
            response = await client.post(
                f"{auth_url}/login",
                content=body,
                headers={"content-type": "application/json"}
            )
            
            print(f"✅ Auth service response: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Auth service error: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
            return response.json()
            
    except httpx.ConnectError as e:
        print(f"❌ Connection error to auth service: {e}")
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")

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

@app.get("/auth/me")
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('auth')}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.put("/auth/me")
async def update_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Update current user information"""
    token = credentials.credentials
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{service_registry.get_service_url('auth')}/me",
            content=body,
            headers={
                "Authorization": f"Bearer {token}",
                "content-type": "application/json"
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

# Monitoring routes
@app.get("/monitoring/sensors")
async def get_sensors(current_user: dict = Depends(get_current_user)):
    """Get all sensors data"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('core')}/monitoring/sensors",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.get("/monitoring/readings/realtime")
async def get_realtime_readings(current_user: dict = Depends(get_current_user)):
    """Get real-time sensor readings"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('core')}/monitoring/readings/realtime",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/monitoring/anomalies")
async def create_anomaly(request: Request, current_user: dict = Depends(get_current_user)):
    """Create anomaly alert"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('core')}/monitoring/anomalies",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {current_user}"
            }
        )
        return response.json()
# Teams routes
@app.get("/maintenance/teams")
async def get_teams(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get maintenance teams"""
    try:
        # Skip token validation for debug
        core_url = service_registry.get_service_url('core')
        print(f"🔍 Proxying to: {core_url}/maintenance/teams")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{core_url}/maintenance/teams",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            
            print(f"✅ Teams response: {response.status_code}")
            print(f"✅ Teams content: {response.text[:200]}...")
            
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            if not response.text.strip():
                return {"data": [], "message": "No teams available"}
            
            try:
                return response.json()
            except ValueError:
                return {"data": [], "error": "Invalid JSON response"}
                
    except Exception as e:
        print(f"❌ Teams error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# Complaints routes
@app.get("/maintenance/complaints")
async def get_complaints(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get maintenance complaints"""
    try:
        core_url = service_registry.get_service_url('core')
        print(f"🔍 Proxying to: {core_url}/maintenance/complaints")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{core_url}/maintenance/complaints",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            
            print(f"✅ Complaints response: {response.status_code}")
            print(f"✅ Complaints content: {response.text[:200]}...")
            
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            if not response.text.strip():
                return {"data": [], "message": "No complaints available"}
            
            try:
                return response.json()
            except ValueError:
                return {"data": [], "error": "Invalid JSON response"}
                
    except Exception as e:
        print(f"❌ Complaints error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Maintenance routes
@app.get("/maintenance/orders")
async def get_service_orders(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get service orders"""
    try:
        # Verificar token (usando função fallback se necessário)
        try:
            verify_token(credentials.credentials)
        except Exception as e:
            print(f"Warning: Token validation failed: {e}")
            # Para debug, pular validação temporariamente
            pass
        
        # Obter URL do core service
        core_url = service_registry.get_service_url('core')
        print(f"🔍 Proxying to: {core_url}/maintenance/orders")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{core_url}/maintenance/orders",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            
            print(f"✅ Core service response: {response.status_code}")
            print(f"✅ Core service content: {response.text[:200]}...")
            
            # Verificar se a resposta é válida
            if response.status_code >= 400:
                print(f"❌ Core service error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Core service error: {response.text}"
                )
            
            # Verificar se tem conteúdo para fazer parse JSON
            if not response.text.strip():
                print("❌ Empty response from core service")
                return {"data": [], "message": "No data available"}
            
            try:
                return response.json()
            except ValueError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"❌ Response content: {response.text}")
                return {"data": [], "error": "Invalid JSON response from core service"}
            
    except httpx.ConnectError as e:
        print(f"❌ Connection error to core service: {e}")
        raise HTTPException(status_code=503, detail=f"Core service unavailable: {e}")
    except httpx.TimeoutException as e:
        print(f"❌ Timeout error: {e}")
        raise HTTPException(status_code=504, detail=f"Core service timeout: {e}")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.post("/maintenance/orders")
async def create_service_order(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create service order"""
    verify_token(credentials.credentials) 
    
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('core')}/maintenance/orders",
            content=body,
            headers={
                "content-type": "application/json",
                "Authorization": f"Bearer {credentials.credentials}"
            }
        )
        return response.json()

@app.put("/maintenance/orders/{order_id}/assign")
async def assign_work_order(
    order_id: int, 
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Assign work order to team"""
    verify_token(credentials.credentials)
    
    # Pegar parâmetros da query string
    params = dict(request.query_params)
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{service_registry.get_service_url('core')}/maintenance/orders/{order_id}/assign",
            params=params,
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

# Billing routes
@app.get("/billing/bills")
async def get_bills(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get bills"""
    verify_token(credentials.credentials)
    return await proxy_request_to_service("core", "GET", "/billing/bills", request, credentials)

@app.post("/billing/contests")
async def create_bill_contest(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Contest a bill"""
    verify_token(credentials.credentials)
    return await proxy_request_to_service("core", "POST", "/billing/contests", request, credentials)

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
            f"{service_registry.get_service_url('core')}/billing/contests/{contest_id}/resolve",
            params=params,
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.get("/billing/contests")
async def get_contests(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all contests"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('core')}/billing/contests",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.post("/billing/debt-negotiations")
async def create_debt_negotiation(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a debt negotiation"""
    verify_token(credentials.credentials)
    return await proxy_request_to_service("core", "POST", "/billing/negotiations", request, credentials)

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
            f"{service_registry.get_service_url('core')}/billing/debt-negotiations/{negotiation_id}/resolve",
            params=params,
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.get("/billing/negotiations")
async def get_negotiations(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all negotiations"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('core')}/billing/negotiations",
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
            f"{service_registry.get_service_url('core')}/billing/negotiations",
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
            f"{service_registry.get_service_url('core')}/billing/payments",
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
            f"{service_registry.get_service_url('core')}/support/tickets",
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
            f"{service_registry.get_service_url('core')}/support/tickets",
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
            f"{service_registry.get_service_url('core')}/support/tickets/{ticket_id}",
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
            f"{service_registry.get_service_url('core')}/support/tickets/{ticket_id}",
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
            f"{service_registry.get_service_url('core')}/support/tickets/{ticket_id}/messages",
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
            f"{service_registry.get_service_url('core')}/support/tickets/{ticket_id}/messages",
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
            f"{service_registry.get_service_url('core')}/support/knowledge-base",
            params=params
        )
        return response.json()

@app.get("/support/knowledge-base/{article_id}")
async def get_knowledge_article(article_id: int):
    """Get knowledge base article (public)"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('core')}/support/knowledge-base/{article_id}"
        )
        return response.json()

@app.get("/support/dashboard")
async def get_support_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get support dashboard stats"""
    verify_token(credentials.credentials)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('core')}/support/dashboard",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        return response.json()

@app.get("/support/agent-dashboard")
async def get_agent_dashboard(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get agent dashboard stats"""
    verify_token(credentials.credentials)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('core')}/support/agent-dashboard",
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
            f"{service_registry.get_service_url('core')}/crisis/alerts",
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
            f"{service_registry.get_service_url('core')}/crisis/simulations",
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
            f"{service_registry.get_service_url('core')}/maintenance/public/complaints",
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
            f"{service_registry.get_service_url('core')}/monitoring/public/leak-reports",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

@app.options("/support/{path:path}")
async def support_options(path: str):
    """Handle CORS preflight for support routes"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true"
        }
    )
# Support service routes
@app.get("/support/health")
async def support_health_check():
    """Support service health check"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{service_registry.get_service_url('core')}/health")
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

@app.post("/public/support/tickets")
async def create_public_support_ticket(request: Request):
    """Create public support ticket"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('core')}/support/public/tickets",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

# Generic proxy function for easier routing
async def proxy_request(request: Request, service: str, path: str):
    """Generic proxy function to forward requests to core service"""
    method = request.method
    body = await request.body() if method in ["POST", "PUT", "PATCH"] else None
    
    # Get headers (preserve Authorization if present)
    headers = {"content-type": "application/json"}
    if "authorization" in [h.lower() for h in request.headers.keys()]:
        headers["Authorization"] = request.headers.get("authorization")
    
    async with httpx.AsyncClient() as client:
        upstream = await client.request(
            method=method,
            url=f"{service_registry.get_service_url(service)}{path}",
            content=body,
            headers=headers,
            params=dict(request.query_params)
        )
        # Return raw response preserving status and content type to avoid JSON decode issues
        media_type = upstream.headers.get("content-type", "application/json")
        return Response(content=upstream.content, status_code=upstream.status_code, media_type=media_type)

# Generic routes for any missing endpoints
@app.api_route("/billing/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_billing_generic(request: Request, path: str):
    """Generic proxy for billing routes"""
    return await proxy_request(request, "core", f"/billing/{path}")

@app.api_route("/support/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_support_generic(request: Request, path: str):
    """Generic proxy for support routes"""
    return await proxy_request(request, "core", f"/support/{path}")

@app.api_route("/maintenance/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_maintenance_generic(request: Request, path: str):
    """Generic proxy for maintenance routes"""
    return await proxy_request(request, "core", f"/maintenance/{path}")

@app.api_route("/monitoring/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_monitoring_generic(request: Request, path: str):
    """Generic proxy for monitoring routes"""
    return await proxy_request(request, "core", f"/monitoring/{path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
