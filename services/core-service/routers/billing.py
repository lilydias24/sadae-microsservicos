from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, Body, Response, Query, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field
import sys
import os

# Add shared modules to path
sys.path.append('/app/shared')

try:
    from shared.models import BillStatus, UserRole
    from shared.utils import generate_protocol_number, make_service_request, service_registry
    from shared.auth import verify_token
except ImportError as e:
    print(f"Warning: Could not import shared modules: {e}")
    # Criar fallbacks simples
    class BillStatus:
        PENDING = "pending"
        PAID = "paid"
        OVERDUE = "overdue"
    
    class UserRole:
        ADMIN = "admin"
        CITIZEN = "citizen"
        FINANCIAL_MANAGER = "financial_manager"
    
    def verify_token(token: str):
        return {"user_id": 1, "role": "admin"}
    
    def generate_protocol_number():
        from random import randint
        return f"PROT{randint(100000, 999999)}"

from database import get_db
from database_models import (
    Customer, WaterMeter, MeterReading, Bill, BillContest, 
    DebtNegotiation, Payment, TariffRate
)
from schemas.billing import (
    CustomerCreate, CustomerResponse,
    WaterMeterCreate, WaterMeterResponse,
    MeterReadingCreate, MeterReadingResponse,
    BillResponse, BillContestCreate, BillContestResponse,
    DebtNegotiationCreate, DebtNegotiationResponse,
    PaymentCreate, PaymentResponse,
    TariffRateCreate, TariffRateResponse
)
from business.billing_calculator import BillingCalculator

router = APIRouter()
security = HTTPBearer()

# Billing calculator
billing_calculator = BillingCalculator()

