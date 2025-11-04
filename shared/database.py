from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Create the declarative base for all models
Base = declarative_base()

def get_database_url(service_name: str) -> str:
    """Get database URL from environment variables"""
    return os.getenv("DATABASE_URL", f"postgresql://user:password@localhost:5432/{service_name}_db")

def create_database_engine(database_url: str):
    """Create database engine"""
    engine = create_engine(database_url)
    return engine

def get_session_local(engine):
    """Create session local"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

def get_db(SessionLocal):
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session(service_name: str):
    """Get database session for background tasks"""
    database_url = get_database_url(service_name)
    engine = create_database_engine(database_url)
    SessionLocal = get_session_local(engine)
    return SessionLocal()
