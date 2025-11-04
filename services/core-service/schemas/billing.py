from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from decimal import Decimal
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import BillStatus

class CustomerBase(BaseModel):
    name: str = Field(
        ...,
        description="Nome completo do cliente",
        example="João da Silva",
        min_length=3,
        max_length=200
    )
    document: str = Field(
        ...,
        description="CPF ou CNPJ do cliente (apenas números)",
        example="12345678900",
        min_length=11,
        max_length=14,
        pattern="^[0-9]{11,14}$"
    )
    email: EmailStr = Field(
        ...,
        description="Email válido do cliente",
        example="joao.silva@email.com"
    )
    phone: Optional[str] = Field(
        None,
        description="Telefone de contato com DDD (formato opcional)",
        example="(55) 99999-9999",
        max_length=20
    )
    address: str = Field(
        ...,
        description="Endereço completo do cliente (rua, número, bairro, cidade, estado)",
        example="Rua das Flores, 123, Centro, São Paulo - SP",
        min_length=10,
        max_length=300
    )
    customer_type: str = Field(
        "residential",
        description="Tipo de cliente: residential (residencial), commercial (comercial) ou industrial (industrial)",
        example="residential",
        pattern="^(residential|commercial|industrial)$"
    )
    user_id: Optional[int] = Field(
        None,
        description="ID do usuário associado (opcional, usado para cidadãos)",
        example=1
    )

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
    bill_id: int = Field(
        ...,
        description="ID da fatura que está sendo contestada",
        example=1,
        gt=0
    )
    reason: str = Field(
        ...,
        description="Motivo da contestação",
        example="Fatura cobrada mesmo com imóvel desocupado durante todo o período",
        min_length=10,
        max_length=500
    )
    description: Optional[str] = Field(
        None,
        description="Descrição detalhada da contestação (opcional)",
        example="O imóvel estava desocupado de 01/01/2025 a 31/01/2025, mas foi gerada fatura de consumo de água.",
        max_length=1000
    )

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
    customer_id: int = Field(
        ...,
        description="ID do cliente para negociação de débito",
        example=1,
        gt=0
    )
    installments: int = Field(
        ...,
        description="Número de parcelas (1 a 12)",
        example=6,
        ge=1,
        le=12
    )
    installment_amount: float = Field(
        ...,
        description="Valor de cada parcela em reais",
        example=150.50,
        gt=0
    )
    discount_percentage: float = Field(
        0.0,
        description="Percentual de desconto aplicado (0 a 100)",
        example=10.0,
        ge=0,
        le=100
    )
    interest_rate: float = Field(
        0.0,
        description="Taxa de juros mensal em percentual (0 a 5)",
        example=1.5,
        ge=0,
        le=5
    )

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
    bill_id: int = Field(
        ...,
        description="ID da fatura sendo paga",
        example=1,
        gt=0
    )
    amount: Decimal = Field(
        ...,
        description="Valor do pagamento em reais",
        example=125.75,
        gt=0
    )
    payment_method: str = Field(
        ...,
        description="Método de pagamento: pix, credit_card, debit_card, boleto ou bank_transfer",
        example="pix",
        pattern="^(pix|credit_card|debit_card|boleto|bank_transfer)$"
    )
    transaction_id: Optional[str] = Field(
        None,
        description="ID da transação (opcional, usado para rastreamento)",
        example="TXN-123456789",
        max_length=100
    )

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