def verify_user_token(token: str) -> dict:
    """Verify JWT token and return user info
    
    Args:
        token: JWT token (without 'Bearer ' prefix) or full 'Bearer token' string
    
    Returns:
        dict with keys: id, name, email, role
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    
    payload = verify_token(token)
    
    # Normalize user data from JWT payload
    user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID do usuário não encontrado no payload"
        )
    
    # Convert to int if it's a string (required for database)
    if isinstance(user_id, str):
        try:
            user_id = int(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: ID do usuário não é um número válido: {user_id}"
            )
    
    return {
        "id": int(user_id),  # Ensure it's always an int
        "name": payload.get("name") or payload.get("username") or payload.get("full_name") or "Usuário",
        "email": payload.get("email") or "",
        "role": payload.get("role") or "citizen"
    }

# Test endpoint (temporary - no auth required)
@router.get("/test-data")
async def get_test_data(db: Session = Depends(get_db)):
    """Get test data without authentication (temporary endpoint)"""
    bills = db.query(Bill).limit(5).all()
    customers = db.query(Customer).limit(3).all()
    contests = db.query(BillContest).limit(3).all()
    
    return {
        "bills": [
            {
                "id": bill.id,
                "customer_id": bill.customer_id,
                "amount": float(bill.amount),
                "consumption": bill.consumption,
                "due_date": bill.due_date.isoformat(),
                "status": bill.status,
                "created_at": bill.created_at.isoformat(),
                "billing_period_start": bill.billing_period_start.isoformat(),
                "billing_period_end": bill.billing_period_end.isoformat()
            } for bill in bills
        ],
        "customers": [
            {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "customer_type": customer.customer_type
            } for customer in customers
        ],
        "contests": [
            {
                "id": contest.id,
                "bill_id": contest.bill_id,
                "protocol_number": contest.protocol_number,
                "reason": contest.reason,
                "status": contest.status,
                "created_at": contest.created_at.isoformat()
            } for contest in contests
        ]
    }

# Customer Management
@router.post(
    "/customers",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo cliente",
    description="""
    Cria um novo cliente no sistema.
    
    **Requisitos:**
    - Apenas usuários com role `financial_manager` podem criar clientes
    - O documento (CPF/CNPJ) deve ser único no sistema
    
    **Validações:**
    - Email deve ser válido
    - Documento deve ter entre 11 e 14 caracteres (apenas números)
    - Tipo de cliente deve ser: residential, commercial ou industrial
    - Nome deve ter entre 3 e 200 caracteres
    """,
    responses={
        201: {
            "description": "Cliente criado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "João da Silva",
                        "document": "12345678900",
                        "email": "joao.silva@email.com",
                        "phone": "(55) 99999-9999",
                        "address": "Rua das Flores, 123, Centro, São Paulo - SP",
                        "customer_type": "residential",
                        "user_id": None,
                        "is_active": True,
                        "created_at": "2025-01-15T10:30:00",
                        "updated_at": "2025-01-15T10:30:00"
                    }
                }
            }
        }
    },
    tags=["Clientes"]
)
async def create_customer(
    req: Request,
    customer_data: CustomerCreate,
    db: Session = Depends(get_db)
):
    """
    Cria um novo cliente no sistema.
    
    Requer permissões de financial_manager.
    """
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != "financial_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Check if customer already exists
    existing = db.query(Customer).filter(Customer.document == customer_data.document).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer already exists")
    
    customer = Customer(**customer_data.dict())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer

@router.get(
    "/customers",
    response_model=List[CustomerResponse],
    summary="Listar clientes",
    description="""
    Lista todos os clientes do sistema com paginação.
    
    **Requisitos:**
    - Apenas usuários com role `financial_manager` podem ver todos os clientes
    
    **Paginação:**
    - Use `skip` para pular registros (padrão: 0)
    - Use `limit` para limitar resultados (padrão: 100, máximo: 1000)
    """,
    responses={
        200: {
            "description": "Lista de clientes retornada com sucesso",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "João da Silva",
                            "document": "12345678900",
                            "email": "joao.silva@email.com",
                            "phone": "(55) 99999-9999",
                            "address": "Rua das Flores, 123",
                            "customer_type": "residential",
                            "is_active": True,
                            "created_at": "2025-01-15T10:30:00",
                            "updated_at": "2025-01-15T10:30:00"
                        }
                    ]
                }
            }
        }
    },
    tags=["Clientes"]
)
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """
    Lista todos os clientes com paginação.
    
    Requer permissões de financial_manager.
    """
    user = await verify_user_token(authorization)
    if user["role"] != "financial_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers

@router.get(
    "/customers/{customer_id}",
    response_model=CustomerResponse,
    summary="Buscar cliente por ID",
    description="""
    Busca um cliente específico pelo seu ID.
    
    **Permissões:**
    - `financial_manager`: pode ver qualquer cliente
    - `citizen`: pode ver apenas seus próprios dados
    """,
    responses={
        200: {
            "description": "Cliente encontrado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "João da Silva",
                        "document": "12345678900",
                        "email": "joao.silva@email.com",
                        "phone": "(55) 99999-9999",
                        "address": "Rua das Flores, 123, Centro, São Paulo - SP",
                        "customer_type": "residential",
                        "user_id": None,
                        "is_active": True,
                        "created_at": "2025-01-15T10:30:00",
                        "updated_at": "2025-01-15T10:30:00"
                    }
                }
            }
        }
    },
    tags=["Clientes"]
)
async def get_customer(
    customer_id: int = Path(..., gt=0),
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """
    Busca um cliente específico pelo ID.
    
    Cidadãos podem ver apenas seus próprios dados.
    """
    user = await verify_user_token(authorization)
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    
    # Citizens can only see their own data
    if user["role"] == "citizen" and customer.user_id != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return customer

# Water Meter Management
@router.post("/meters", response_model=WaterMeterResponse)
async def create_water_meter(
    meter_data: WaterMeterCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """Create water meter (financial manager only)"""
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != "financial_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Check if meter ID already exists
    existing = db.query(WaterMeter).filter(WaterMeter.meter_id == meter_data.meter_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meter ID already exists")
    
    meter = WaterMeter(**meter_data.dict())
    db.add(meter)
    db.commit()
    db.refresh(meter)
    
    return meter

@router.get("/meters")
async def get_water_meters(
    customer_id: Optional[int] = None,
    active_only: bool = True,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """Get water meters"""
    user = await verify_user_token(authorization)
    
    query = db.query(WaterMeter)
    
    if customer_id:
        query = query.filter(WaterMeter.customer_id == customer_id)
    if active_only:
        query = query.filter(WaterMeter.is_active == True)
    
    # Citizens can only see their own meters
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if customer:
            query = query.filter(WaterMeter.customer_id == customer.id)
        else:
            return {"meters": []}
    
    meters = query.all()
    return {"meters": meters}

# Meter Reading Collection (from smart meters)
@router.post("/readings", response_model=MeterReadingResponse)
async def create_meter_reading(
    reading_data: MeterReadingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create meter reading (from smart meters - no auth required)"""
    
    # Verify meter exists
    meter = db.query(WaterMeter).filter(WaterMeter.meter_id == reading_data.meter_id).first()
    if not meter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Water meter not found")
    
    # Check for duplicate readings (same meter, same timestamp)
    existing = db.query(MeterReading).filter(
        MeterReading.meter_id == reading_data.meter_id,
        MeterReading.reading_date == reading_data.reading_date
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reading already exists for this date")
    
    # Validate reading value (should be increasing)
    last_reading = db.query(MeterReading).filter(
        MeterReading.meter_id == reading_data.meter_id
    ).order_by(MeterReading.reading_date.desc()).first()
    
    if last_reading and reading_data.reading_value < last_reading.reading_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Reading value cannot be less than previous reading"
        )
    
    reading = MeterReading(**reading_data.dict())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    
    # Check if it's time to generate a bill
    background_tasks.add_task(check_billing_cycle, meter.customer_id, db)
    
    return reading

