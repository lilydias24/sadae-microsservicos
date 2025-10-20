from database_models import *
from database import SessionLocal, engine
from datetime import datetime, timedelta
import random

def seed_all_data():
    """Seed data for all modules in core service"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Limpar dados existentes
        db.query(Payment).delete()
        db.query(BillContest).delete()
        db.query(Bill).delete()
        db.query(Customer).delete()
        db.query(SupportTicket).delete()
        db.query(ServiceOrder).delete()
        db.query(Sensor).delete()
        
        # Seed billing data
        seed_billing_data(db)
        # Seed support data
        seed_support_data(db)
        # Seed maintenance data
        seed_maintenance_data(db)
        # Seed monitoring data
        seed_monitoring_data(db)
        # Seed teams data
        seed_teams_data(db)
        # Seed complaints data
        seed_complaints_data(db)
    
        db.commit()
        print("✅ All core service data seeded successfully")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()

def seed_teams_data(db):
    """Seed teams data"""
    teams = [
        Team(
            name="Equipe Hidráulica A",
            description="Especializada em reparos de tubulação",
            specialization="plumbing",
            members_count=4,
            max_concurrent_orders=3,
            supervisor_name="João Silva",
            supervisor_contact="(11) 99999-1111",
            is_active=True
        ),
        Team(
            name="Equipe Elétrica B",
            description="Especializada em sistemas elétricos",
            specialization="electrical",
            members_count=3,
            max_concurrent_orders=2,
            supervisor_name="Maria Santos",
            supervisor_contact="(11) 99999-2222",
            is_active=True
        ),
        Team(
            name="Equipe Geral C",
            description="Manutenção geral e emergências",
            specialization="general",
            members_count=5,
            max_concurrent_orders=4,
            supervisor_name="Pedro Costa",
            supervisor_contact="(11) 99999-3333",
            is_active=True
        )
    ]
    
    for team in teams:
        existing = db.query(Team).filter(Team.name == team.name).first()
        if not existing:
            db.add(team)

def seed_complaints_data(db):
    """Seed complaints data"""
    from datetime import datetime
    from shared.utils import generate_protocol_number
    
    complaints = [
        Complaint(
            protocol_number=generate_protocol_number(),
            title="Vazamento na Rua das Flores",
            description="Há um vazamento de água na calçada em frente ao número 123",
            category="water_leak",
            location="Rua das Flores, 123",
            citizen_name="Ana Silva",
            citizen_contact="(11) 98888-1111",
            citizen_email="ana@email.com",
            urgency_level="high",
            status="pending"
        ),
        Complaint(
            protocol_number=generate_protocol_number(),
            title="Baixa pressão da água",
            description="A pressão da água está muito baixa no bairro",
            category="pressure_issue",
            location="Bairro Centro",
            citizen_name="Carlos Santos",
            citizen_contact="(11) 98888-2222",
            citizen_email="carlos@email.com",
            urgency_level="medium",
            status="assigned",
            assigned_to="Equipe Hidráulica A"
        ),
        Complaint(
            protocol_number=generate_protocol_number(),
            title="Água com gosto estranho",
            description="A água está com gosto e cheiro estranhos",
            category="quality_issue",
            location="Rua da Paz, 456",
            citizen_name="Mariana Lima",
            citizen_contact="(11) 98888-3333",
            citizen_email="mariana@email.com",
            urgency_level="medium",
            status="in_progress"
        )
    ]
    
    for complaint in complaints:
        existing = db.query(Complaint).filter(Complaint.protocol_number == complaint.protocol_number).first()
        if not existing:
            db.add(complaint)

def seed_billing_data(db):
    """Seed billing data"""
    # Create customers
    customers = [
        Customer(name="João Silva", document="12345678901", email="joao@email.com", 
                phone="11999999999", address="Rua A, 123", customer_type="residential"),
        Customer(name="Maria Santos", document="98765432100", email="maria@email.com", 
                phone="11888888888", address="Rua B, 456", customer_type="residential"),
    ]
    
    for customer in customers:
        db.add(customer)
    db.flush()
    
    # Create bills
    for customer in customers:
        bill = Bill(
            customer_id=customer.id,
            amount=150.50,
            consumption=20.5,
            billing_period_start=datetime.now() - timedelta(days=30),
            billing_period_end=datetime.now(),
            due_date=datetime.now() + timedelta(days=10)
        )
        db.add(bill)

def seed_support_data(db):
    """Seed support data"""
    tickets = [
        SupportTicket(
            ticket_number="TK001",
            title="Problema na conta",
            description="Valor da conta muito alto",
            category="billing",
            priority="medium",
            client_id=1,
            client_name="João Silva",
            client_email="joao@email.com"
        ),
        SupportTicket(
            ticket_number="TK002", 
            title="Vazamento na rua",
            description="Há um vazamento na Rua A",
            category="technical",
            priority="high",
            client_id=2,
            client_name="Maria Santos",
            client_email="maria@email.com"
        )
    ]
    
    for ticket in tickets:
        db.add(ticket)

def seed_maintenance_data(db):
    """Seed maintenance data"""
    orders = [
        ServiceOrder(
            protocol_number="SO001",
            title="Reparo de vazamento",
            description="Reparo urgente na Rua A",
            priority="high",
            location="Rua A, 123",
            created_by=1
        )
    ]
    
    for order in orders:
        db.add(order)

def seed_monitoring_data(db):
    """Seed monitoring data"""
    sensors = [
        Sensor(
            id="SENSOR001",
            name="Sensor Pressão Centro",
            sensor_type="pressure",
            location="Centro da cidade",
            unit="bar",
            min_threshold=2.0,
            max_threshold=8.0
        ),
        Sensor(
            id="SENSOR002",
            name="Sensor Qualidade Zona Norte", 
            sensor_type="quality",
            location="Zona Norte",
            unit="pH",
            min_threshold=6.5,
            max_threshold=8.5
        )
    ]
    
    for sensor in sensors:
        db.add(sensor)

if __name__ == "__main__":
    seed_all_data()