from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import sys
import os

# Adiciona os módulos compartilhados ao caminho Python
sys.path.append('/app/shared')

from models import UserRole
from database import get_database_url, create_database_engine, get_session_local, get_db
from auth import verify_password, get_password_hash, create_access_token, verify_token

from database_models import User, Base
from schemas import UserCreate, UserLogin, UserResponse, Token, UserUpdate

# Aplicação FastAPI - Serviço de Autenticação e Gestão de Usuários
app = FastAPI(
    title="SADAE Serviço de Autenticação",
    description="Serviço de autenticação e gerenciamento de usuários para SADAE",
    version="1.0.0"
)

# Middleware CORS - Permite requisições de qualquer origem (desenvolvimento)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração do Banco de Dados
DATABASE_URL = get_database_url("auth")  # URL do banco específico para autenticação
engine = create_database_engine(DATABASE_URL)  # Engine SQLAlchemy
SessionLocal = get_session_local(engine)  # Factory de sessões

# Cria as tabelas no banco de dados se não existirem
Base.metadata.create_all(bind=engine)

# Esquema de segurança HTTP Bearer para JWT
security = HTTPBearer()

def get_db_session():
    """
    Obtém uma sessão do banco de dados com gerenciamento automático de recursos
    
    Yields:
        Session: Sessão SQLAlchemy para operações de banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Garante que a conexão seja fechada

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
):
    """
    Obtém o usuário autenticado a partir do token JWT
    
    Args:
        credentials: Credenciais HTTP Bearer com token JWT
        db: Sessão do banco de dados
        
    Returns:
        User: Usuário autenticado e ativo
        
    Raises:
        HTTPException: Se token inválido, usuário não encontrado ou inativo
    """
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )
    
    return user

def require_role(required_roles: list[UserRole]):
    """
    Decorator para exigir roles específicos do usuário
    
    Args:
        required_roles: Lista de roles permitidos para acessar o endpoint
        
    Returns:
        function: Função de validação de role
        
    Raises:
        HTTPException: Se usuário não possui role necessário
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissões insuficientes para esta operação"
            )
        return current_user
    return role_checker

@app.get("/")
async def root():
    """Endpoint raiz - Informações básicas do serviço de autenticação"""
    return {"message": "SADAE Serviço de Autenticação", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Verificação de saúde do serviço - Status operacional"""
    return {"status": "healthy", "service": "auth"}

@app.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db_session)):
    """
    Registra um novo usuário no sistema
    
    Args:
        user_data: Dados do usuário (nome, email, senha, role)
        db: Sessão do banco de dados
        
    Returns:
        UserResponse: Dados do usuário criado (sem senha)
        
    Raises:
        HTTPException: Se email já estiver em uso
    """
    
    # Verifica se o usuário já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já está em uso"
        )
    
    # Cria novo usuário com senha criptografada
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=True  # Usuário ativo por padrão
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db_session)):
    """
    Autentica o usuário e retorna um token JWT
    
    Args:
        user_credentials: Credenciais de login (nome/email e senha)
        db: Sessão do banco de dados
        
    Returns:
        Token: Token JWT de acesso e dados do usuário
        
    Raises:
        HTTPException: Se credenciais inválidas ou usuário inativo
    """
    # Busca usuário por nome
    user = db.query(User).filter(User.name == user_credentials.name).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )
    
    # Cria token JWT com expiração de 24 horas
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
    }

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update current user information"""
    
    if user_update.name is not None:
        current_user.name = user_update.name
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        current_user.email = user_update.email
    
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@app.get("/users", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.CRISIS_MANAGER, UserRole.MAINTENANCE_MANAGER, UserRole.FINANCIAL_MANAGER])),
    db: Session = Depends(get_db_session)
):
    """Get list of users (admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.OPERATOR, UserRole.CRISIS_MANAGER, UserRole.MAINTENANCE_MANAGER, UserRole.FINANCIAL_MANAGER])),
    db: Session = Depends(get_db_session)
):
    """Get user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.put("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.OPERATOR])),
    db: Session = Depends(get_db_session)
):
    """Activate user account (operator only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    db.commit()
    
    return {"message": "User activated successfully"}

@app.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role([UserRole.OPERATOR])),
    db: Session = Depends(get_db_session)
):
    """Deactivate user account (operator only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}

@app.post("/verify-token")
async def verify_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
):
    """Verify JWT token and return user info"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {
        "valid": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_active": user.is_active
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
