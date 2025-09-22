"""
Script to seed initial data for the authentication service
"""
from sqlalchemy.orm import Session
from database_models import User, Base
from database import get_database_url, create_database_engine, get_session_local
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import UserRole
from auth import get_password_hash

def create_initial_users():
    """Create initial users for testing"""
    
    # Database setup
    DATABASE_URL = get_database_url("auth")
    engine = create_database_engine(DATABASE_URL)
    SessionLocal = get_session_local(engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Limpa todos os usuários existentes
        db.query(User).delete()
        db.commit()

        # Garante que o usuário Operator sempre existe
        operator_data = {
            "email": "operator@sadae.com",
            "name": "Operator",
            "password": "123",
            "role": UserRole.OPERATOR
        }
        hashed_password = get_password_hash(operator_data["password"])
        user = User(
            email=operator_data["email"],
            name=operator_data["name"],
            hashed_password=hashed_password,
            role=operator_data["role"],
            is_active=True
        )
        db.add(user)
        print("Operator user created.")

        # Demais usuários
        users_data = [
            {
                "email": "operador@sadae.com",
                "name": "João Operador",
                "password": "operador123",
                "role": UserRole.OPERATOR
            },
            {
                "email": "cidadao@email.com",
                "name": "Maria Cidadã",
                "password": "cidadao123",
                "role": UserRole.CITIZEN
            },
            {
                "email": "gestor.crise@sadae.com",
                "name": "Carlos Gestor de Crise",
                "password": "crise123",
                "role": UserRole.CRISIS_MANAGER
            },
            {
                "email": "gestor.manutencao@sadae.com",
                "name": "Ana Gestora de Manutenção",
                "password": "manutencao123",
                "role": UserRole.MAINTENANCE_MANAGER
            },
            {
                "email": "gestor.financeiro@sadae.com",
                "name": "Pedro Gestor Financeiro",
                "password": "financeiro123",
                "role": UserRole.FINANCIAL_MANAGER
            }
        ]
        for user_data in users_data:
            hashed_password = get_password_hash(user_data["password"])
            user = User(
                email=user_data["email"],
                name=user_data["name"],
                hashed_password=hashed_password,
                role=user_data["role"],
                is_active=True
            )
            db.add(user)
        db.commit()
        print(f"Operator e demais usuários criados.")
        # Print login credentials
        print("\n=== LOGIN CREDENTIALS ===")
        print(f"Role: {operator_data['role']}")
        print(f"Name: {operator_data['name']}")
        print(f"Password: {operator_data['password']}")
        print("---")
        for user_data in users_data:
            print(f"Role: {user_data['role']}\nName: {user_data['name']}\nPassword: {user_data['password']}\n---")
            
    except Exception as e:
        print(f"Error creating initial users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_users()
