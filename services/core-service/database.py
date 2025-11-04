import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add shared modules to path AFTER local imports
sys.path.append('/app/shared')

from shared.database import get_database_url, create_database_engine
from database_models import Base

# Database setup
DATABASE_URL = get_database_url("core")
engine = create_database_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get database session - NO PARAMETERS!
def get_db():
    """
    Database dependency for FastAPI.
    This function MUST NOT have any parameters other than internal generator state.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Confirm this module loaded correctly
print("✅ Core-service database.py loaded with parameter-free get_db()")