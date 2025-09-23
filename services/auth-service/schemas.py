from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import sys

# Adiciona os módulos compartilhados ao caminho Python
sys.path.append('/app/shared')
from models import UserRole

class UserBase(BaseModel):
    """
    Schema base para usuários - Campos comuns para criação e resposta
    
    Attributes:
        email: Email único do usuário (validado)
        name: Nome completo do usuário
        role: Role/função do usuário no sistema
    """
    email: EmailStr
    name: str
    role: UserRole

class UserCreate(UserBase):
    """
    Schema para criação de novos usuários
    
    Estende UserBase adicionando o campo senha
    
    Attributes:
        password: Senha em texto plano (será criptografada)
    """
    password: str

class UserLogin(BaseModel):
    """
    Schema para autenticação de usuários
    
    Attributes:
        name: Nome de usuário para login
        password: Senha em texto plano
    """
    name: str
    password: str

class UserUpdate(BaseModel):
    """
    Schema para atualização de dados de usuários
    
    Todos os campos são opcionais para permitir atualizações parciais
    
    Attributes:
        name: Novo nome (opcional)
        email: Novo email (opcional)
        password: Nova senha (opcional)
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    """
    Schema de resposta para dados de usuários
    
    Retorna dados do usuário sem informações sensíveis como senha
    
    Attributes:
        id: ID único do usuário
        is_active: Status ativo/inativo
        created_at: Data de criação
    """
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Permite conversão automática de ORM para Pydantic

class UserInToken(BaseModel):
    """
    Schema para dados de usuário incluídos no token JWT
    
    Contém informações básicas do usuário para evitar consultas desnecessárias
    
    Attributes:
        id: ID único do usuário
        email: Email do usuário
        name: Nome do usuário
        role: Role/função do usuário
        is_active: Status ativo/inativo
        created_at: Data de criação
    """
    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    """
    Schema de resposta para autenticação bem-sucedida
    
    Retorna o token JWT e dados do usuário autenticado
    
    Attributes:
        access_token: Token JWT para autenticação
        token_type: Tipo do token (sempre "bearer")
        user: Dados do usuário autenticado
    """
    access_token: str
    token_type: str
    user: UserInToken
