from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
import sys

# Adiciona os módulos compartilhados ao caminho Python
sys.path.append('/app/shared')
from models import ServiceOrderStatus, AlertLevel

class ServiceOrderBase(BaseModel):
    """
    Schema base para ordens de serviço - Campos comuns
    
    Attributes:
        title: Título resumido da ordem de serviço
        description: Descrição detalhada do problema
        priority: Nível de prioridade (LOW, MEDIUM, HIGH, CRITICAL)
        location: Localização onde o serviço deve ser executado
        anomaly_id: ID da anomalia que originou a ordem (opcional)
    """
    title: str
    description: str
    priority: AlertLevel
    location: str
    anomaly_id: Optional[int] = None

class ServiceOrderCreate(ServiceOrderBase):
    """
    Schema para criação de novas ordens de serviço
    
    Herda todos os campos de ServiceOrderBase sem campos adicionais.
    Usado nos endpoints de criação de ordens.
    """
    pass

class ServiceOrderUpdate(BaseModel):
    """
    Schema para atualização de ordens de serviço existentes
    
    Todos os campos são opcionais para permitir atualizações parciais.
    
    Attributes:
        title: Novo título (opcional)
        description: Nova descrição (opcional)
        priority: Nova prioridade (opcional)
        location: Nova localização (opcional)
        status: Novo status (opcional)
        assigned_team: Nova equipe responsável (opcional)
    """
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[AlertLevel] = None
    location: Optional[str] = None
    status: Optional[ServiceOrderStatus] = None
    assigned_team: Optional[str] = None

class ServiceOrderResponse(ServiceOrderBase):
    """
    Schema de resposta para ordens de serviço
    
    Inclui todos os dados da ordem incluindo campos de controle
    e timestamps para rastreamento completo.
    
    Attributes:
        id: ID único da ordem
        protocol_number: Número de protocolo para rastreamento
        status: Status atual da ordem
        created_by: ID do usuário que criou a ordem
        assigned_team: Equipe responsável (se atribuída)
        assigned_at: Data de atribuição à equipe
        completed_at: Data de conclusão (se concluída)
        complaint_id: ID da reclamação relacionada (se aplicável)
        created_at: Data de criação
        updated_at: Data da última atualização
    """
    id: int
    protocol_number: str
    status: ServiceOrderStatus
    created_by: int
    assigned_team: Optional[str]
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]
    complaint_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Permite conversão automática de ORM para Pydantic

class MaintenanceBase(BaseModel):
    """
    Schema base para registros de manutenção - Campos comuns
    
    Attributes:
        service_order_id: ID da ordem de serviço relacionada (opcional)
        title: Título da manutenção executada
        description: Descrição detalhada do trabalho realizado
        team_name: Nome da equipe que executou a manutenção
        location: Local onde a manutenção foi realizada
        completion_date: Data e hora de conclusão
        duration_hours: Duração em horas (opcional)
        cost: Custo total da manutenção (opcional)
        materials_used: Materiais utilizados (opcional)
    """
    service_order_id: Optional[int] = None
    title: str
    description: str
    team_name: str
    location: str
    completion_date: datetime
    duration_hours: Optional[float] = None
    cost: Optional[float] = None
    materials_used: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    """
    Schema para criação de novos registros de manutenção
    
    Herda todos os campos de MaintenanceBase.
    Usado nos endpoints de registro de manutenções executadas.
    """
    pass

class MaintenanceResponse(MaintenanceBase):
    """
    Schema de resposta para registros de manutenção
    
    Inclui dados de controle e auditoria além dos campos básicos.
    
    Attributes:
        id: ID único do registro de manutenção
        registered_by: ID do usuário que registrou a manutenção
        created_at: Data de criação do registro
    """
    id: int
    registered_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComplaintBase(BaseModel):
    """
    Schema base para reclamações de cidadãos - Campos comuns
    
    Attributes:
        title: Título resumido da reclamação
        description: Descrição detalhada do problema
        category: Categoria da reclamação (falta d'água, esgoto, etc.)
        location: Localização do problema
        citizen_name: Nome do cidadão que fez a reclamação
        citizen_contact: Contato do cidadão (telefone, email)
    """
    title: str
    description: str
    category: str
    location: str
    citizen_name: str
    citizen_contact: str

