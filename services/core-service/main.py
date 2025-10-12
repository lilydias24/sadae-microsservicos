from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add shared modules to path
sys.path.append('/app/shared')

# Import database setup
from shared.database import get_database_url, create_database_engine, get_session_local
from database_models import Base

app = FastAPI(title="SADAE Core Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = get_database_url("core")
engine = create_database_engine(DATABASE_URL)
SessionLocal = get_session_local(engine)

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Importar todos os routers (precisam ser criados)
from routers.billing import router as billing_router
from routers.support import router as support_router
from routers.maintenance import router as maintenance_router
from routers.monitoring import router as monitoring_router

# Incluir todos os routers
app.include_router(billing_router, prefix="/billing", tags=["billing"])
app.include_router(support_router, prefix="/support", tags=["support"])
app.include_router(maintenance_router, prefix="/maintenance", tags=["maintenance"])
app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])

@app.get("/")
async def root():
    return {"message": "SADAE Core Service", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "core"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)