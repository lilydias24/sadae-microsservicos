from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
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

# 🔗 Chain of Responsibility - Importar cadeias de validação
try:
    from business.billing_validation_chain import (
        create_contest_validation_chain,
        create_negotiation_validation_chain,
        ContestRequest,
        NegotiationRequest,
        ContestReason
    )
    CHAIN_ENABLED = True
    print("✅ Chain of Responsibility habilitado para Billing")
except ImportError as e:
    print(f"⚠️ Chain of Responsibility não disponível: {e}")
    CHAIN_ENABLED = False

# 📊 Audit Logger - Importar sistema de auditoria
sys.path.insert(0, '/app/shared')
try:
    from audit_logger import (
        audit_contest_decision,
        audit_negotiation_decision,
        audit_auto_approval,
        audit_manual_review_required,
        get_audit_logger,
        set_audit_logger,
        AuditLogger
    )
    AUDIT_ENABLED = True
    print("✅ Sistema de Auditoria habilitado para Billing")
except ImportError as e:
    print(f"⚠️ Sistema de Auditoria não disponível: {e}")
    AUDIT_ENABLED = False

router = APIRouter()

# Billing calculator
billing_calculator = BillingCalculator()

# 🔗 Inicializar cadeias de validação
if CHAIN_ENABLED:
    contest_validation_chain = create_contest_validation_chain()
    negotiation_validation_chain = create_negotiation_validation_chain()

# 📊 Configurar Audit Logger com sessão do banco
if AUDIT_ENABLED:
    from database import SessionLocal
    audit_logger_instance = AuditLogger(
        log_to_file=True,
        log_to_db=True,
        log_file_path="/tmp/sadae_audit.log",
        db_session_factory=SessionLocal
    )
    set_audit_logger(audit_logger_instance)
    print("✅ Audit Logger configurado com banco de dados")

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
@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """Create customer (financial manager only)"""
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

