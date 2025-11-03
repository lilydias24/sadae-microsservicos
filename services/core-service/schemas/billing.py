from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from decimal import Decimal
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import BillStatus

class CustomerBase(BaseModel):
    name: str
    document: str
    email: EmailStr
    phone: Optional[str] = None
    address: str
    customer_type: str = "residential"
    user_id: Optional[int] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class WaterMeterBase(BaseModel):
    meter_id: str
    customer_id: int
    location: str
    installation_date: datetime

class WaterMeterCreate(WaterMeterBase):
    pass

class WaterMeterResponse(WaterMeterBase):
    id: int
    last_reading: float
    last_reading_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class MeterReadingBase(BaseModel):
    meter_id: str
    reading_value: float
    reading_date: datetime

class MeterReadingCreate(MeterReadingBase):
    pass

class MeterReadingResponse(MeterReadingBase):
    id: int
    consumption: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BillBase(BaseModel):
    customer_id: int
    amount: Decimal
    consumption: float
    billing_period_start: datetime
    billing_period_end: datetime
    due_date: datetime

class BillResponse(BillBase):
    id: int
    meter_id: Optional[str]
    status: BillStatus
    paid_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BillContestBase(BaseModel):
    bill_id: int
    reason: str
    description: Optional[str] = None

class BillContestCreate(BillContestBase):
    pass

class BillContestResponse(BillContestBase):
    id: int
    protocol_number: str
    status: str
    resolution: Optional[str]
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DebtNegotiationBase(BaseModel):
    customer_id: int
    installments: int
    installment_amount: float
    discount_percentage: float = 0.0
    interest_rate: float = 0.0

class DebtNegotiationCreate(DebtNegotiationBase):
    pass

class DebtNegotiationResponse(DebtNegotiationBase):
    id: int
    total_debt: Decimal
    status: str
    start_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    bill_id: int
    amount: Decimal
    payment_method: str
    transaction_id: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    payment_date: datetime
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TariffRateBase(BaseModel):
    customer_type: str
    tier_start: float
    tier_end: Optional[float] = None
    rate_per_m3: Decimal
    fixed_charge: Decimal = Decimal('0.00')
    effective_date: datetime

class TariffRateCreate(TariffRateBase):
    pass

class TariffRateResponse(TariffRateBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True