from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import sys

# Adiciona os módulos compartilhados ao caminho Python
sys.path.append('/app/shared')
from models import ServiceOrderStatus, AlertLevel

# Base class para todos os modelos SQLAlchemy
Base = declarative_base()

class ServiceOrder(Base):
    """
    Modelo de dados para ordens de serviço de manutenção
    
    Representa uma ordem de trabalho criada para solucionar problemas
    no sistema de abastecimento de água e esgoto, podendo ser originada
    por anomalias detectadas automaticamente ou reclamações de cidadãos.
    """
    __tablename__ = "service_orders"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True, comment="ID único da ordem de serviço")
    
    # Identificação e rastreamento
    protocol_number = Column(String, unique=True, nullable=False, comment="Número de protocolo único para rastreamento")
    title = Column(String, nullable=False, comment="Título resumido da ordem de serviço")
    description = Column(Text, nullable=False, comment="Descrição detalhada do problema a ser solucionado")
    
    # Classificação e localização
    priority = Column(String, nullable=False, comment="Nível de prioridade (LOW, MEDIUM, HIGH, CRITICAL)")
    location = Column(String, nullable=False, comment="Localização específica onde o serviço deve ser executado")
    
    # Status e controle de fluxo
    status = Column(String, default=ServiceOrderStatus.OPEN, comment="Status atual da ordem (OPEN, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED)")
    
    # Responsabilidades
    created_by = Column(Integer, nullable=False, comment="ID do usuário que criou a ordem")
    assigned_team = Column(String, comment="Nome da equipe responsável pela execução")
    
    # Controle temporal
    assigned_at = Column(DateTime, comment="Data e hora da atribuição à equipe")
    completed_at = Column(DateTime, comment="Data e hora de conclusão do serviço")
    
    # Referências externas
    anomaly_id = Column(Integer, comment="ID da anomalia no serviço de monitoramento (se aplicável)")
    complaint_id = Column(Integer, comment="ID da reclamação que originou esta ordem (se aplicável)")
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, comment="Data de criação da ordem")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Data da última atualização")

class Maintenance(Base):
    """
    Modelo de dados para registros de manutenção executada
    
    Representa o registro de uma manutenção que foi efetivamente realizada,
    incluindo detalhes sobre duração, custos, materiais utilizados e equipe responsável.
    """
    __tablename__ = "maintenances"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True, comment="ID único do registro de manutenção")
    
    # Relacionamento com ordem de serviço
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), comment="ID da ordem de serviço relacionada")
    
    # Detalhes da manutenção
    title = Column(String, nullable=False, comment="Título da manutenção executada")
    description = Column(Text, nullable=False, comment="Descrição detalhada do trabalho realizado")
    team_name = Column(String, nullable=False, comment="Nome da equipe que executou a manutenção")
    location = Column(String, nullable=False, comment="Local onde a manutenção foi realizada")
    
    # Dados de execução
    completion_date = Column(DateTime, nullable=False, comment="Data e hora de conclusão da manutenção")
    duration_hours = Column(Float, comment="Duração da manutenção em horas")
    cost = Column(Float, comment="Custo total da manutenção (mão de obra + materiais)")
    materials_used = Column(Text, comment="Lista de materiais utilizados na manutenção")
    
    # Controle e auditoria
    registered_by = Column(Integer, nullable=False, comment="ID do usuário que registrou a manutenção")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Data de criação do registro")

class Complaint(Base):
    """
    Modelo de dados para reclamações de cidadãos
    
    Representa uma reclamação feita por um cidadão sobre problemas
    no abastecimento de água, esgoto ou outros serviços públicos relacionados.
    """
    __tablename__ = "complaints"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True, comment="ID único da reclamação")
    
    # Identificação e rastreamento
    protocol_number = Column(String, unique=True, nullable=False, comment="Número de protocolo único para rastreamento")
    title = Column(String, nullable=False, comment="Título resumido da reclamação")
    description = Column(Text, nullable=False, comment="Descrição detalhada do problema reportado")
    
    # Classificação
    category = Column(String, nullable=False, comment="Categoria da reclamação (falta d'água, esgoto entupido, etc.)")
    location = Column(String, nullable=False, comment="Localização do problema reportado")
    
    # Dados do cidadão
    citizen_name = Column(String, nullable=False, comment="Nome do cidadão que fez a reclamação")
    citizen_contact = Column(String, nullable=False, comment="Contato do cidadão (telefone, email)")
    
    # Status e controle
    status = Column(String, default="pending", comment="Status da reclamação (pending, in_analysis, resolved, rejected)")
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, comment="Data de criação da reclamação")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Data da última atualização")

class ServiceEvaluation(Base):
    """
    Modelo de dados para avaliações de serviços executados
    
    Representa a avaliação feita por cidadãos sobre a qualidade
    do atendimento e execução de ordens de serviço.
    """
    __tablename__ = "service_evaluations"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True, comment="ID único da avaliação")
    
    # Relacionamento com ordem de serviço
    service_order_id = Column(Integer, ForeignKey("service_orders.id"), nullable=False, 
                             comment="ID da ordem de serviço avaliada")
    
    # Dados da avaliação
    rating = Column(Integer, nullable=False, comment="Nota de 1 a 5 estrelas para o serviço")
    comment = Column(Text, comment="Comentário opcional sobre o serviço prestado")
    
    # Dados do avaliador
    evaluator_name = Column(String, comment="Nome de quem fez a avaliação")
    evaluator_contact = Column(String, comment="Contato do avaliador")
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, comment="Data de criação da avaliação")

class Team(Base):
    """
    Modelo de dados para equipes de manutenção
    
    Representa uma equipe técnica responsável pela execução
    de ordens de serviço e manutenções no sistema.
    """
    __tablename__ = "teams"
    
    # Chave primária
    id = Column(Integer, primary_key=True, index=True, comment="ID único da equipe")
    
    # Identificação
    name = Column(String, unique=True, nullable=False, comment="Nome único da equipe")
    description = Column(Text, comment="Descrição das responsabilidades da equipe")
    
    # Especialização e capacidade
    specialization = Column(String, comment="Especialização da equipe (hidráulica, elétrica, geral)")
    members_count = Column(Integer, default=0, comment="Número de membros na equipe")
    
    # Status e controle
    is_active = Column(Boolean, default=True, comment="Se a equipe está ativa e disponível")
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, comment="Data de criação da equipe")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, 
                       comment="Data da última atualização")
