from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import sys

# Adiciona os módulos compartilhados ao caminho Python
sys.path.append('/app/shared')

try:
    from auth import verify_token
    from utils import service_registry
except ImportError as e:
    print(f"Aviso: Não foi possível importar módulos compartilhados: {e}")
    # Função de fallback para desenvolvimento local
    def verify_token(token: str):
        return {"sub": "fallback_user", "user_id": "1", "role": "user"}
    
    # Registry de serviços de fallback
    service_registry = {}

# Aplicação FastAPI principal - Gateway de entrada para todos os microsserviços
app = FastAPI(
    title="SADAE API Gateway",
    description="Gateway API para SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto",
    version="1.0.0"
)

# Middleware CORS - Permite requisições do frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],  # URLs permitidas do frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# Esquema de segurança HTTP Bearer para JWT tokens
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica o token JWT e retorna os dados do usuário atual
    
    Args:
        credentials: Credenciais HTTP Bearer com token JWT
        
    Returns:
        dict: Dados do usuário decodificados do token
    """
    token = credentials.credentials
    payload = verify_token(token)
    return payload

@app.get("/")
async def root():
    """Endpoint raiz - Informações básicas do gateway"""
    return {"message": "SADAE API Gateway", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Verificação de saúde do gateway - Status operacional"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# Rotas de Autenticação - Proxy para o serviço de autenticação
@app.post("/auth/login")
async def login(request: Request):
    """
    Proxy da requisição de login para o serviço de autenticação
    
    Args:
        request: Requisição HTTP com dados de login (email, senha)
        
    Returns:
        dict: Token JWT e dados do usuário autenticado
    """
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
    """
    Proxy da requisição de registro para o serviço de autenticação
    
    Args:
        request: Requisição HTTP com dados de registro (nome, email, senha, role)
        
    Returns:
        dict: Usuário criado e token de acesso
    """
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{service_registry.get_service_url('auth')}/register",
            content=body,
            headers={"content-type": "application/json"}
        )
        return response.json()

# Rotas de Monitoramento - Proxy para o serviço de monitoramento de sensores
@app.get("/monitoring/sensors")
async def get_sensors(current_user: dict = Depends(get_current_user)):
    """
    Obtém dados de todos os sensores IoT do sistema
    
    Args:
        current_user: Usuário autenticado via JWT
        
    Returns:
        list: Lista com todos os sensores e seus dados atuais
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('monitoring')}/sensors",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.get("/monitoring/readings/realtime")
async def get_realtime_readings(current_user: dict = Depends(get_current_user)):
    """
    Obtém leituras de sensores em tempo real via WebSocket
    
    Args:
        current_user: Usuário autenticado via JWT
        
    Returns:
        dict: Dados em tempo real dos sensores (pressão, vazão, temperatura)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('monitoring')}/readings/realtime",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/monitoring/anomalies")
async def create_anomaly(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Cria um alerta de anomalia no sistema de monitoramento
    
    Args:
        request: Requisição HTTP com dados da anomalia (sensor_id, type, severity)
        current_user: Usuário autenticado via JWT
        
    Returns:
        dict: Anomalia criada com ID e timestamp
    """
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

# Rotas de Manutenção - Proxy para o serviço de manutenção e ordens de serviço
@app.get("/maintenance/orders")
async def get_service_orders(current_user: dict = Depends(get_current_user)):
    """
    Obtém todas as ordens de serviço de manutenção
    
    Args:
        current_user: Usuário autenticado via JWT
        
    Returns:
        list: Lista de ordens de serviço com status, prioridade e equipe responsável
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('maintenance')}/orders",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/maintenance/orders")
async def create_service_order(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Cria uma nova ordem de serviço de manutenção
    
    Args:
        request: Requisição HTTP com dados da ordem (descrição, prioridade, sensor_id, local)
        current_user: Usuário autenticado via JWT
        
    Returns:
        dict: Ordem de serviço criada com ID, status e equipe atribuída
    """
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

# Rotas de Faturamento - Proxy para o serviço de faturamento e cobrança
@app.get("/billing/bills")
async def get_bills(current_user: dict = Depends(get_current_user)):
    """
    Obtém todas as faturas de água e esgoto do usuário
    
    Args:
        current_user: Usuário autenticado via JWT
        
    Returns:
        list: Lista de faturas com valores, vencimentos e status de pagamento
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{service_registry.get_service_url('billing')}/bills",
            headers={"Authorization": f"Bearer {current_user}"}
        )
        return response.json()

@app.post("/billing/contests")
async def create_bill_contest(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Cria uma contestação de fatura para revisão
    
    Args:
        request: Requisição HTTP com dados da contestação (bill_id, motivo, evidências)
        current_user: Usuário autenticado via JWT
        
    Returns:
        dict: Contestação criada com protocolo e prazo para análise
    """
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

# Rotas de Gestão de Crises - Proxy para o serviço de emergências hídricas
@app.post("/crisis/alerts")
async def create_crisis_alert(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Cria um alerta de situação crítica no abastecimento
    
    Args:
        request: Requisição HTTP com dados da crise (tipo, localização, severidade)
        current_user: Usuário autenticado via JWT
        
    Returns:
        dict: Alerta de crise criado com plano de evacuação e recursos necessários
    """
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
