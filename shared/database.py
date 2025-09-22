import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_database_url(service_name: str) -> str:
    # Ex: DATABASE_URL_MONITORING ou fallback para SQLite
    env_key = f"DATABASE_URL_{service_name.upper()}"
    url = os.getenv(env_key)
    if url:
        return url
    return f"sqlite:///./{service_name}.db"

def create_database_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, echo=False, future=True, connect_args=connect_args)

def get_session_local(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