@router.get("/readings")
async def get_meter_readings(
    meter_id: Optional[str] = None,
    customer_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """Get meter readings"""
    user = await verify_user_token(authorization)
    
    query = db.query(MeterReading)
    
    if meter_id:
        query = query.filter(MeterReading.meter_id == meter_id)
    if start_date:
        query = query.filter(MeterReading.reading_date >= start_date)
    if end_date:
        query = query.filter(MeterReading.reading_date <= end_date)
    
    # Citizens can only see their own readings
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if customer:
            meter_ids = [m.meter_id for m in db.query(WaterMeter).filter(WaterMeter.customer_id == customer.id).all()]
            if meter_ids:
                query = query.filter(MeterReading.meter_id.in_(meter_ids))
        else:
            return {"readings": []}
    elif customer_id:
        meter_ids = [m.meter_id for m in db.query(WaterMeter).filter(WaterMeter.customer_id == customer_id).all()]
        if meter_ids:
            query = query.filter(MeterReading.meter_id.in_(meter_ids))
    
    readings = query.order_by(MeterReading.reading_date.desc()).all()
    return {"readings": readings}

# Bill Management
@router.get(
    "/bills",
    response_model=List[BillResponse],
    summary="Listar faturas",
    description="""
    Lista faturas do sistema com filtros opcionais.
    
    **Permissões:**
    - `financial_manager`: pode ver todas as faturas
    - `citizen`: pode ver apenas suas próprias faturas
    
    **Filtros disponíveis:**
    - `customer_id`: filtrar por cliente específico
    - `status`: filtrar por status (pending, paid, overdue, contested)
    - `skip` e `limit`: paginação
    
    **Status possíveis:**
    - `pending`: Fatura pendente de pagamento
    - `paid`: Fatura paga
    - `overdue`: Fatura vencida
    - `contested`: Fatura contestada
    """,
    responses={
        200: {
            "description": "Lista de faturas retornada com sucesso",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "customer_id": 5,
                            "meter_id": "WM-001",
                            "amount": 125.75,
                            "consumption": 25.5,
                            "billing_period_start": "2025-01-01T00:00:00",
                            "billing_period_end": "2025-01-31T23:59:59",
                            "due_date": "2025-02-15T23:59:59",
                            "status": "pending",
                            "paid_at": None,
                            "created_at": "2025-01-15T10:00:00"
                        }
                    ]
                }
            }
        }
    },
    tags=["Faturas"]
)
async def get_bills(
    request: Request,
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Lista faturas com filtros opcionais.
    
    Cidadãos veem apenas suas próprias faturas.
    Gestores financeiros veem todas as faturas.
    """
    authorization = request.headers.get("Authorization")
    user = await verify_user_token(authorization)
    
    query = db.query(Bill)
    
    if status:
        query = query.filter(Bill.status == status)
    
    # Citizens can only see their own bills
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if customer:
            query = query.filter(Bill.customer_id == customer.id)
        else:
            return []
    elif customer_id:
        query = query.filter(Bill.customer_id == customer_id)
    
    bills = query.order_by(Bill.due_date.desc()).offset(skip).limit(limit).all()
    return bills

@router.get(
    "/bills/{bill_id}",
    response_model=BillResponse,
    summary="Buscar fatura por ID",
    description="""
    Busca uma fatura específica pelo seu ID.
    
    **Permissões:**
    - `financial_manager`: pode ver qualquer fatura
    - `citizen`: pode ver apenas suas próprias faturas
    """,
    responses={
        200: {
            "description": "Fatura encontrada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "customer_id": 5,
                        "meter_id": "WM-001",
                        "amount": 125.75,
                        "consumption": 25.5,
                        "billing_period_start": "2025-01-01T00:00:00",
                        "billing_period_end": "2025-01-31T23:59:59",
                        "due_date": "2025-02-15T23:59:59",
                        "status": "pending",
                        "paid_at": None,
                        "created_at": "2025-01-15T10:00:00"
                    }
                }
            }
        }
    },
    tags=["Faturas"]
)
async def get_bill(
    bill_id: int = Path(..., gt=0),
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """
    Busca uma fatura específica pelo ID.
    
    Cidadãos podem ver apenas suas próprias faturas.
    """
    user = await verify_user_token(authorization)
    
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    # Citizens can only see their own bills
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if not customer or bill.customer_id != customer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return bill

@router.post("/bills/generate")
async def generate_bills(
    month: int,
    year: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """Generate bills for all customers (financial manager only)"""
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != "financial_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    generated_count = 0
    customers = db.query(Customer).filter(Customer.is_active == True).all()
    
    for customer in customers:
        try:
            bill = await billing_calculator.generate_monthly_bill(customer.id, month, year, db)
            if bill:
                generated_count += 1
        except Exception as e:
            print(f"Error generating bill for customer {customer.id}: {e}")
    
    return {"message": f"Generated {generated_count} bills for {month}/{year}"}

# Bill Contest Management
@router.post(
    "/contests",
    response_model=BillContestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Contestar fatura",
    description="""
    Cria uma contestação para uma fatura.
    
    **Quem pode contestar:**
    - Cidadãos (citizens) podem contestar apenas suas próprias faturas
    - Um número de protocolo é gerado automaticamente
    
    **Validações:**
    - A fatura deve existir e pertencer ao usuário
    - Não pode haver contestação duplicada para a mesma fatura
    - O motivo da contestação deve ter no mínimo 10 caracteres
    
    **Resultado:**
    - A fatura terá seu status alterado para "contested"
    - Um protocolo único é gerado para acompanhamento
    """,
    responses={
        201: {
            "description": "Contestação criada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "bill_id": 123,
                        "protocol_number": "PROT123456",
                        "reason": "Fatura cobrada mesmo com imóvel desocupado durante todo o período",
                        "description": "O imóvel estava desocupado de 01/01/2025 a 31/01/2025.",
                        "status": "pending",
                        "resolution": None,
                        "resolved_at": None,
                        "resolved_by": None,
                        "created_at": "2025-01-15T14:30:00"
                    }
                }
            }
        }
    },
    tags=["Contestações"]
)
async def create_bill_contest(
    req: Request,
    contest_data: BillContestCreate,
    db: Session = Depends(get_db)
):
    """
    Contesta uma fatura.
    
    Cidadãos podem contestar apenas suas próprias faturas.
    Um protocolo é gerado automaticamente para acompanhamento.
    """
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    
    # Verify bill exists and belongs to user
    bill = db.query(Bill).filter(Bill.id == contest_data.bill_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if not customer or bill.customer_id != customer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Check if contest already exists
    existing = db.query(BillContest).filter(BillContest.bill_id == contest_data.bill_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contest already exists for this bill")
    
    protocol_number = generate_protocol_number()
    
    contest = BillContest(
        **contest_data.dict(),
        protocol_number=protocol_number,
        status="pending"
    )
    db.add(contest)
    
    # Update bill status
    bill.status = BillStatus.CONTESTED
    
    db.commit()
    db.refresh(contest)
    
    return contest

@router.get(
    "/contests",
    response_model=List[BillContestResponse],
    summary="Listar contestações",
    description="""
    Lista contestações de faturas com filtros opcionais.
    
    **Permissões:**
    - `financial_manager`: pode ver todas as contestações
    - `citizen`: pode ver apenas suas próprias contestações
    
    **Filtros:**
    - `status`: filtrar por status (pending, approved, rejected)
    - `skip` e `limit`: paginação
    """,
    responses={
        200: {
            "description": "Lista de contestações retornada com sucesso",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "bill_id": 123,
                            "protocol_number": "PROT123456",
                            "reason": "Fatura cobrada mesmo com imóvel desocupado",
                            "description": "O imóvel estava desocupado no período.",
                            "status": "pending",
                            "resolution": None,
                            "resolved_at": None,
                            "resolved_by": None,
                            "created_at": "2025-01-15T14:30:00"
                        }
                    ]
                }
            }
        }
    },
    tags=["Contestações"]
)
async def get_bill_contests(
    request: Request,
    status: Optional[str] = Query(None, description="Status da contestação: pending, approved, rejected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Lista contestações de faturas.
    
    Cidadãos veem apenas suas próprias contestações.
    """
    authorization = request.headers.get("Authorization")
    user = await verify_user_token(authorization)
    
    query = db.query(BillContest)
    
    if status:
        query = query.filter(BillContest.status == status)
    
    # Citizens can only see their own contests
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if customer:
            bill_ids = [b.id for b in db.query(Bill).filter(Bill.customer_id == customer.id).all()]
            if bill_ids:
                query = query.filter(BillContest.bill_id.in_(bill_ids))
        else:
            return []
    
    contests = query.order_by(BillContest.created_at.desc()).offset(skip).limit(limit).all()
    return contests

@router.put("/contests/{contest_id}/resolve")
async def resolve_bill_contest(
    contest_id: int,
    resolution: str,
    approved: bool,
    req: Request,
    new_amount: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Resolve bill contest (financial manager only)"""
    print(f"🔍 Resolving contest - ID: {contest_id}, Type: {type(contest_id)}, Resolution: {resolution}, Approved: {approved}")
    
    try:
        authorization = req.headers.get("Authorization")
        user = await verify_user_token(authorization)
        print(f"🔍 User verified: {user}")
        if user["role"] != "financial_manager":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        contest = db.query(BillContest).filter(BillContest.id == contest_id).first()
        print(f"🔍 Contest found: {contest}")
        if not contest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
        
        bill = db.query(Bill).filter(Bill.id == contest.bill_id).first()
        print(f"🔍 Bill found: {bill}")
        
        contest.status = "approved" if approved else "rejected"
        contest.resolution = resolution
        contest.resolved_at = datetime.utcnow()
        contest.resolved_by = user["id"]
        
        if approved and new_amount is not None:
            bill.amount = Decimal(str(new_amount))
            bill.status = BillStatus.PENDING
        else:
            bill.status = BillStatus.PENDING
        
        db.commit()
        print(f"🔍 Contest resolved successfully")
        
        return {"message": "Contest resolved successfully"}
    except Exception as e:
        print(f"❌ Error resolving contest: {e}")
        raise

# Debt Negotiation
@router.post(
    "/negotiations",
    response_model=DebtNegotiationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar negociação de débito",
    description="""
    Cria uma proposta de negociação de débito para um cliente.
    
    **Requisitos:**
    - Apenas usuários com role `financial_manager` podem criar negociações
    - O cliente não pode ter uma negociação ativa já em andamento
    
    **Como funciona:**
    - O sistema calcula automaticamente o débito total (todas as faturas vencidas)
    - O desconto pode ser aplicado conforme o número de parcelas
    - Taxa de juros pode ser aplicada para parcelamentos longos (acima de 12 parcelas)
    
    **Regras de desconto:**
    - 1 parcela: 15% de desconto
    - 2 parcelas: 10% de desconto
    - 3 parcelas: 8% de desconto
    - 6 parcelas: 5% de desconto
    - 12 parcelas: 2% de desconto
    - Acima de 12 parcelas: sem desconto, com juros de 1% ao mês
    
    **Status da negociação:**
    - Inicialmente criada com status "proposed"
    - Precisa ser aprovada pelo gestor financeiro para entrar em vigor
    """,
    responses={
        201: {
            "description": "Negociação criada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "customer_id": 5,
                        "total_debt": 1250.00,
                        "installments": 6,
                        "installment_amount": 150.50,
                        "discount_percentage": 5.0,
                        "interest_rate": 0.0,
                        "status": "proposed",
                        "start_date": None,
                        "created_at": "2025-01-15T10:30:00",
                        "updated_at": "2025-01-15T10:30:00"
                    }
                }
            }
        }
    },
    tags=["Negociações"]
)
async def create_debt_negotiation(
    negotiation_data: DebtNegotiationCreate,
    db: Session = Depends(get_db),
    authorization: str = Depends(lambda request: request.headers.get("Authorization"))
):
    """
    Cria uma proposta de negociação de débito.
    
    Apenas financial_manager pode criar negociações.
    O sistema calcula automaticamente o débito total baseado nas faturas vencidas.
    """
    print(f"🔍 Creating negotiation - Data: {negotiation_data}")
    
    try:
        user = await verify_user_token(authorization)
        print(f"🔍 User verified: {user}")
        if user["role"] != "financial_manager":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Check if customer has active negotiation
        existing = db.query(DebtNegotiation).filter(
            DebtNegotiation.customer_id == negotiation_data.customer_id,
            DebtNegotiation.status == "active"
        ).first()
        print(f"🔍 Existing negotiation: {existing}")
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer already has active negotiation")
        
        # Calculate negotiation terms
        overdue_bills = db.query(Bill).filter(
            Bill.customer_id == negotiation_data.customer_id,
            Bill.status == BillStatus.OVERDUE
        ).all()
        print(f"🔍 Found overdue bills: {len(overdue_bills)}")
        
        total_debt = sum(bill.amount for bill in overdue_bills)
        print(f"🔍 Total debt calculated: {total_debt}")
        
        negotiation = DebtNegotiation(
            customer_id=negotiation_data.customer_id,
            installments=negotiation_data.installments,
            installment_amount=Decimal(str(negotiation_data.installment_amount)),
            discount_percentage=negotiation_data.discount_percentage,
            interest_rate=negotiation_data.interest_rate,
            total_debt=total_debt,
            status="proposed"
        )
        print(f"🔍 Created negotiation object: {negotiation}")
        db.add(negotiation)
        db.commit()
        db.refresh(negotiation)
        
        print(f"🔍 Negotiation saved successfully")
        return negotiation
    except Exception as e:
        print(f"❌ Error creating negotiation: {e}")
        print(f"❌ Error type: {type(e)}")
        raise

@router.get(
    "/negotiations",
    response_model=List[DebtNegotiationResponse],
    summary="Listar negociações de débito",
    description="""
    Lista negociações de débito com filtros opcionais.
    
    **Permissões:**
    - `financial_manager`: pode ver todas as negociações
    - `citizen`: pode ver apenas suas próprias negociações
    
    **Filtros:**
    - `customer_id`: filtrar por cliente específico
    - `status`: filtrar por status (proposed, active, cancelled, completed)
    
    **Status possíveis:**
    - `proposed`: Negociação proposta, aguardando aprovação
    - `active`: Negociação aprovada e em andamento
    - `cancelled`: Negociação cancelada
    - `completed`: Negociação concluída
    """,
    responses={
        200: {
            "description": "Lista de negociações retornada com sucesso",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "customer_id": 5,
                            "total_debt": 1250.00,
                            "installments": 6,
                            "installment_amount": 150.50,
                            "discount_percentage": 5.0,
                            "interest_rate": 0.0,
                            "status": "proposed",
                            "start_date": None,
                            "created_at": "2025-01-15T10:30:00",
                            "updated_at": "2025-01-15T10:30:00"
                        }
                    ]
                }
            }
        }
    },
    tags=["Negociações"]
)
async def get_debt_negotiations(
    request: Request,
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Lista negociações de débito.
    
    Cidadãos veem apenas suas próprias negociações.
    """
    authorization = request.headers.get("Authorization")
    user = await verify_user_token(authorization)
    
    query = db.query(DebtNegotiation)
    
    if status:
        query = query.filter(DebtNegotiation.status == status)
    
    # Citizens can only see their own negotiations
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if customer:
            query = query.filter(DebtNegotiation.customer_id == customer.id)
        else:
            return []
    elif customer_id:
        query = query.filter(DebtNegotiation.customer_id == customer_id)
    
    negotiations = query.order_by(DebtNegotiation.created_at.desc()).all()
    return negotiations

@router.put("/debt-negotiations/{negotiation_id}/resolve")
async def resolve_debt_negotiation(
    negotiation_id: str,
    approved: bool,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resolve debt negotiation (financial manager only)"""
    authorization = request.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != "financial_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Try to find by string ID first, then by integer ID
    negotiation = db.query(DebtNegotiation).filter(DebtNegotiation.id == negotiation_id).first()
    if not negotiation:
        # Try to convert to int if it's a numeric string
        try:
            int_id = int(negotiation_id)
            negotiation = db.query(DebtNegotiation).filter(DebtNegotiation.id == int_id).first()
        except ValueError:
            pass
    
    if not negotiation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negotiation not found")
    
    if negotiation.status != "proposed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negotiation is not in proposed status")
    
    negotiation.status = "active" if approved else "cancelled"
    if approved:
        negotiation.start_date = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Negotiation resolved successfully"}

# Payment Processing
@router.post("/bills/{bill_id}/pay", response_model=PaymentResponse)
async def pay_bill(
    bill_id: int,
    req: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Pay a bill (simplified endpoint for frontend).
    """
    from business.payment_gateway import payment_gateway
    
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    
    # Verify bill exists
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    # Check if bill is already paid
    if bill.status == BillStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bill already paid")
    
    # Citizens can only pay their own bills
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if not customer or bill.customer_id != customer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Process payment through gateway mock
    # Defaulting to credit_card as frontend doesn't provide choice
    payment_result = await payment_gateway.process_payment(
        bill_id=bill.id,
        amount=float(bill.amount),
        customer_id=bill.customer_id,
        payment_method="credit_card"
    )
    
    # Check if payment was successful
    if not payment_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": payment_result["message"],
                "error_code": payment_result["error_code"],
                "transaction_id": payment_result["transaction_id"]
            }
        )
    
    # Payment successful - create payment record
    payment = Payment(
        bill_id=bill.id,
        customer_id=bill.customer_id,
        amount=bill.amount,
        payment_method=payment_result["payment_method"],
        payment_date=datetime.utcnow(),
        confirmation_number=payment_result["confirmation_number"],
        transaction_id=payment_result["transaction_id"]
    )
    db.add(payment)
    
    # Update bill status
    bill.status = BillStatus.PAID
    bill.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(payment)
    
    # Send payment confirmation
    background_tasks.add_task(send_payment_confirmation, payment, bill)
    
    return payment

@router.post("/payments", response_model=PaymentResponse)
async def process_payment(
    
    payment_data: PaymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process payment through mock gateway"""
    from business.payment_gateway import payment_gateway
    
    authorization = request.headers.get("Authorization")
    user = await verify_user_token(authorization)
    
    # Verify bill exists
    bill = db.query(Bill).filter(Bill.id == payment_data.bill_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    # Check if bill is already paid
    if bill.status == BillStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bill already paid")
    
    # Citizens can only pay their own bills
    if user["role"] == "citizen":
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if not customer or bill.customer_id != customer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Process payment through gateway mock
    payment_result = await payment_gateway.process_payment(
        bill_id=bill.id,
        amount=float(bill.amount),
        customer_id=bill.customer_id,
        payment_method=payment_data.payment_method if hasattr(payment_data, 'payment_method') else "credit_card"
    )
    
    # Check if payment was successful
    if not payment_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": payment_result["message"],
                "error_code": payment_result["error_code"],
                "transaction_id": payment_result["transaction_id"]
            }
        )
    
    # Payment successful - create payment record
    payment = Payment(
        bill_id=bill.id,
        customer_id=bill.customer_id,
        amount=bill.amount,
        payment_method=payment_result["payment_method"],
        payment_date=datetime.utcnow(),
        confirmation_number=payment_result["confirmation_number"],
        transaction_id=payment_result["transaction_id"]
    )
    db.add(payment)
    
    # Update bill status
    bill.status = BillStatus.PAID
    bill.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(payment)
    
    # Send payment confirmation
    background_tasks.add_task(send_payment_confirmation, payment, bill)
    
    return {
        "success": True,
        "message": payment_result["message"],
        "payment": payment,
        "confirmation_number": payment_result["confirmation_number"],
        "transaction_id": payment_result["transaction_id"]
    }

# Tariff Management
@router.post("/tariffs", response_model=TariffRateResponse)
async def create_tariff_rate(
    tariff_data: TariffRateCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """Create tariff rate (financial manager only)"""
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != "financial_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    tariff = TariffRate(**tariff_data.dict())
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    
    return tariff

@router.get("/tariffs")
async def get_tariff_rates(
    active_only: bool = True,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """Get tariff rates"""
    await verify_user_token(authorization)
    
    query = db.query(TariffRate)
    if active_only:
        query = query.filter(TariffRate.is_active == True)
    
    tariffs = query.order_by(TariffRate.effective_date.desc()).all()
    return {"tariffs": tariffs}

# Background tasks
async def check_billing_cycle(customer_id: int, db: Session):
    """Check if it's time to generate a bill for customer"""
    try:
        # This would typically check if a month has passed since last bill
        # For now, we'll skip automatic generation
        pass
    except Exception as e:
        print(f"Error checking billing cycle: {e}")

async def send_payment_confirmation(payment: Payment, bill: Bill):
    """Send payment confirmation notification"""
    try:
        notification_data = {
            "recipient_id": bill.customer_id,
            "title": "Payment Confirmed",
            "message": f"Payment of ${payment.amount} for bill #{bill.id} has been processed successfully.",
            "type": "payment_confirmation",
            "channel": "email"
        }
        
        await make_service_request(
            service_registry.get_service_url("notification"),
            "/notifications",
            method="POST",
            data=notification_data
        )
    except Exception as e:
        print(f"Error sending payment confirmation: {e}")

# Test endpoints
@router.post("/test-debt-nego", response_model=DebtNegotiationResponse)
async def test_debt_negotiation(
    negotiation_data: DebtNegotiationCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """Test endpoint for debt negotiation"""
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != "financial_manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Simple creation without business logic
    negotiation = DebtNegotiation(
        customer_id=negotiation_data.customer_id,
        installments=negotiation_data.installments,
        installment_amount=negotiation_data.installment_amount,
        discount_percentage=negotiation_data.discount_percentage,
        interest_rate=negotiation_data.interest_rate,
        total_debt=100.00,  # Fixed value for test
        status="proposed"
    )
    db.add(negotiation)
    db.commit()
    db.refresh(negotiation)
    return negotiation

# ==================== REPORTS ====================

class BillingReportFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    customer_id: Optional[int] = None

@router.post("/reports/billing")
async def generate_billing_report(
    filters: BillingReportFilters,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Generate billing report"""
    user = verify_user_token(f"Bearer {credentials.credentials}")
    
    # Check permissions
    user_role = user.get("role", "")
    if user_role not in ["financial_manager", "operator"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente")
    
    # Validate period
    if filters.start_date and filters.end_date:
        period_days = (filters.end_date - filters.start_date).days
        if period_days < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A data de início deve ser anterior à data de fim"
            )
    
    # Query bills
    query = db.query(Bill)
    
    if filters.start_date:
        query = query.filter(Bill.billing_period_start >= filters.start_date)
    if filters.end_date:
        query = query.filter(Bill.billing_period_end <= filters.end_date)
    if filters.status:
        query = query.filter(Bill.status == filters.status)
    if filters.customer_id:
        query = query.filter(Bill.customer_id == filters.customer_id)
    
    bills = query.order_by(Bill.billing_period_start.desc()).all()
    
    # Calculate statistics
    total_bills = len(bills)
    total_amount = sum(float(bill.amount) for bill in bills)
    total_consumption = sum(float(bill.consumption or 0) for bill in bills)
    
    # Status breakdown
    status_breakdown = {}
    for bill in bills:
        status_key = bill.status or "unknown"
        if status_key not in status_breakdown:
            status_breakdown[status_key] = {"count": 0, "amount": 0}
        status_breakdown[status_key]["count"] += 1
        status_breakdown[status_key]["amount"] += float(bill.amount)
    
    # Calculate averages
    avg_amount = total_amount / total_bills if total_bills > 0 else 0
    avg_consumption = total_consumption / total_bills if total_bills > 0 else 0
    
    # Paid vs unpaid
    paid_bills = [b for b in bills if b.status == "paid"]
    unpaid_bills = [b for b in bills if b.status != "paid"]
    paid_amount = sum(float(bill.amount) for bill in paid_bills)
    unpaid_amount = total_amount - paid_amount
    
    # Payment rate
    payment_rate = (len(paid_bills) / total_bills * 100) if total_bills > 0 else 0
    
    # Overdue bills
    today = datetime.now().date()
    overdue_bills = [b for b in unpaid_bills if b.due_date and b.due_date < today]
    overdue_amount = sum(float(bill.amount) for bill in overdue_bills)
    
    # Average consumption per customer
    customer_consumption = {}
    for bill in bills:
        if bill.customer_id:
            if bill.customer_id not in customer_consumption:
                customer_consumption[bill.customer_id] = {"bills": 0, "total_consumption": 0, "total_amount": 0}
            customer_consumption[bill.customer_id]["bills"] += 1
            customer_consumption[bill.customer_id]["total_consumption"] += float(bill.consumption or 0)
            customer_consumption[bill.customer_id]["total_amount"] += float(bill.amount)
    
    # Calculate averages per customer
    for customer_id, stats in customer_consumption.items():
        if stats["bills"] > 0:
            stats["avg_consumption"] = round(stats["total_consumption"] / stats["bills"], 2)
            stats["avg_amount"] = round(stats["total_amount"] / stats["bills"], 2)
    
    # Bills by month (for trend analysis)
    bills_by_month = {}
    for bill in bills:
        if bill.billing_period_start:
            month_key = bill.billing_period_start.strftime("%Y-%m")
            if month_key not in bills_by_month:
                bills_by_month[month_key] = {"count": 0, "total_amount": 0, "total_consumption": 0}
            bills_by_month[month_key]["count"] += 1
            bills_by_month[month_key]["total_amount"] += float(bill.amount)
            bills_by_month[month_key]["total_consumption"] += float(bill.consumption or 0)
    
    report_id = generate_protocol_number()
    
    return {
        "report_id": report_id,
        "filters": filters.dict(),
        "summary": {
            "total_bills": total_bills,
            "total_amount": round(total_amount, 2),
            "total_consumption": round(total_consumption, 2),
            "average_amount": round(avg_amount, 2),
            "average_consumption": round(avg_consumption, 2),
            "paid_bills": len(paid_bills),
            "paid_amount": round(paid_amount, 2),
            "unpaid_bills": len(unpaid_bills),
            "unpaid_amount": round(unpaid_amount, 2),
            "payment_rate": round(payment_rate, 2),
            "overdue_bills": len(overdue_bills),
            "overdue_amount": round(overdue_amount, 2),
            "status_breakdown": status_breakdown,
            "customer_statistics": customer_consumption,
            "bills_by_month": bills_by_month,
            "period": {
                "start": filters.start_date.isoformat() if filters.start_date else None,
                "end": filters.end_date.isoformat() if filters.end_date else None
            }
        },
        "bills": [
            {
                "id": bill.id,
                "customer_id": bill.customer_id,
                "meter_id": bill.meter_id,
                "amount": float(bill.amount) if bill.amount else 0.0,
                "consumption": float(bill.consumption or 0),
                "billing_period_start": bill.billing_period_start.isoformat() if bill.billing_period_start else None,
                "billing_period_end": bill.billing_period_end.isoformat() if bill.billing_period_end else None,
                "due_date": bill.due_date.isoformat() if bill.due_date else None,
                "status": bill.status or "unknown",
                "paid_at": bill.paid_at.isoformat() if bill.paid_at else None,
                "created_at": bill.created_at.isoformat() if bill.created_at else None
            }
            for bill in bills[:1000]  # Limit to 1000 for performance
        ],
        "generated_at": datetime.now().isoformat(),
        "generated_by": user.get("email", "Unknown")
    }

@router.post("/test-simple")
async def test_simple(
    data: dict,
    req: Request,
    db: Session = Depends(get_db)
):
    """Simple test endpoint"""
    authorization = req.headers.get("Authorization")
    return {"status": "success", "received": data}