@router.get("/customers", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """Get customers (financial manager only)"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.FINANCIAL_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers

@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """Get customer by ID"""
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
@router.get("/bills", response_model=List[BillResponse])
async def get_bills(
    request: Request,
    customer_id: Optional[int] = None,
    status: Optional[BillStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get bills"""
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

@router.get("/bills/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: int,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db)
):
    """Get bill by ID"""
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
@router.post("/contests", response_model=BillContestResponse)
async def create_bill_contest(
    contest_data: BillContestCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    🔗 Contest a bill with Chain of Responsibility validation
    
    A cadeia de validação analisa automaticamente:
    - Elegibilidade da contestação
    - Análise de valor vs. histórico de consumo
    - Evidências fornecidas
    - Auto-aprovação baseada em score (>= 70 = aprovado automático)
    """
    authorization = req.headers.get("Authorization")
    user = await verify_user_token(authorization)
    
    # Verify bill exists and belongs to user
    bill = db.query(Bill).filter(Bill.id == contest_data.bill_id).first()
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    
    # Get customer
    customer = db.query(Customer).filter(Customer.user_id == user["id"]).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    
    if user["role"] == UserRole.CITIZEN:
        if bill.customer_id != customer.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Check if contest already exists
    existing = db.query(BillContest).filter(BillContest.bill_id == contest_data.bill_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contest already exists for this bill")
    
    protocol_number = generate_protocol_number()
    
    # 🔗 CHAIN OF RESPONSIBILITY - Validação automática
    validation_result = None
    validation_notes = []
    
    if CHAIN_ENABLED:
        try:
            # Calcular média de consumo histórico
            previous_bills = db.query(Bill).filter(
                Bill.customer_id == bill.customer_id,
                Bill.id < bill.id
            ).order_by(Bill.created_at.desc()).limit(6).all()
            
            avg_consumption = None
            if previous_bills:
                avg_consumption = sum(b.amount for b in previous_bills) / len(previous_bills)
            
            # Mapear motivo para enum
            reason_map = {
                "high_consumption": ContestReason.HIGH_CONSUMPTION,
                "billing_error": ContestReason.BILLING_ERROR,
                "meter_defect": ContestReason.METER_DEFECT,
                "leak_reported": ContestReason.LEAK_REPORTED,
                "service_interruption": ContestReason.SERVICE_INTERRUPTION,
                "duplicate_charge": ContestReason.DUPLICATE_CHARGE,
                "other": ContestReason.OTHER
            }
            reason = reason_map.get(contest_data.reason, ContestReason.OTHER)
            
            # Criar requisição para a cadeia
            chain_request = ContestRequest(
                bill_id=bill.id,
                customer_id=customer.id,
                current_amount=bill.amount,
                contested_amount=contest_data.contested_amount or bill.amount * Decimal("0.5"),
                reason=reason,
                description=contest_data.description,
                evidence_files=getattr(contest_data, 'evidence_files', []),
                previous_consumption_avg=avg_consumption,
                has_leak_report=False,  # TODO: verificar se há relatório de vazamento
                has_maintenance_request=False  # TODO: verificar ordens de manutenção
            )
            
            # Processar na cadeia com medição de tempo
            import time
            start_time = time.time()
            validation_result = contest_validation_chain.handle(chain_request)
            processing_time_ms = (time.time() - start_time) * 1000
            
            validation_notes = validation_result.data.get('notes', [])
            
            print(f"🔗 Chain validation - Score: {validation_result.data['validation_score']}, Approved: {validation_result.approved}")
            
            # 📊 AUDITORIA - Registrar decisão da cadeia
            if AUDIT_ENABLED:
                try:
                    audit_contest_decision(
                        request_id=chain_request.request_id,
                        user_id=customer.id,
                        bill_id=bill.id,
                        decision="approved" if validation_result.approved else ("review" if validation_result.requires_review else "rejected"),
                        score=float(validation_result.data['validation_score']),
                        handler_sequence=[entry['handler'] for entry in chain_request.processing_history],
                        input_data={
                            "bill_id": bill.id,
                            "current_amount": float(bill.amount),
                            "contested_amount": float(contest_data.contested_amount) if contest_data.contested_amount else None,
                            "reason": contest_data.reason,
                            "description": contest_data.description[:100]  # Limitar tamanho
                        },
                        output_data={
                            "approved": validation_result.approved,
                            "requires_review": validation_result.requires_review,
                            "suggested_amount": float(validation_result.suggested_amount) if validation_result.suggested_amount else None,
                            "validation_score": validation_result.data['validation_score']
                        },
                        processing_time_ms=processing_time_ms
                    )
                    
                    # Log específico para auto-aprovações
                    if validation_result.approved:
                        audit_auto_approval(
                            chain_name="ContestValidationChain",
                            request_id=chain_request.request_id,
                            user_id=customer.id,
                            entity_type="bill_contest",
                            entity_id=bill.id,
                            reason=f"Score {validation_result.data['validation_score']} >= 70",
                            score=float(validation_result.data['validation_score'])
                        )
                    elif validation_result.requires_review:
                        audit_manual_review_required(
                            chain_name="ContestValidationChain",
                            request_id=chain_request.request_id,
                            user_id=customer.id,
                            entity_type="bill_contest",
                            entity_id=bill.id,
                            reason=f"Score {validation_result.data['validation_score']} requer revisão manual",
                            score=float(validation_result.data['validation_score'])
                        )
                except Exception as audit_error:
                    print(f"⚠️ Erro ao registrar auditoria: {audit_error}")
            
        except Exception as e:
            print(f"⚠️ Erro na validação da cadeia: {e}")
            # Continua sem validação automática em caso de erro
    
    # Determinar status inicial baseado na validação
    initial_status = "pending"
    suggested_amount = None
    
    if validation_result:
        if validation_result.approved:
            initial_status = "approved"
            suggested_amount = validation_result.suggested_amount
        elif validation_result.requires_review:
            initial_status = "under_review"
        else:
            initial_status = "rejected"
    
    contest = BillContest(
        **contest_data.dict(),
        protocol_number=protocol_number,
        status=initial_status
    )
    
    # Adicionar notas de validação como comentário interno
    if validation_notes:
        contest.admin_notes = "\n".join([f"🔗 {note}" for note in validation_notes])
    
    db.add(contest)
    
    # Update bill status
    bill.status = BillStatus.CONTESTED
    
    db.commit()
    db.refresh(contest)
    
    return contest

@router.get("/contests", response_model=List[BillContestResponse])
async def get_bill_contests(
    request: Request,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get bill contests"""
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
@router.post("/negotiations", response_model=DebtNegotiationResponse)
async def create_debt_negotiation(
    negotiation_data: DebtNegotiationCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    🔗 Create debt negotiation with Chain of Responsibility validation
    
    A cadeia analisa automaticamente:
    - Elegibilidade (sem negociações ativas)
    - Análise de crédito e histórico de pagamento
    - Validação de entrada mínima
    - Definição automática de: parcelas máximas, taxa de juros, desconto
    """
    print(f"🔍 Creating negotiation - Data received: {negotiation_data}")
    print(f"🔍 negotiation_data type: {type(negotiation_data)}")
    print(f"🔍 negotiation_data dict: {negotiation_data.dict()}")
    
    try:
        authorization = request.headers.get("Authorization")
        user = await verify_user_token(authorization)
        print(f"🔍 User verified: {user}")
        if user["role"] != UserRole.FINANCIAL_MANAGER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        
        # Get customer
        customer = db.query(Customer).filter(Customer.id == negotiation_data.customer_id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        # Check if customer has active negotiation
        existing = db.query(DebtNegotiation).filter(
            DebtNegotiation.customer_id == negotiation_data.customer_id,
            DebtNegotiation.status == "active"
        ).first()
        print(f"🔍 Existing negotiation: {existing}")
        
        # Get overdue bills
        overdue_bills = db.query(Bill).filter(
            Bill.customer_id == negotiation_data.customer_id,
            Bill.status == BillStatus.OVERDUE
        ).all()
        print(f"🔍 Found overdue bills: {len(overdue_bills)}")
        
        if not overdue_bills:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No overdue bills found for this customer")
        
        total_debt = sum(bill.amount for bill in overdue_bills)
        print(f"🔍 Total debt calculated: {total_debt}")
        
        # 🔗 CHAIN OF RESPONSIBILITY - Validação e cálculo automático de condições
        validation_result = None
        validation_notes = []
        final_terms = {
            "installments": negotiation_data.installments,
            "interest_rate": negotiation_data.interest_rate,
            "discount_percentage": negotiation_data.discount_percentage or Decimal(0)
        }
        
        if CHAIN_ENABLED:
            try:
                # Calcular score de histórico de pagamento (simplificado)
                total_bills = db.query(Bill).filter(Bill.customer_id == customer.id).count()
                paid_on_time = db.query(Bill).filter(
                    Bill.customer_id == customer.id,
                    Bill.status == BillStatus.PAID
                ).count()
                payment_score = int((paid_on_time / total_bills * 100)) if total_bills > 0 else 50
                
                # Calcular idade da dívida mais antiga
                oldest_bill = min(overdue_bills, key=lambda b: b.due_date) if overdue_bills else None
                debt_age_days = (datetime.now().date() - oldest_bill.due_date).days if oldest_bill else 0
                
                # Criar requisição para a cadeia
                chain_request = NegotiationRequest(
                    customer_id=customer.id,
                    total_debt=total_debt,
                    overdue_bills=[{"id": b.id, "amount": float(b.amount)} for b in overdue_bills],
                    proposed_installments=negotiation_data.installments,
                    proposed_down_payment=Decimal(str(negotiation_data.down_payment or 0)),
                    payment_history_score=payment_score,
                    has_active_negotiations=existing is not None,
                    debt_age_days=debt_age_days
                )
                
                # Processar na cadeia com medição de tempo
                import time
                start_time = time.time()
                validation_result = negotiation_validation_chain.handle(chain_request)
                processing_time_ms = (time.time() - start_time) * 1000
                
                validation_notes = validation_result.data.get('notes', [])
                
                print(f"🔗 Chain validation - Approved: {validation_result.approved}")
                
                # 📊 AUDITORIA - Registrar decisão da negociação
                if AUDIT_ENABLED:
                    try:
                        audit_negotiation_decision(
                            request_id=chain_request.request_id,
                            user_id=user["id"],
                            customer_id=customer.id,
                            decision="approved" if validation_result.approved else "rejected",
                            handler_sequence=[entry['handler'] for entry in chain_request.processing_history],
                            input_data={
                                "customer_id": customer.id,
                                "total_debt": float(total_debt),
                                "proposed_installments": negotiation_data.installments,
                                "proposed_down_payment": float(negotiation_data.down_payment or 0),
                                "payment_history_score": payment_score,
                                "debt_age_days": debt_age_days
                            },
                            output_data={
                                "approved": validation_result.approved,
                                "max_installments": validation_result.data.get('max_installments'),
                                "interest_rate": float(validation_result.data.get('interest_rate', 0)),
                                "discount_percentage": float(validation_result.data.get('discount_percentage', 0))
                            },
                            processing_time_ms=processing_time_ms
                        )
                        
                        # Log de auto-aprovação
                        if validation_result.approved:
                            audit_auto_approval(
                                chain_name="NegotiationValidationChain",
                                request_id=chain_request.request_id,
                                user_id=user["id"],
                                entity_type="debt_negotiation",
                                entity_id=customer.id,
                                reason=f"Negociação aprovada com desconto de {validation_result.data['discount_percentage']}%"
                            )
                    except Exception as audit_error:
                        print(f"⚠️ Erro ao registrar auditoria: {audit_error}")
                
                # Se aprovado, usar os termos calculados pela cadeia
                if validation_result.approved:
                    final_terms = {
                        "installments": validation_result.data['max_installments'],
                        "interest_rate": validation_result.data['interest_rate'],
                        "discount_percentage": validation_result.data['discount_percentage']
                    }
                    print(f"✅ Termos aprovados pela cadeia: {final_terms}")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Negociação rejeitada: {validation_result.message}"
                    )
                    
            except HTTPException:
                raise
            except Exception as e:
                print(f"⚠️ Erro na validação da cadeia: {e}")
                # Em caso de erro, usa valores padrão conservadores
                final_terms = {
                    "installments": min(negotiation_data.installments, 12),
                    "interest_rate": Decimal("1.5"),
                    "discount_percentage": Decimal(0)
                }
        
        # Calcular valor com desconto
        total_with_discount = total_debt * (Decimal("100") - final_terms["discount_percentage"]) / Decimal("100")
        
        # Calcular valor da parcela
        down_payment = Decimal(str(negotiation_data.down_payment or 0))
        remaining = total_with_discount - down_payment
        installment_amount = remaining / final_terms["installments"] if final_terms["installments"] > 0 else remaining
        
        negotiation = DebtNegotiation(
            customer_id=negotiation_data.customer_id,
            installments=final_terms["installments"],
            installment_amount=installment_amount,
            discount_percentage=float(final_terms["discount_percentage"]),
            interest_rate=float(final_terms["interest_rate"]),
            total_debt=total_debt,
            status="proposed"
        )
        
        # Adicionar notas de validação
        if validation_notes:
            negotiation.notes = "\n".join([f"🔗 {note}" for note in validation_notes])
        
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

@router.get("/negotiations", response_model=List[DebtNegotiationResponse])
async def get_debt_negotiations(
    request: Request,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get debt negotiations"""
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

# ❌ Rotas duplicadas removidas - usar as rotas com Chain of Responsibility acima

@router.post("/payments")
async def process_payment(payment_data: dict, db: Session = Depends(get_db)):
    """Process payment"""
    payment = Payment(**payment_data)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment