"""
Script to seed initial data for the maintenance service
"""
from sqlalchemy.orm import Session
from database_models import Team, Base
from database import get_database_url, create_database_engine, get_session_local
import sys

# Add shared modules to path
sys.path.append('/app/shared')

def create_initial_teams():
    """Create initial maintenance teams"""
    
    # Database setup
    DATABASE_URL = get_database_url("maintenance")
    engine = create_database_engine(DATABASE_URL)
    SessionLocal = get_session_local(engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if teams already exist
        if db.query(Team).count() > 0:
            print("Teams already exist, skipping seed data creation")
            return
        
        # Create initial teams
        teams_data = [
            {
                "name": "Equipe Hidráulica A",
                "description": "Equipe especializada em reparos hidráulicos e vazamentos",
                "specialization": "hydraulic",
                "members_count": 4
            },
            {
                "name": "Equipe Elétrica B",
                "description": "Equipe especializada em sistemas elétricos e bombas",
                "specialization": "electrical",
                "members_count": 3
            },
            {
                "name": "Equipe Geral C",
                "description": "Equipe para manutenções gerais e emergências",
                "specialization": "general",
                "members_count": 5
            },
            {
                "name": "Equipe Qualidade D",
                "description": "Equipe especializada em qualidade da água e tratamento",
                "specialization": "water_quality",
                "members_count": 2
            }
        ]
        
        for team_data in teams_data:
            team = Team(**team_data)
            db.add(team)
        
        db.commit()
        print(f"Created {len(teams_data)} initial teams")
        
        # Print team information
        print("\n=== MAINTENANCE TEAMS ===")
        for team_data in teams_data:
            print(f"Team: {team_data['name']}")
            print(f"Specialization: {team_data['specialization']}")
            print(f"Members: {team_data['members_count']}")
            print("---")
            
    except Exception as e:
        print(f"Error creating initial teams: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_teams()
