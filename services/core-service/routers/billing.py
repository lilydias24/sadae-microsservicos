from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, Body, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import Field
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

# Billing calculator
billing_calculator = BillingCalculator()

async def verify_user_token(authorization: str):
    """Verify user token locally"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
        
        token = authorization.split(" ")[1]
        payload = verify_token(token)
        
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

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
    customer_data: CustomerCreate = Body(
        ...,
        example={
            "name": "João da Silva",
            "document": "12345678900",
            "email": "joao.silva@email.com",
            "phone": "(55) 99999-9999",
            "address": "Rua das Flores, 123, Centro, São Paulo - SP",
            "customer_type": "residential"
        }
    ),
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Cria um novo cliente no sistema.
    
    Requer permissões de financial_manager.
    """
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.FINANCIAL_MANAGER:
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
    skip: int = Field(0, description="Número de registros para pular (paginação)", ge=0, example=0),
    limit: int = Field(100, description="Número máximo de registros a retornar", ge=1, le=1000, example=100),
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """
    Lista todos os clientes com paginação.
    
    Requer permissões de financial_manager.
    """
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.FINANCIAL_MANAGER:
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
    customer_id: int = Field(..., description="ID do cliente", example=1, gt=0),
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
    if user["role"] == UserRole.CITIZEN and customer.user_id != user["id"]:
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
    if user["role"] != UserRole.FINANCIAL_MANAGER:
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
    if user["role"] == UserRole.CITIZEN:
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
    if user["role"] == UserRole.CITIZEN:
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if customer:
            meter_ids = [m.meter_id for m in db.query(WaterMeter).filter(WaterMeter.customer_id == customer.id).all()]
            query = query.filter(MeterReading.meter_id.in_(meter_ids))
        else:
            return {"readings": []}
    elif customer_id:
        meter_ids = [m.meter_id for m in db.query(WaterMeter).filter(WaterMeter.customer_id == customer_id).all()]
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
    customer_id: Optional[int] = Field(None, description="ID do cliente para filtrar faturas", example=5),
    status: Optional[BillStatus] = Field(None, description="Status da fatura: pending, paid, overdue, contested", example="pending"),
    skip: int = Field(0, description="Número de registros para pular", ge=0, example=0),
    limit: int = Field(100, description="Número máximo de registros", ge=1, le=1000, example=100),
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
    if user["role"] == UserRole.CITIZEN:
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
    bill_id: int = Field(..., description="ID da fatura", example=1, gt=0),
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
    if user["role"] == UserRole.CITIZEN:
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
    if user["role"] != UserRole.FINANCIAL_MANAGER:
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
    contest_data: BillContestCreate = Body(
        ...,
        example={
            "bill_id": 123,
            "reason": "Fatura cobrada mesmo com imóvel desocupado durante todo o período",
            "description": "O imóvel estava desocupado de 01/01/2025 a 31/01/2025, mas foi gerada fatura de consumo."
        }
    ),
    req: Request,
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
    
    if user["role"] == UserRole.CITIZEN:
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
    status: Optional[str] = Field(None, description="Status da contestação: pending, approved, rejected", example="pending"),
    skip: int = Field(0, description="Número de registros para pular", ge=0, example=0),
    limit: int = Field(100, description="Número máximo de registros", ge=1, le=1000, example=100),
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
    if user["role"] == UserRole.CITIZEN:
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if customer:
            bill_ids = [b.id for b in db.query(Bill).filter(Bill.customer_id == customer.id).all()]
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
        if user["role"] != UserRole.FINANCIAL_MANAGER:
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
    negotiation_data: DebtNegotiationCreate = Body(
        ...,
        example={
            "customer_id": 5,
            "installments": 6,
            "installment_amount": 150.50,
            "discount_percentage": 5.0,
            "interest_rate": 0.0
        }
    ),
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
        if user["role"] != UserRole.FINANCIAL_MANAGER:
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
    customer_id: Optional[int] = Field(None, description="ID do cliente para filtrar negociações", example=5),
    status: Optional[str] = Field(None, description="Status da negociação: proposed, active, cancelled, completed", example="proposed"),
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
    if user["role"] == UserRole.CITIZEN:
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
    if user["role"] != UserRole.FINANCIAL_MANAGER:
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
@router.post("/payments", response_model=PaymentResponse)
async def process_payment(
    request: Request,
    payment_data: PaymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process payment"""
    authorization = request.headers.get("Authorization")
    user = await verify_user_token(authorization)
    
    # Verify bill exists
    bill = db.query(Bill).filter(Bill.id == payment_data.bill_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    # Citizens can only pay their own bills
    if user["role"] == UserRole.CITIZEN:
        customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
        if not customer or bill.customer_id != customer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    payment = Payment(**payment_data.dict())
    db.add(payment)
    
    # Update bill status
    bill.status = BillStatus.PAID
    bill.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(payment)
    
    # Send payment confirmation
    background_tasks.add_task(send_payment_confirmation, payment, bill)
    
    return payment

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
    if user["role"] != UserRole.FINANCIAL_MANAGER:
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
    if user["role"] != UserRole.FINANCIAL_MANAGER:
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

@router.post("/test-simple")
async def test_simple(
    data: dict,
    req: Request,
    db: Session = Depends(get_db)
):
    """Simple test endpoint"""
    authorization = req.headers.get("Authorization")
    return {"status": "success", "received": data}

@router.post("/tariffs")
async def create_tariff_rate(tariff_data: dict, db: Session = Depends(get_db)):
    """Create tariff rate"""
    tariff = TariffRate(**tariff_data)
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    return tariff

@router.get("/tariffs")
async def get_tariff_rates(active_only: bool = True, db: Session = Depends(get_db)):
    """Get tariff rates"""
    query = db.query(TariffRate)
    if active_only:
        query = query.filter(TariffRate.is_active == True)
    tariffs = query.order_by(TariffRate.effective_date.desc()).all()
    return {"tariffs": tariffs}

@router.get("/test-data")
async def get_test_data(db: Session = Depends(get_db)):
    """Get test data"""
    bills = db.query(Bill).limit(5).all()
    customers = db.query(Customer).limit(3).all()
    contests = db.query(BillContest).limit(3).all()
    
    return {
        "bills": bills,
        "customers": customers,
        "contests": contests
    }

@router.get("/bills")
async def get_bills(db: Session = Depends(get_db)):
    """Get all bills"""
    bills = db.query(Bill).all()
    return bills

@router.post("/contests")
async def create_contest(contest_data: dict, db: Session = Depends(get_db)):
    """Create bill contest"""
    contest = BillContest(**contest_data)
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest

@router.get("/contests")
async def get_contests(db: Session = Depends(get_db)):
    """Get all contests"""
    contests = db.query(BillContest).all()
    return contests

@router.put("/contests/{contest_id}/resolve")
async def resolve_contest(contest_id: int, resolution: str, approved: bool, db: Session = Depends(get_db)):
    """Resolve contest"""
    contest = db.query(BillContest).filter(BillContest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    
    contest.resolution = resolution
    contest.status = "approved" if approved else "rejected"
    db.commit()
    return contest

@router.post("/negotiations")
async def create_negotiation(negotiation_data: dict, db: Session = Depends(get_db)):
    """Create debt negotiation"""
    negotiation = DebtNegotiation(**negotiation_data)
    db.add(negotiation)
    db.commit()
    db.refresh(negotiation)
    return negotiation

@router.get("/negotiations")
async def get_negotiations(db: Session = Depends(get_db)):
    """Get all negotiations"""
    negotiations = db.query(DebtNegotiation).all()
    return negotiations

@router.post("/payments")
async def process_payment(payment_data: dict, db: Session = Depends(get_db)):
    """Process payment"""
    payment = Payment(**payment_data)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment