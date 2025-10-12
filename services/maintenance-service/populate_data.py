"""
Script to populate maintenance service with sample data
"""
from sqlalchemy.orm import Session
from database_models import ServiceOrder, Complaint, Maintenance, ServiceEvaluation, Base
from database import get_database_url, create_database_engine, get_session_local
import sys
from datetime import datetime, timedelta
import random

# Add shared modules to path
sys.path.append('/app/shared')
from models import ServiceOrderStatus, AlertLevel

def populate_sample_data():
    """Populate database with sample data"""
    
    # Database setup
    DATABASE_URL = get_database_url("maintenance")
    engine = create_database_engine(DATABASE_URL)
    SessionLocal = get_session_local(engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(ServiceOrder).count() > 0:
            print("Sample data already exists, skipping population")
            return
        
        # Create sample service orders
        service_orders_data = [
            {
                "protocol_number": "OS-2024-001",
                "title": "Reparo de vazamento na rua principal",
                "description": "Vazamento de água na rua principal, próximo ao número 123. Necessário reparo urgente.",
                "priority": AlertLevel.HIGH,
                "location": "Rua Principal, 123 - Centro",
                "status": ServiceOrderStatus.OPEN,
                "created_by": 1,
                "created_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "protocol_number": "OS-2024-002",
                "title": "Manutenção preventiva da bomba principal",
                "description": "Manutenção preventiva da bomba principal do sistema de abastecimento.",
                "priority": AlertLevel.MEDIUM,
                "location": "Estação de Bombeamento Central",
                "status": ServiceOrderStatus.ASSIGNED,
                "created_by": 1,
                "assigned_team": "Equipe Hidráulica A",
                "assigned_at": datetime.utcnow() - timedelta(hours=1),
                "created_at": datetime.utcnow() - timedelta(days=1)
            },
            {
                "protocol_number": "OS-2024-003",
                "title": "Troca de válvula defeituosa",
                "description": "Válvula de controle com defeito no setor norte da cidade.",
                "priority": AlertLevel.MEDIUM,
                "location": "Setor Norte - Válvula 15",
                "status": ServiceOrderStatus.IN_PROGRESS,
                "created_by": 1,
                "assigned_team": "Equipe Elétrica B",
                "assigned_at": datetime.utcnow() - timedelta(hours=3),
                "created_at": datetime.utcnow() - timedelta(days=2)
            },
            {
                "protocol_number": "OS-2024-004",
                "title": "Limpeza do reservatório",
                "description": "Limpeza e desinfecção do reservatório principal.",
                "priority": AlertLevel.LOW,
                "location": "Reservatório Principal - Zona Sul",
                "status": ServiceOrderStatus.COMPLETED,
                "created_by": 1,
                "assigned_team": "Equipe Geral C",
                "assigned_at": datetime.utcnow() - timedelta(days=3),
                "completed_at": datetime.utcnow() - timedelta(hours=6),
                "created_at": datetime.utcnow() - timedelta(days=4)
            }
        ]
        
        for order_data in service_orders_data:
            order = ServiceOrder(**order_data)
            db.add(order)
        
        # Create sample complaints
        complaints_data = [
            {
                "protocol_number": "REC-2024-001",
                "title": "Água com gosto estranho",
                "description": "A água da minha casa está com um gosto estranho há 3 dias. Suspeito de contaminação.",
                "category": "quality_issue",
                "location": "Rua das Flores, 456 - Bairro Novo",
                "citizen_name": "João Silva",
                "citizen_contact": "joao.silva@email.com",
                "status": "pending",
                "created_at": datetime.utcnow() - timedelta(hours=4)
            },
            {
                "protocol_number": "REC-2024-002",
                "title": "Pressão da água muito baixa",
                "description": "A pressão da água está muito baixa no meu bairro. Difícil de tomar banho e lavar louça.",
                "category": "pressure_issue",
                "location": "Avenida Central, 789 - Centro",
                "citizen_name": "Maria Santos",
                "citizen_contact": "maria.santos@email.com",
                "status": "in_progress",
                "created_at": datetime.utcnow() - timedelta(days=1)
            },
            {
                "protocol_number": "REC-2024-003",
                "title": "Vazamento na rua",
                "description": "Há um vazamento de água na rua da minha casa. Já faz 2 dias e ninguém veio verificar.",
                "category": "water_leak",
                "location": "Rua da Paz, 321 - Jardim das Flores",
                "citizen_name": "Pedro Oliveira",
                "citizen_contact": "pedro.oliveira@email.com",
                "status": "resolved",
                "created_at": datetime.utcnow() - timedelta(days=3)
            }
        ]
        
        for complaint_data in complaints_data:
            complaint = Complaint(**complaint_data)
            db.add(complaint)
        
        # Get the completed service order ID
        completed_order = db.query(ServiceOrder).filter(ServiceOrder.protocol_number == "OS-2024-004").first()
        
        if completed_order:
            # Create sample maintenances
            maintenances_data = [
                {
                    "service_order_id": completed_order.id,
                    "title": "Limpeza e desinfecção do reservatório",
                    "description": "Limpeza completa do reservatório principal com produtos específicos para desinfecção.",
                    "team_name": "Equipe Geral C",
                    "location": "Reservatório Principal - Zona Sul",
                    "completion_date": datetime.utcnow() - timedelta(hours=6),
                    "duration_hours": 8.0,
                    "cost": 1500.00,
                    "materials_used": "Produtos de limpeza, desinfetante, equipamentos de segurança",
                    "registered_by": 1
                }
            ]
            
            for maintenance_data in maintenances_data:
                maintenance = Maintenance(**maintenance_data)
                db.add(maintenance)
            
            # Create sample service evaluations
            evaluations_data = [
                {
                    "service_order_id": completed_order.id,
                    "rating": 5,
                    "comment": "Excelente atendimento! A equipe foi muito profissional e resolveu o problema rapidamente.",
                    "evaluator_name": "João Silva",
                    "evaluator_contact": "joao.silva@email.com"
                }
            ]
            
            for evaluation_data in evaluations_data:
                evaluation = ServiceEvaluation(**evaluation_data)
                db.add(evaluation)
        
        db.commit()
        print(f"✅ Created {len(service_orders_data)} service orders")
        print(f"✅ Created {len(complaints_data)} complaints")
        
        if completed_order:
            print(f"✅ Created {len(maintenances_data)} maintenance records")
            print(f"✅ Created {len(evaluations_data)} service evaluations")
        
        print("\n=== SAMPLE DATA SUMMARY ===")
        print("Service Orders:")
        for order in service_orders_data:
            print(f"  - {order['protocol_number']}: {order['title']} ({order['status']})")
        
        print("\nComplaints:")
        for complaint in complaints_data:
            print(f"  - {complaint['protocol_number']}: {complaint['title']} ({complaint['status']})")
            
    except Exception as e:
        print(f"Error populating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_sample_data()
