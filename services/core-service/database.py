import sys
import os

# Add shared modules to path
sys.path.append('/app/shared')

from shared.database import get_database_url, create_database_engine, get_session_local
from database_models import Base

# Database setup
DATABASE_URL = get_database_url("core")
engine = create_database_engine(DATABASE_URL)
SessionLocal = get_session_local(engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()