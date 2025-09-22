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
                "id": 5,
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
            {
                "bill_id": 2,
                "protocol_number": "CONTEST-001-2024",
                "reason": "Consumo muito alto para o período",
                "description": "Suspeito de vazamento não detectado ou erro na leitura do hidrômetro.",
                "status": "pending",
                "created_at": datetime(2024, 9, 11, 14, 30, 0)
            },
            {
                "bill_id": 6,
                "protocol_number": "CONTEST-002-2024",
                "reason": "Fatura cobrada com imóvel desocupado",
                "description": "Fatura cobrada mesmo com imóvel desocupado durante todo o mês de julho.",
                "status": "approved",
                "resolution": "Após verificação, confirmamos que o imóvel estava desocupado. Valor será ajustado na próxima fatura.",
                "resolved_at": datetime(2024, 9, 15, 16, 0, 0),
                "created_at": datetime(2024, 9, 6, 9, 15, 0)
            },
            {
                "bill_id": 4,
                "protocol_number": "CONTEST-003-2024",
                "reason": "Taxa de esgoto incorreta",
                "description": "Cobrança de taxa de esgoto incorreta.",
                "status": "rejected",
                "resolution": "A taxa de esgoto está correta conforme regulamentação municipal vigente.",
                "resolved_at": datetime(2024, 9, 25, 10, 0, 0),
                "created_at": datetime(2024, 9, 21, 16, 45, 0)
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
            {
                "customer_id": 2,
                "total_debt": Decimal("1250.80"),
                "installments": 6,
                "installment_amount": Decimal("208.47"),
                "discount_percentage": 5.0,
                "interest_rate": 1.2,
                "status": "active",
                "start_date": datetime(2024, 8, 15),
                "created_at": datetime(2024, 8, 15, 11, 0, 0)
            },
            {
                "customer_id": 3,
                "total_debt": Decimal("650.40"),
                "installments": 4,
                "installment_amount": Decimal("162.60"),
                "status": "proposed",
                "created_at": datetime(2024, 9, 10, 13, 20, 0)
            },
            {
                "customer_id": 1,
                "total_debt": Decimal("890.30"),
                "installments": 12,
                "installment_amount": Decimal("74.19"),
                "status": "completed",
                "start_date": datetime(2024, 1, 15),
                "created_at": datetime(2024, 1, 15, 10, 30, 0)
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
            {
                "bill_id": 3,
                "amount": Decimal("67.80"),
                "payment_method": "credit_card",
                "payment_date": datetime(2024, 8, 12, 14, 30, 0),
                "transaction_id": "TXN-001-2024",
                "status": "completed"
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