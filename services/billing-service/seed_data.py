#!/usr/bin/env python3
"""
Seed script to populate the billing database with mock data
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add shared modules to path
sys.path.append('/app/shared')

from database import get_database_url, create_database_engine, get_session_local
from database_models import (
    Base, Customer, WaterMeter, MeterReading, Bill, 
    BillContest, DebtNegotiation, Payment, TariffRate
)
from models import BillStatus

def create_tables_and_seed():
    """Create all tables and seed with mock data"""
    try:
        # Database setup
        database_url = get_database_url("billing")
        engine = create_database_engine(database_url)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Billing database tables created successfully")
        
        # Create session
        SessionLocal = get_session_local(engine)
        db = SessionLocal()
        
        # Check if data already exists
        existing_customers = db.query(Customer).count()
        if existing_customers > 0:
            print(f"⚠️  Database already has {existing_customers} customers. Skipping seed.")
            db.close()
            return
        
        # Create customers
        customers_data = [
            {
                "id": 1,
                "user_id": 1,  # Reference to auth user
                "name": "João Silva",
                "document": "12345678901",
                "email": "joao.silva@email.com",
                "phone": "(11) 99999-1111",
                "address": "Rua das Flores, 123 - Centro - São Paulo/SP",
                "customer_type": "residential"
            },
            {
                "id": 2,
                "user_id": 2,
                "name": "Maria Santos",
                "document": "23456789012",
                "email": "maria.santos@email.com",
                "phone": "(11) 99999-2222",
                "address": "Av. Paulista, 456 - Bela Vista - São Paulo/SP",
                "customer_type": "commercial"
            },
            {
                "id": 3,
                "user_id": 3,
                "name": "Pedro Oliveira",
                "document": "34567890123",
                "email": "pedro.oliveira@email.com",
                "phone": "(11) 99999-3333",
                "address": "Rua Augusta, 789 - Consolação - São Paulo/SP",
                "customer_type": "residential"
            },
            {
                "id": 4,
                "user_id": None,
                "name": "Ana Costa",
                "document": "45678901234",
                "email": "ana.costa@email.com",
                "phone": "(11) 99999-4444",
                "address": "Rua da Paz, 321 - Vila Madalena - São Paulo/SP",
                "customer_type": "residential"
            },
            {
                "id": 5,
                "user_id": None,
                "name": "Carlos Ferreira",
                "document": "56789012345",
                "email": "carlos.ferreira@email.com",
                "phone": "(11) 99999-5555",
                "address": "Av. Industrial, 1000 - Distrito Industrial - São Paulo/SP",
                "customer_type": "industrial"
            },
            {
                "id": 6,
                "user_id": None,
                "name": "Luciana Rocha",
                "document": "67890123456",
                "email": "luciana.rocha@email.com",
                "phone": "(11) 99999-6666",
                "address": "Rua das Acácias, 159 - Jardim Botânico - São Paulo/SP",
                "customer_type": "residential"
            },
            {
                "id": 7,
                "user_id": None,
                "name": "Roberto Lima",
                "document": "78901234567",
                "email": "roberto.lima@email.com",
                "phone": "(11) 99999-7777",
                "address": "Av. Comercial, 500 - Centro Comercial - São Paulo/SP",
                "customer_type": "commercial"
            }
        ]
        
        customers = []
        for customer_data in customers_data:
            customer = Customer(**customer_data)
            customers.append(customer)
            db.add(customer)
        
        db.commit()
        print(f"✅ Created {len(customers)} customers")
        
        # Create water meters
        meters_data = [
            {
                "meter_id": "METER-001",
                "customer_id": 1,
                "location": "Entrada principal",
                "installation_date": datetime(2023, 1, 15),
                "last_reading": 245.8,
                "last_reading_date": datetime(2024, 9, 15)
            },
            {
                "meter_id": "METER-002", 
                "customer_id": 2,
                "location": "Subsolo comercial",
                "installation_date": datetime(2023, 3, 20),
                "last_reading": 1205.6,
                "last_reading_date": datetime(2024, 9, 20)
            },
            {
                "meter_id": "METER-003",
                "customer_id": 3,
                "location": "Área de serviço",
                "installation_date": datetime(2023, 2, 10),
                "last_reading": 156.3,
                "last_reading_date": datetime(2024, 9, 12)
            },
            {
                "meter_id": "METER-004",
                "customer_id": 4,
                "location": "Jardim frontal",
                "installation_date": datetime(2023, 4, 5),
                "last_reading": 89.2,
                "last_reading_date": datetime(2024, 9, 18)
            },
            {
                "meter_id": "METER-005",
                "customer_id": 5,
                "location": "Área industrial",
                "installation_date": datetime(2023, 5, 10),
                "last_reading": 2850.7,
                "last_reading_date": datetime(2024, 9, 25)
            },
            {
                "meter_id": "METER-006",
                "customer_id": 6,
                "location": "Quintal",
                "installation_date": datetime(2023, 6, 15),
                "last_reading": 124.5,
                "last_reading_date": datetime(2024, 9, 22)
            },
            {
                "meter_id": "METER-007",
                "customer_id": 7,
                "location": "Entrada comercial",
                "installation_date": datetime(2023, 7, 20),
                "last_reading": 678.9,
                "last_reading_date": datetime(2024, 9, 28)
            }
        ]
        
        meters = []
        for meter_data in meters_data:
            meter = WaterMeter(**meter_data)
            meters.append(meter)
            db.add(meter)
        
        db.commit()
        print(f"✅ Created {len(meters)} water meters")
        
        # Create tariff rates
        tariff_rates_data = [
            {
                "customer_type": "residential",
                "tier_start": 0.0,
                "tier_end": 10.0,
                "rate_per_m3": Decimal("3.50"),
                "fixed_charge": Decimal("25.00"),
                "effective_date": datetime(2024, 1, 1)
            },
            {
                "customer_type": "residential",
                "tier_start": 10.0,
                "tier_end": 20.0,
                "rate_per_m3": Decimal("4.20"),
                "fixed_charge": Decimal("0.00"),
                "effective_date": datetime(2024, 1, 1)
            },
            {
                "customer_type": "residential",
                "tier_start": 20.0,
                "tier_end": None,
                "rate_per_m3": Decimal("5.80"),
                "fixed_charge": Decimal("0.00"),
                "effective_date": datetime(2024, 1, 1)
            },
            {
                "customer_type": "commercial",
                "tier_start": 0.0,
                "tier_end": None,
                "rate_per_m3": Decimal("6.50"),
                "fixed_charge": Decimal("45.00"),
                "effective_date": datetime(2024, 1, 1)
            }
        ]
        
        tariff_rates = []
        for rate_data in tariff_rates_data:
            rate = TariffRate(**rate_data)
            tariff_rates.append(rate)
            db.add(rate)
        
        db.commit()
        print(f"✅ Created {len(tariff_rates)} tariff rates")
        
        # Create bills based on mock data structure
        bills_data = [
            # João Silva (Customer 1) - METER-001
            {
                "id": 1,
                "customer_id": 1,
                "meter_id": "METER-001",
                "amount": Decimal("85.50"),
                "consumption": 15.2,
                "billing_period_start": datetime(2024, 8, 15),
                "billing_period_end": datetime(2024, 9, 15),
                "due_date": datetime(2024, 10, 15),
                "status": BillStatus.PENDING,
                "created_at": datetime(2024, 9, 15, 10, 0, 0)
            },
            {
                "id": 2,
                "customer_id": 1,
                "meter_id": "METER-001",
                "amount": Decimal("125.30"),
                "consumption": 22.1,
                "billing_period_start": datetime(2024, 7, 15),
                "billing_period_end": datetime(2024, 8, 15),
                "due_date": datetime(2024, 9, 10),
                "status": BillStatus.OVERDUE,
                "created_at": datetime(2024, 8, 15, 10, 0, 0)
            },
            {
                "id": 3,
                "customer_id": 1,
                "meter_id": "METER-001",
                "amount": Decimal("67.80"),
                "consumption": 12.5,
                "billing_period_start": datetime(2024, 6, 15),
                "billing_period_end": datetime(2024, 7, 15),
                "due_date": datetime(2024, 8, 15),
                "status": BillStatus.PAID,
                "paid_at": datetime(2024, 8, 12, 14, 30, 0),
                "created_at": datetime(2024, 7, 15, 10, 0, 0)
            },
            {
                "id": 4,
                "customer_id": 1,
                "meter_id": "METER-001",
                "amount": Decimal("98.40"),
                "consumption": 18.7,
                "billing_period_start": datetime(2024, 5, 15),
                "billing_period_end": datetime(2024, 6, 15),
                "due_date": datetime(2024, 7, 15),
                "status": BillStatus.PAID,
                "paid_at": datetime(2024, 7, 10, 16, 20, 0),
                "created_at": datetime(2024, 6, 15, 10, 0, 0)
            },
            
            # Maria Santos (Customer 2) - METER-002 (Commercial)
            {
                "id": 5,
                "customer_id": 2,
                "meter_id": "METER-002",
                "amount": Decimal("198.75"),
                "consumption": 35.8,
                "billing_period_start": datetime(2024, 8, 20),
                "billing_period_end": datetime(2024, 9, 20),
                "due_date": datetime(2024, 10, 20),
                "status": BillStatus.PENDING,
                "created_at": datetime(2024, 9, 20, 10, 0, 0)
            },
            {
                "id": 6,
                "customer_id": 2,
                "meter_id": "METER-002",
                "amount": Decimal("156.40"),
                "consumption": 28.3,
                "billing_period_start": datetime(2024, 7, 5),
                "billing_period_end": datetime(2024, 8, 5),
                "due_date": datetime(2024, 9, 5),
                "status": BillStatus.OVERDUE,
                "created_at": datetime(2024, 8, 5, 10, 0, 0)
            },
            {
                "id": 7,
                "customer_id": 2,
                "meter_id": "METER-002",
                "amount": Decimal("189.30"),
                "consumption": 32.5,
                "billing_period_start": datetime(2024, 6, 5),
                "billing_period_end": datetime(2024, 7, 5),
                "due_date": datetime(2024, 8, 5),
                "status": BillStatus.OVERDUE,
                "created_at": datetime(2024, 7, 5, 10, 0, 0)
            },
            
            # Pedro Oliveira (Customer 3) - METER-003
            {
                "id": 8,
                "customer_id": 3,
                "meter_id": "METER-003",
                "amount": Decimal("45.60"),
                "consumption": 8.9,
                "billing_period_start": datetime(2024, 8, 12),
                "billing_period_end": datetime(2024, 9, 12),
                "due_date": datetime(2024, 10, 12),
                "status": BillStatus.PENDING,
                "created_at": datetime(2024, 9, 12, 10, 0, 0)
            },
            {
                "id": 9,
                "customer_id": 3,
                "meter_id": "METER-003",
                "amount": Decimal("52.30"),
                "consumption": 11.2,
                "billing_period_start": datetime(2024, 7, 12),
                "billing_period_end": datetime(2024, 8, 12),
                "due_date": datetime(2024, 9, 12),
                "status": BillStatus.PAID,
                "paid_at": datetime(2024, 9, 8, 11, 15, 0),
                "created_at": datetime(2024, 8, 12, 10, 0, 0)
            },
            
            # Ana Costa (Customer 4) - METER-004
            {
                "id": 10,
                "customer_id": 4,
                "meter_id": "METER-004",
                "amount": Decimal("78.90"),
                "consumption": 14.8,
                "billing_period_start": datetime(2024, 8, 18),
                "billing_period_end": datetime(2024, 9, 18),
                "due_date": datetime(2024, 10, 18),
                "status": BillStatus.PENDING,
                "created_at": datetime(2024, 9, 18, 10, 0, 0)
            },
            {
                "id": 11,
                "customer_id": 4,
                "meter_id": "METER-004",
                "amount": Decimal("143.20"),
                "consumption": 25.6,
                "billing_period_start": datetime(2024, 7, 18),
                "billing_period_end": datetime(2024, 8, 18),
                "due_date": datetime(2024, 9, 18),
                "status": BillStatus.OVERDUE,
                "created_at": datetime(2024, 8, 18, 10, 0, 0)
            },
            
            # Carlos Ferreira (Customer 5) - METER-005 (Industrial)
            {
                "id": 12,
                "customer_id": 5,
                "meter_id": "METER-005",
                "amount": Decimal("450.80"),
                "consumption": 125.3,
                "billing_period_start": datetime(2024, 8, 25),
                "billing_period_end": datetime(2024, 9, 25),
                "due_date": datetime(2024, 10, 25),
                "status": BillStatus.PENDING,
                "created_at": datetime(2024, 9, 25, 10, 0, 0)
            },
            {
                "id": 13,
                "customer_id": 5,
                "meter_id": "METER-005",
                "amount": Decimal("523.40"),
                "consumption": 142.8,
                "billing_period_start": datetime(2024, 7, 25),
                "billing_period_end": datetime(2024, 8, 25),
                "due_date": datetime(2024, 9, 25),
                "status": BillStatus.OVERDUE,
                "created_at": datetime(2024, 8, 25, 10, 0, 0)
            },
            
            # Luciana Rocha (Customer 6) - METER-006
            {
                "id": 14,
                "customer_id": 6,
                "meter_id": "METER-006",
                "amount": Decimal("63.70"),
                "consumption": 12.8,
                "billing_period_start": datetime(2024, 8, 22),
                "billing_period_end": datetime(2024, 9, 22),
                "due_date": datetime(2024, 10, 22),
                "status": BillStatus.PENDING,
                "created_at": datetime(2024, 9, 22, 10, 0, 0)
            },
            {
                "id": 15,
                "customer_id": 6,
                "meter_id": "METER-006",
                "amount": Decimal("58.20"),
                "consumption": 11.5,
                "billing_period_start": datetime(2024, 7, 22),
                "billing_period_end": datetime(2024, 8, 22),
                "due_date": datetime(2024, 9, 22),
                "status": BillStatus.PAID,
                "paid_at": datetime(2024, 9, 18, 13, 45, 0),
                "created_at": datetime(2024, 8, 22, 10, 0, 0)
            },
            
            # Roberto Lima (Customer 7) - METER-007 (Commercial)
            {
                "id": 16,
                "customer_id": 7,
                "meter_id": "METER-007",
                "amount": Decimal("234.60"),
                "consumption": 42.3,
                "billing_period_start": datetime(2024, 8, 28),
                "billing_period_end": datetime(2024, 9, 28),
                "due_date": datetime(2024, 10, 28),
                "status": BillStatus.PENDING,
                "created_at": datetime(2024, 9, 28, 10, 0, 0)
            },
            {
                "id": 17,
                "customer_id": 7,
                "meter_id": "METER-007",
                "amount": Decimal("267.80"),
                "consumption": 48.9,
                "billing_period_start": datetime(2024, 7, 28),
                "billing_period_end": datetime(2024, 8, 28),
                "due_date": datetime(2024, 9, 28),
                "status": BillStatus.OVERDUE,
                "created_at": datetime(2024, 8, 28, 10, 0, 0)
            }
        ]
        
        bills = []
        for bill_data in bills_data:
            bill = Bill(**bill_data)
            bills.append(bill)
            db.add(bill)
        
        db.commit()
        print(f"✅ Created {len(bills)} bills")
        
        # Create bill contests (disputes)
        contests_data = [
            # Contestação da Fatura 2 (João Silva - OVERDUE)
            {
                "bill_id": 2,
                "protocol_number": "CONTEST-001-2024",
                "reason": "Consumo muito alto para o período",
                "description": "Suspeito de vazamento não detectado ou erro na leitura do hidrômetro. Consumo de 22.1m³ é muito acima da média mensal de 12-15m³.",
                "status": "pending",
                "created_at": datetime(2024, 9, 11, 14, 30, 0)
            },
            # Contestação da Fatura 6 (Maria Santos - OVERDUE Commercial)
            {
                "bill_id": 6,
                "protocol_number": "CONTEST-002-2024", 
                "reason": "Fatura cobrada com estabelecimento fechado",
                "description": "Estabelecimento comercial esteve fechado durante todo o mês de julho por reforma. Não deveria haver consumo tão alto.",
                "status": "approved",
                "resolution": "Após verificação, confirmamos que o estabelecimento estava fechado durante a reforma. Valor será ajustado na próxima fatura.",
                "resolved_at": datetime(2024, 9, 15, 16, 0, 0),
                "created_at": datetime(2024, 9, 6, 9, 15, 0)
            },
            # Contestação da Fatura 7 (Maria Santos - OVERDUE Commercial)
            {
                "bill_id": 7,
                "protocol_number": "CONTEST-003-2024",
                "reason": "Taxa de esgoto incorreta",
                "description": "Cobrança de taxa de esgoto incorreta para estabelecimento comercial.",
                "status": "rejected",
                "resolution": "A taxa de esgoto está correta conforme regulamentação municipal vigente para estabelecimentos comerciais.",
                "resolved_at": datetime(2024, 9, 25, 10, 0, 0),
                "created_at": datetime(2024, 9, 20, 11, 45, 0)
            },
            # Contestação da Fatura 11 (Ana Costa - OVERDUE)
            {
                "bill_id": 11,
                "protocol_number": "CONTEST-004-2024",
                "reason": "Valor muito alto comparado aos meses anteriores",
                "description": "Fatura de R$ 143,20 é muito superior ao histórico de consumo. Normalmente gasto entre R$ 60-80 por mês.",
                "status": "under_review",
                "created_at": datetime(2024, 9, 19, 15, 20, 0)
            },
            # Contestação da Fatura 13 (Carlos Ferreira - Industrial OVERDUE)
            {
                "bill_id": 13,
                "protocol_number": "CONTEST-005-2024",
                "reason": "Erro na categoria tarifária",
                "description": "Fatura cobrada com tarifa residencial quando deveria ser industrial. Empresa possui cadastro industrial ativo.",
                "status": "approved",
                "resolution": "Erro confirmado na categoria tarifária. Recálculo será feito e diferença creditada na próxima fatura.",
                "resolved_at": datetime(2024, 10, 2, 9, 30, 0),
                "created_at": datetime(2024, 9, 26, 8, 15, 0)
            },
            # Contestação da Fatura 18 (Roberto Lima - Commercial OVERDUE)
            {
                "bill_id": 17,
                "protocol_number": "CONTEST-006-2024",
                "reason": "Hidrômetro com defeito",
                "description": "Suspeita de defeito no hidrômetro. Leitura inconsistente - muito alta para o padrão do estabelecimento.",
                "status": "pending",
                "created_at": datetime(2024, 9, 29, 16, 45, 0)
            },
            # Contestação da Fatura 10 (Ana Costa - PENDING)
            {
                "bill_id": 10,
                "protocol_number": "CONTEST-007-2024",
                "reason": "Cobrança de multa indevida",
                "description": "Fatura inclui multa por atraso mas o pagamento foi feito dentro do prazo no mês anterior.",
                "status": "under_review",
                "created_at": datetime(2024, 10, 1, 10, 30, 0)
            },
            # Contestação da Fatura 12 (Carlos Ferreira - Industrial PENDING)
            {
                "bill_id": 12,
                "protocol_number": "CONTEST-008-2024",
                "reason": "Desconto industrial não aplicado",
                "description": "Desconto para grandes consumidores industriais não foi aplicado conforme contrato vigente.",
                "status": "approved",
                "resolution": "Desconto confirmado no contrato. Será aplicado retroativamente nas próximas faturas.",
                "resolved_at": datetime(2024, 10, 3, 14, 15, 0),
                "created_at": datetime(2024, 9, 30, 13, 0, 0)
            },
            # Contestação da Fatura 16 (Roberto Lima - Commercial PENDING)
            {
                "bill_id": 16,
                "protocol_number": "CONTEST-009-2024",
                "reason": "Leitura estimada incorreta",
                "description": "Fatura baseada em leitura estimada muito superior ao consumo real. Solicito releitura do hidrômetro.",
                "status": "pending",
                "created_at": datetime(2024, 10, 2, 11, 20, 0)
            },
            # Contestação da Fatura 14 (Luciana Rocha - PENDING)
            {
                "bill_id": 14,
                "protocol_number": "CONTEST-010-2024",
                "reason": "Taxa de iluminação pública duplicada",
                "description": "Cobrança duplicada da taxa de iluminação pública nesta fatura.",
                "status": "rejected",
                "resolution": "Verificação realizada. Não há cobrança duplicada. Taxa está correta conforme legislação municipal.",
                "resolved_at": datetime(2024, 10, 4, 15, 45, 0),
                "created_at": datetime(2024, 9, 28, 14, 10, 0)
            }
        ]
        
        contests = []
        for contest_data in contests_data:
            contest = BillContest(**contest_data)
            contests.append(contest)
            db.add(contest)
        
        db.commit()
        print(f"✅ Created {len(contests)} bill contests")
        
        # Create debt negotiations
        negotiations_data = [
            # João Silva (Customer 1) - Negociação ativa para faturas em atraso
            {
                "customer_id": 1,
                "total_debt": Decimal("253.10"),  # Faturas 2 + outros débitos
                "installments": 6,
                "installment_amount": Decimal("42.18"),
                "discount_percentage": 8.0,
                "interest_rate": 1.5,
                "status": "active",
                "start_date": datetime(2024, 9, 20),
                "created_at": datetime(2024, 9, 20, 11, 0, 0)
            },
            # Maria Santos (Customer 2) - Negociação proposta para comercial
            {
                "customer_id": 2,
                "total_debt": Decimal("545.85"),  # Faturas 6 + 7 + juros
                "installments": 10,
                "installment_amount": Decimal("54.59"),
                "discount_percentage": 15.0,
                "interest_rate": 2.0,
                "status": "proposed",
                "created_at": datetime(2024, 10, 1, 14, 30, 0)
            },
            # Pedro Oliveira (Customer 3) - Negociação completada
            {
                "customer_id": 3,
                "total_debt": Decimal("180.50"),
                "installments": 4,
                "installment_amount": Decimal("45.13"),
                "discount_percentage": 5.0,
                "status": "completed",
                "start_date": datetime(2024, 7, 15),
                "end_date": datetime(2024, 9, 15),
                "created_at": datetime(2024, 7, 15, 10, 30, 0)
            },
            # Ana Costa (Customer 4) - Negociação ativa para fatura em atraso
            {
                "customer_id": 4,
                "total_debt": Decimal("167.30"),  # Fatura 11 + juros
                "installments": 3,
                "installment_amount": Decimal("55.77"),
                "discount_percentage": 12.0,
                "interest_rate": 1.8,
                "status": "active",
                "start_date": datetime(2024, 9, 25),
                "created_at": datetime(2024, 9, 25, 15, 45, 0)
            },
            # Carlos Ferreira (Customer 5) - Negociação industrial em análise
            {
                "customer_id": 5,
                "total_debt": Decimal("1156.70"),  # Fatura 13 + histórico
                "installments": 18,
                "installment_amount": Decimal("64.26"),
                "discount_percentage": 20.0,
                "interest_rate": 1.0,
                "status": "under_review",
                "created_at": datetime(2024, 10, 2, 9, 15, 0)
            },
            # Luciana Rocha (Customer 6) - Negociação rejeitada
            {
                "customer_id": 6,
                "total_debt": Decimal("127.40"),
                "installments": 2,
                "installment_amount": Decimal("63.70"),
                "status": "rejected",
                "rejection_reason": "Cliente não atendeu aos critérios mínimos para parcelamento",
                "created_at": datetime(2024, 9, 18, 11, 20, 0)
            },
            # Roberto Lima (Customer 7) - Negociação comercial em proposta
            {
                "customer_id": 7,
                "total_debt": Decimal("502.40"),  # Fatura 17 + taxas
                "installments": 8,
                "installment_amount": Decimal("62.80"),
                "discount_percentage": 10.0,
                "interest_rate": 1.5,
                "status": "proposed",
                "created_at": datetime(2024, 10, 3, 16, 10, 0)
            },
            # João Silva (Customer 1) - Negociação anterior já completada
            {
                "customer_id": 1,
                "total_debt": Decimal("345.60"),
                "installments": 12,
                "installment_amount": Decimal("28.80"),
                "discount_percentage": 10.0,
                "status": "completed",
                "start_date": datetime(2024, 3, 10),
                "end_date": datetime(2024, 8, 10),
                "created_at": datetime(2024, 3, 10, 14, 0, 0)
            },
            # Maria Santos (Customer 2) - Negociação cancelada anterior
            {
                "customer_id": 2,
                "total_debt": Decimal("289.70"),
                "installments": 5,
                "installment_amount": Decimal("57.94"),
                "status": "cancelled",
                "cancellation_reason": "Cliente optou pelo pagamento à vista",
                "created_at": datetime(2024, 8, 5, 10, 45, 0)
            },
            # Carlos Ferreira (Customer 5) - Negociação anterior ativa
            {
                "customer_id": 5,
                "total_debt": Decimal("2340.80"),
                "installments": 24,
                "installment_amount": Decimal("97.53"),
                "discount_percentage": 25.0,
                "interest_rate": 0.8,
                "status": "active",
                "start_date": datetime(2024, 6, 1),
                "created_at": datetime(2024, 6, 1, 8, 30, 0)
            },
            # Ana Costa (Customer 4) - Negociação rejeitada anterior
            {
                "customer_id": 4,
                "total_debt": Decimal("98.50"),
                "installments": 2,
                "installment_amount": Decimal("49.25"),
                "status": "rejected",
                "rejection_reason": "Valor mínimo não atingido para parcelamento",
                "created_at": datetime(2024, 8, 12, 13, 15, 0)
            },
            # Roberto Lima (Customer 7) - Negociação completada anterior
            {
                "customer_id": 7,
                "total_debt": Decimal("789.40"),
                "installments": 15,
                "installment_amount": Decimal("52.63"),
                "discount_percentage": 18.0,
                "status": "completed",
                "start_date": datetime(2024, 4, 20),
                "end_date": datetime(2024, 9, 20),
                "created_at": datetime(2024, 4, 20, 11, 40, 0)
            }
        ]
        
        negotiations = []
        for negotiation_data in negotiations_data:
            negotiation = DebtNegotiation(**negotiation_data)
            negotiations.append(negotiation)
            db.add(negotiation)
        
        db.commit()
        print(f"✅ Created {len(negotiations)} debt negotiations")
        
        # Create payments for paid bills
        payments_data = [
            # Pagamento da Fatura 3 (João Silva)
            {
                "bill_id": 3,
                "amount": Decimal("67.80"),
                "payment_method": "credit_card",
                "payment_date": datetime(2024, 8, 12, 14, 30, 0),
                "transaction_id": "TXN-001-2024",
                "status": "completed"
            },
            # Pagamento da Fatura 4 (João Silva)
            {
                "bill_id": 4,
                "amount": Decimal("98.40"),
                "payment_method": "bank_slip",
                "payment_date": datetime(2024, 7, 10, 16, 20, 0),
                "transaction_id": "TXN-002-2024",
                "status": "completed"
            },
            # Pagamento da Fatura 9 (Pedro Oliveira)
            {
                "bill_id": 9,
                "amount": Decimal("52.30"),
                "payment_method": "pix",
                "payment_date": datetime(2024, 9, 8, 11, 15, 0),
                "transaction_id": "TXN-003-2024",
                "status": "completed"
            },
            # Pagamento da Fatura 15 (Luciana Rocha)
            {
                "bill_id": 15,
                "amount": Decimal("58.20"),
                "payment_method": "debit_card",
                "payment_date": datetime(2024, 9, 18, 13, 45, 0),
                "transaction_id": "TXN-004-2024",
                "status": "completed"
            },
            # Pagamento parcial da Fatura 2 (João Silva) - primeira parcela da negociação
            {
                "bill_id": 2,
                "amount": Decimal("42.18"),
                "payment_method": "pix",
                "payment_date": datetime(2024, 9, 25, 10, 0, 0),
                "transaction_id": "TXN-005-2024",
                "status": "completed",
                "installment_number": 1
            },
            # Pagamento parcial da Fatura 2 (João Silva) - segunda parcela da negociação
            {
                "bill_id": 2,
                "amount": Decimal("42.18"),
                "payment_method": "pix",
                "payment_date": datetime(2024, 10, 25, 10, 0, 0),
                "transaction_id": "TXN-006-2024",
                "status": "completed",
                "installment_number": 2
            },
            # Tentativa de pagamento falhou (Carlos Ferreira)
            {
                "bill_id": 13,
                "amount": Decimal("523.40"),
                "payment_method": "credit_card",
                "payment_date": datetime(2024, 9, 30, 15, 20, 0),
                "transaction_id": "TXN-007-2024",
                "status": "failed",
                "failure_reason": "Cartão recusado - limite insuficiente"
            },
            # Pagamento em processamento (Ana Costa)
            {
                "bill_id": 11,
                "amount": Decimal("55.77"),
                "payment_method": "bank_slip",
                "payment_date": datetime(2024, 10, 1, 9, 30, 0),
                "transaction_id": "TXN-008-2024",
                "status": "processing",
                "installment_number": 1
            },
            # Estorno de pagamento (Maria Santos)
            {
                "bill_id": 6,
                "amount": Decimal("156.40"),
                "payment_method": "credit_card",
                "payment_date": datetime(2024, 9, 10, 14, 15, 0),
                "transaction_id": "TXN-009-2024",
                "status": "refunded",
                "refund_reason": "Pagamento duplicado"
            },
            # Pagamento via negotiation installment (Pedro Oliveira)
            {
                "bill_id": 8,
                "amount": Decimal("45.13"),
                "payment_method": "bank_transfer",
                "payment_date": datetime(2024, 8, 15, 12, 0, 0),
                "transaction_id": "TXN-010-2024",
                "status": "completed",
                "installment_number": 1
            },
            # Pagamento de multa adicional (Roberto Lima)
            {
                "bill_id": 17,
                "amount": Decimal("26.78"),
                "payment_method": "pix",
                "payment_date": datetime(2024, 10, 2, 16, 30, 0),
                "transaction_id": "TXN-011-2024",
                "status": "completed",
                "payment_type": "late_fee"
            },
            # Pagamento com desconto (Luciana Rocha)
            {
                "bill_id": 14,
                "amount": Decimal("57.33"),  # Com desconto
                "payment_method": "credit_card",
                "payment_date": datetime(2024, 10, 3, 11, 45, 0),
                "transaction_id": "TXN-012-2024",
                "status": "completed",
                "discount_applied": Decimal("6.37")
            }
        ]
        
        payments = []
        for payment_data in payments_data:
            payment = Payment(**payment_data)
            payments.append(payment)
            db.add(payment)
        
        db.commit()
        print(f"✅ Created {len(payments)} payments")
        
        # Create meter readings
        readings_data = [
            # Customer 1 readings
            {"meter_id": "METER-001", "reading_value": 230.6, "consumption": 12.5, "reading_date": datetime(2024, 7, 15)},
            {"meter_id": "METER-001", "reading_value": 245.8, "consumption": 15.2, "reading_date": datetime(2024, 8, 15)},
            {"meter_id": "METER-001", "reading_value": 268.3, "consumption": 22.5, "reading_date": datetime(2024, 9, 15)},
            
            # Customer 2 readings
            {"meter_id": "METER-002", "reading_value": 1148.1, "consumption": 28.3, "reading_date": datetime(2024, 8, 5)},
            {"meter_id": "METER-002", "reading_value": 1183.9, "consumption": 35.8, "reading_date": datetime(2024, 9, 20)},
            
            # Customer 3 readings
            {"meter_id": "METER-003", "reading_value": 147.4, "consumption": 8.9, "reading_date": datetime(2024, 9, 12)}
        ]
        
        readings = []
        for reading_data in readings_data:
            reading = MeterReading(**reading_data)
            readings.append(reading)
            db.add(reading)
        
        db.commit()
        print(f"✅ Created {len(readings)} meter readings")
        
        db.close()
        
        print("\n🎉 BILLING DATABASE SEEDED SUCCESSFULLY!")
        print("\n📊 Summary:")
        print(f"   • {len(customers)} Customers")
        print(f"   • {len(meters)} Water Meters")
        print(f"   • {len(bills)} Bills")
        print(f"   • {len(contests)} Bill Contests")
        print(f"   • {len(negotiations)} Debt Negotiations")
        print(f"   • {len(payments)} Payments")
        print(f"   • {len(readings)} Meter Readings")
        print(f"   • {len(tariff_rates)} Tariff Rates")
        
        print("\n🔑 Test Data Available:")
        print("   • Bills with IDs 1-6")
        print("   • Customers: João Silva, Maria Santos, Pedro Oliveira")
        print("   • Bill statuses: pending, overdue, paid")
        print("   • Bill contests with different statuses")
        print("   • Active debt negotiations")
        
    except Exception as e:
        print(f"❌ Error seeding billing database: {e}")
        raise

if __name__ == "__main__":
    create_tables_and_seed()