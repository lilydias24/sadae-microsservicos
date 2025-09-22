from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from decimal import Decimal
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import BillStatus

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True)  # Reference to auth service user
    name = Column(String, nullable=False)
    document = Column(String, unique=True, nullable=False)  # CPF/CNPJ
    email = Column(String, nullable=False)
    phone = Column(String)
    address = Column(Text, nullable=False)
    customer_type = Column(String, default="residential")  # residential, commercial, industrial
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WaterMeter(Base):
    __tablename__ = "water_meters"
    
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(String, unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    location = Column(String, nullable=False)
    installation_date = Column(DateTime, nullable=False)
    last_reading = Column(Float, default=0.0)
    last_reading_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MeterReading(Base):
    __tablename__ = "meter_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(String, ForeignKey("water_meters.meter_id"), nullable=False)
    reading_value = Column(Float, nullable=False)
    reading_date = Column(DateTime, nullable=False)
    consumption = Column(Float)  # Calculated consumption since last reading
    created_at = Column(DateTime, default=datetime.utcnow)

class Bill(Base):
    __tablename__ = "bills"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    meter_id = Column(String, ForeignKey("water_meters.meter_id"))
    amount = Column(Numeric(10, 2), nullable=False)
    consumption = Column(Float, nullable=False)
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String, default=BillStatus.PENDING)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class BillContest(Base):
    __tablename__ = "bill_contests"
    
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    protocol_number = Column(String, unique=True, nullable=False)
    reason = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String, default="pending")  # pending, approved, rejected
    resolution = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class DebtNegotiation(Base):
    __tablename__ = "debt_negotiations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    total_debt = Column(Numeric(10, 2), nullable=False)
    installments = Column(Integer, nullable=False)
    installment_amount = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Float, default=0.0)
    interest_rate = Column(Float, default=0.0)
    status = Column(String, default="proposed")  # proposed, active, completed, cancelled
    start_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String, nullable=False)  # credit_card, debit_card, bank_transfer, cash
    payment_date = Column(DateTime, default=datetime.utcnow)
    transaction_id = Column(String)
    status = Column(String, default="completed")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

class TariffRate(Base):
    __tablename__ = "tariff_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_type = Column(String, nullable=False)  # residential, commercial, industrial
    tier_start = Column(Float, nullable=False)  # m³ start range
    tier_end = Column(Float)  # m³ end range (null for unlimited)
    rate_per_m3 = Column(Numeric(10, 4), nullable=False)
    fixed_charge = Column(Numeric(10, 2), default=0.0)
    effective_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
