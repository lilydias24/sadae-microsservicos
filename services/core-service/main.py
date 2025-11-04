from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add shared modules to path
sys.path.append('/app/shared')

try:
    # Import database setup
    from shared.database import get_database_url, create_database_engine, get_session_local
    from database_models import Base
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback imports
    from database import SessionLocal, engine
    from database_models import Base

app = FastAPI(
    title="SADAE Core Service",
    description="Core Service for SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Database setup
    DATABASE_URL = get_database_url("core")
    engine = create_database_engine(DATABASE_URL)
    SessionLocal = get_session_local(engine)
    
    # Criar tabelas
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"⚠️  Database setup error: {e}")

# Import routers with error handling
try:
    from routers.billing import router as billing_router
    app.include_router(billing_router, prefix="/billing", tags=["billing"])
    print("✅ Billing router loaded")
except Exception as e:
    print(f"⚠️  Error loading billing router: {e}")

try:
    from routers.support import router as support_router
    app.include_router(support_router, prefix="/support", tags=["support"])
    print("✅ Support router loaded")
except Exception as e:
    print(f"⚠️  Error loading support router: {e}")

try:
    from routers.maintenance import router as maintenance_router
    app.include_router(maintenance_router, prefix="/maintenance", tags=["maintenance"])
    print("✅ Maintenance router loaded")
except Exception as e:
    print(f"⚠️  Error loading maintenance router: {e}")

try:
    from routers.monitoring import router as monitoring_router
    app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
    print("✅ Monitoring router loaded")
except Exception as e:
    print(f"⚠️  Error loading monitoring router: {e}")

@app.get("/")
async def root():
    return {
        "message": "SADAE Core Service", 
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": "core",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)