from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import Base, Team
import sys
import os

sys.path.append('/app/shared')
from database import get_database_url

# Database setup
DATABASE_URL = get_database_url("maintenance")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def seed_teams():
    db = SessionLocal()
    try:
        # Check if teams already exist
        existing_teams = db.query(Team).count()
        if existing_teams > 0:
            print("Teams already exist, skipping seed.")
            return

        # Create initial teams
        teams = [
            Team(
                name="Equipe A",
                description="Equipe de manutenção geral",
                specialization="general",
                members_count=3,
                is_active=True
            ),
            Team(
                name="Equipe B",
                description="Equipe especializada em encanamento",
                specialization="plumbing",
                members_count=4,
                is_active=True
            ),
            Team(
                name="Equipe C",
                description="Equipe especializada em elétrica",
                specialization="electrical",
                members_count=3,
                is_active=True
            )
        ]

        for team in teams:
            db.add(team)
        
        db.commit()
        print(f"Added {len(teams)} teams successfully!")

    except Exception as e:
        print(f"Error seeding teams: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_teams()