class ComplaintCreate(ComplaintBase):
    """
    Schema para criação de novas reclamações
    
    Herda todos os campos de ComplaintBase.
    Usado quando cidadãos fazem novas reclamações.
    """
    pass

class ComplaintResponse(ComplaintBase):
    """
    Schema de resposta para reclamações
    
    Inclui dados de controle e rastreamento além dos campos básicos.
    
    Attributes:
        id: ID único da reclamação
        protocol_number: Número de protocolo para rastreamento
        status: Status atual da reclamação
        created_at: Data de criação
        updated_at: Data da última atualização
    """
    id: int
    protocol_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ServiceEvaluationBase(BaseModel):
    """
    Schema base para avaliações de serviços - Campos comuns
    
    Attributes:
        service_order_id: ID da ordem de serviço avaliada
        rating: Nota de 1 a 5 estrelas
        comment: Comentário opcional sobre o serviço
        evaluator_name: Nome de quem fez a avaliação (opcional)
        evaluator_contact: Contato do avaliador (opcional)
    """
    service_order_id: int
    rating: int  # 1-5 estrelas
    comment: Optional[str] = None
    evaluator_name: Optional[str] = None
    evaluator_contact: Optional[str] = None

class ServiceEvaluationCreate(ServiceEvaluationBase):
    """
    Schema para criação de novas avaliações
    
    Usado quando cidadãos avaliam serviços executados.
    """
    pass

class ServiceEvaluationResponse(ServiceEvaluationBase):
    """
    Schema de resposta para avaliações
    
    Inclui ID único e timestamp de criação.
    
    Attributes:
        id: ID único da avaliação
        created_at: Data de criação da avaliação
    """
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TeamBase(BaseModel):
    """
    Schema base para equipes de manutenção - Campos comuns
    
    Attributes:
        name: Nome único da equipe
        description: Descrição das responsabilidades (opcional)
        specialization: Área de especialização (opcional)
        members_count: Número de membros na equipe
    """
    name: str
    description: Optional[str] = None
    specialization: Optional[str] = None
    members_count: int = 0

class TeamCreate(TeamBase):
    """
    Schema para criação de novas equipes
    
    Usado na criação de equipes técnicas de manutenção.
    """
    pass

class TeamResponse(TeamBase):
    """
    Schema de resposta para equipes
    
    Inclui dados de controle e status da equipe.
    
    Attributes:
        id: ID único da equipe
        is_active: Se a equipe está ativa
        created_at: Data de criação
        updated_at: Data da última atualização
    """
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReportFilters(BaseModel):
    """
    Schema para filtros de relatórios de manutenção
    
    Permite filtrar relatórios por período, equipe, localização e tipo de serviço.
    
    Attributes:
        start_date: Data de início do período (opcional)
        end_date: Data de fim do período (opcional)
        team_name: Nome da equipe para filtrar (opcional)
        location: Localização para filtrar (opcional)
        service_type: Tipo de serviço para filtrar (opcional)
    """
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    team_name: Optional[str] = None
    location: Optional[str] = None
    service_type: Optional[str] = None

class MaintenanceReportResponse(BaseModel):
    """
    Schema de resposta para relatórios de manutenção
    
    Contém estatísticas consolidadas e lista de intervenções do período.
    
    Attributes:
        report_id: ID único do relatório gerado
        filters: Filtros aplicados na geração
        summary: Resumo estatístico do relatório
        team_statistics: Estatísticas por equipe
        interventions: Lista de manutenções do período
        generated_at: Data e hora de geração do relatório
        generated_by: Nome do usuário que gerou o relatório
    """
    report_id: str
    filters: ReportFilters
    summary: Dict[str, Any]
    team_statistics: Dict[str, Dict[str, Any]]
    interventions: List[MaintenanceResponse]
    generated_at: datetime
    generated_by: str
