from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import sys

# Adiciona os módulos compartilhados ao caminho Python
sys.path.append('/app/shared')
from models import UserRole

# Base class para todos os modelos SQLAlchemy
Base = declarative_base()

class User(Base):
    """
    Modelo de dados para usuários do sistema SADAE
    
    Representa os usuários do sistema com diferentes níveis de acesso:
    - operator: Operadores do sistema
    - maintenance_manager: Gestores de manutenção
    - financial_manager: Gestores financeiros
    - crisis_manager: Gestores de emergência
    - citizen: Cidadãos comuns
    """
    __tablename__ = "users"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True, comment="ID único do usuário")
    
    # Dados de identificação
    email = Column(String, unique=True, index=True, nullable=False, comment="Email único do usuário")
    name = Column(String, nullable=False, comment="Nome completo do usuário")
    
    # Autenticação
    hashed_password = Column(String, nullable=False, comment="Senha criptografada com bcrypt")
    role = Column(String, nullable=False, comment="Role/função do usuário no sistema")
    
    # Status e controle
    is_active = Column(Boolean, default=True, comment="Se o usuário está ativo no sistema")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Data de criação do usuário")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, 
                       comment="Data da última atualização")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
