from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os
from decimal import Decimal

# Add shared modules to path
sys.path.append('/app/shared')

from models import BillStatus, UserRole
from database import get_database_url, create_database_engine, get_session_local
from utils import generate_protocol_number, make_service_request, service_registry
from auth import verify_token

from database_models import (
    Customer, WaterMeter, MeterReading, Bill, BillContest, 
    DebtNegotiation, Payment, TariffRate, Base
)
from schemas import (
    CustomerCreate, CustomerResponse,
    WaterMeterCreate, WaterMeterResponse,
    MeterReadingCreate, MeterReadingResponse,
    BillResponse, BillContestCreate, BillContestResponse,
    DebtNegotiationCreate, DebtNegotiationResponse,
    PaymentCreate, PaymentResponse,
    TariffRateCreate, TariffRateResponse
)
from billing_calculator import BillingCalculator

app = FastAPI(
    title="SADAE Billing Service",
    description="Billing and payment management service for SADAE",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = get_database_url("billing")
engine = create_database_engine(DATABASE_URL)
SessionLocal = get_session_local(engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Billing calculator
billing_calculator = BillingCalculator()

def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@app.get("/")
async def root():
    return {"message": "SADAE Billing Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "billing"}

# Test endpoint (temporary - no auth required)
@app.get("/test-data")
async def get_test_data(db: Session = Depends(get_db_session)):
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
@app.post("/customers", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create customer (financial manager only)"""
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

@app.get("/customers", response_model=List[CustomerResponse])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Get customers (financial manager only)"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.FINANCIAL_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers

@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
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
@app.post("/meters", response_model=WaterMeterResponse)
async def create_water_meter(
    meter_data: WaterMeterCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create water meter (financial manager only)"""
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

@app.get("/meters")
async def get_water_meters(
    customer_id: Optional[int] = None,
    active_only: bool = True,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
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
@app.post("/readings", response_model=MeterReadingResponse)
async def create_meter_reading(
    reading_data: MeterReadingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
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

@app.get("/readings")
async def get_meter_readings(
    meter_id: Optional[str] = None,
    customer_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
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
@app.get("/bills", response_model=List[BillResponse])
async def get_bills(
    request: Request,
    customer_id: Optional[int] = None,
    status: Optional[BillStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
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

@app.get("/bills/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: int,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
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

@app.post("/bills/generate")
async def generate_bills(
    month: int,
    year: int,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Generate bills for all customers (financial manager only)"""
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
@app.post("/contests", response_model=BillContestResponse)
async def create_bill_contest(
    contest_data: BillContestCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Contest a bill (citizen only)"""
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

@app.get("/contests", response_model=List[BillContestResponse])
async def get_bill_contests(
    request: Request,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
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

@app.put("/contests/{contest_id}/resolve")
async def resolve_bill_contest(
    contest_id: int,
    resolution: str,
    approved: bool,
    request: Request,
    new_amount: Optional[float] = None,
    db: Session = Depends(get_db_session)
):
    """Resolve bill contest (financial manager only)"""
    authorization = request.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.FINANCIAL_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    contest = db.query(BillContest).filter(BillContest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    
    bill = db.query(Bill).filter(Bill.id == contest.bill_id).first()
    
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
    
    return {"message": "Contest resolved successfully"}

@app.put("/debt-negotiations/{negotiation_id}/resolve")
async def resolve_debt_negotiation(
    negotiation_id: int,
    approved: bool,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Resolve debt negotiation (financial manager only)"""
    authorization = request.headers.get("Authorization")
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.FINANCIAL_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    negotiation = db.query(DebtNegotiation).filter(DebtNegotiation.id == negotiation_id).first()
    if not negotiation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negotiation not found")
    
    if negotiation.status != "proposed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negotiation is not in proposed status")
    
    negotiation.status = "active" if approved else "cancelled"
    if approved:
        negotiation.start_date = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Negotiation resolved successfully"}

# Debt Negotiation
@app.post("/negotiations", response_model=DebtNegotiationResponse)
async def create_debt_negotiation(
    negotiation_data: DebtNegotiationCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create debt negotiation (financial manager only)"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.FINANCIAL_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Check if customer has active negotiation
    existing = db.query(DebtNegotiation).filter(
        DebtNegotiation.customer_id == negotiation_data.customer_id,
        DebtNegotiation.status == "active"
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer already has active negotiation")
    
    # Calculate negotiation terms
    overdue_bills = db.query(Bill).filter(
        Bill.customer_id == negotiation_data.customer_id,
        Bill.status == BillStatus.OVERDUE
    ).all()
    
    total_debt = sum(bill.amount for bill in overdue_bills)
    
    negotiation = DebtNegotiation(
        **negotiation_data.dict(),
        total_debt=total_debt,
        status="proposed"
    )
    db.add(negotiation)
    db.commit()
    db.refresh(negotiation)
    
    return negotiation

@app.get("/negotiations", response_model=List[DebtNegotiationResponse])
async def get_debt_negotiations(
    request: Request,
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db_session)
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

# Payment Processing
@app.post("/payments", response_model=PaymentResponse)
async def process_payment(
    payment_data: PaymentCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
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
@app.post("/tariffs", response_model=TariffRateResponse)
async def create_tariff_rate(
    tariff_data: TariffRateCreate,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
):
    """Create tariff rate (financial manager only)"""
    user = await verify_user_token(authorization)
    if user["role"] != UserRole.FINANCIAL_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    tariff = TariffRate(**tariff_data.dict())
    db.add(tariff)
    db.commit()
    db.refresh(tariff)
    
    return tariff

@app.get("/tariffs")
async def get_tariff_rates(
    active_only: bool = True,
    authorization: str = Depends(lambda request: request.headers.get("Authorization")),
    db: Session = Depends(get_db_session)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
