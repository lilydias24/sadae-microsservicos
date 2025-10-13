"""
Chain of Responsibility - Processamento de Ordens de Serviço
Core Service - Maintenance Module - Sistema SADAE

Implementa cadeia de handlers para rotear e processar ordens de serviço:
1. Classificação por tipo (preventiva, corretiva, emergencial)
2. Avaliação de urgência e prioridade
3. Alocação de equipe adequada
4. Estimativa de recursos
5. Aprovação baseada em regras
"""

import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

# Add shared modules to path
sys.path.insert(0, '/app/shared')

from chain_of_responsibility import Handler, Request, Response, ChainBuilder


class ServiceOrderType(Enum):
    """Tipos de ordem de serviço"""
    PREVENTIVE = "preventive"  # Manutenção preventiva programada
    CORRECTIVE = "corrective"  # Correção de problemas detectados
    EMERGENCY = "emergency"    # Emergências (vazamentos, rupturas)
    INSTALLATION = "installation"  # Novas instalações
    INSPECTION = "inspection"  # Inspeções e vistorias
    METER_READING = "meter_reading"  # Leitura de medidores
    METER_REPLACEMENT = "meter_replacement"  # Troca de medidores
    NETWORK_EXPANSION = "network_expansion"  # Expansão de rede


class ServiceOrderPriority(Enum):
    """Prioridade da ordem de serviço"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class ServiceOrderRequest(Request):
    """
    Solicitação de criação de ordem de serviço.
    """
    
    def __init__(
        self,
        order_type: ServiceOrderType,
        description: str,
        location: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        customer_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        reported_issue: Optional[str] = None,
        affects_water_supply: bool = False,
        affects_multiple_customers: bool = False,
        estimated_affected_customers: int = 0,
        has_safety_risk: bool = False,
        requires_street_closure: bool = False,
        requires_special_equipment: bool = False,
        special_equipment_list: Optional[List[str]] = None,
        photos: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(metadata=metadata)
        self.order_type = order_type
        self.description = description
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.reported_issue = reported_issue
        self.affects_water_supply = affects_water_supply
        self.affects_multiple_customers = affects_multiple_customers
        self.estimated_affected_customers = estimated_affected_customers
        self.has_safety_risk = has_safety_risk
        self.requires_street_closure = requires_street_closure
        self.requires_special_equipment = requires_special_equipment
        self.special_equipment_list = special_equipment_list or []
        self.photos = photos or []
        
        # Dados a serem preenchidos pelos handlers
        self.priority: ServiceOrderPriority = ServiceOrderPriority.MEDIUM
        self.assigned_team: Optional[str] = None
        self.estimated_duration_hours: float = 0
        self.estimated_cost: Decimal = Decimal(0)
        self.required_materials: List[Dict[str, Any]] = []
        self.required_workers: int = 0
        self.max_response_time_hours: float = 24
        self.requires_approval: bool = False
        self.auto_approved: bool = False
        self.processing_notes: List[str] = []


class ServiceOrderResponse(Response):
    """
    Resposta de processamento de ordem de serviço.
    """
    
    def __init__(
        self,
        success: bool,
        order_number: Optional[str] = None,
        priority: Optional[ServiceOrderPriority] = None,
        assigned_team: Optional[str] = None,
        estimated_duration_hours: float = 0,
        estimated_cost: Decimal = Decimal(0),
        max_response_time_hours: float = 24,
        requires_approval: bool = False,
        approved: bool = False,
        message: str = "",
        notes: Optional[List[str]] = None
    ):
        super().__init__(success, data={
            "order_number": order_number,
            "priority": priority.value if priority else None,
            "assigned_team": assigned_team,
            "estimated_duration_hours": estimated_duration_hours,
            "estimated_cost": float(estimated_cost),
            "max_response_time_hours": max_response_time_hours,
            "requires_approval": requires_approval,
            "approved": approved,
            "notes": notes or []
        }, message=message)




class OrderClassificationHandler(Handler[ServiceOrderRequest, ServiceOrderResponse]):
    """
    Handler 1: Classifica a ordem de serviço e define prioridade inicial.
    
    Responsabilidade:
    - Classificar por tipo
    - Definir prioridade baseada em fatores de impacto
    - Identificar emergências
    """
    
    def __init__(self):
        super().__init__("OrderClassificationHandler")
        
        # Prioridades base por tipo
        self.base_priorities = {
            ServiceOrderType.EMERGENCY: ServiceOrderPriority.CRITICAL,
            ServiceOrderType.CORRECTIVE: ServiceOrderPriority.HIGH,
            ServiceOrderType.METER_REPLACEMENT: ServiceOrderPriority.MEDIUM,
            ServiceOrderType.INSPECTION: ServiceOrderPriority.MEDIUM,
            ServiceOrderType.PREVENTIVE: ServiceOrderPriority.LOW,
            ServiceOrderType.INSTALLATION: ServiceOrderPriority.MEDIUM,
            ServiceOrderType.METER_READING: ServiceOrderPriority.LOW,
            ServiceOrderType.NETWORK_EXPANSION: ServiceOrderPriority.MEDIUM
        }
    
    def can_handle(self, request: ServiceOrderRequest) -> bool:
        return True  # Sempre primeiro na cadeia
    
    def process(self, request: ServiceOrderRequest) -> ServiceOrderResponse:
        """Classifica a ordem"""
        
        notes = []
        
        # Define prioridade base
        base_priority = self.base_priorities.get(
            request.order_type, 
            ServiceOrderPriority.MEDIUM
        )
        request.priority = base_priority
        notes.append(f"Tipo: {request.order_type.value} - Prioridade base: {base_priority.name}")
        
        # Ajustes de prioridade baseados em fatores
        priority_value = base_priority.value
        
        # Fator 1: Risco à segurança
        if request.has_safety_risk:
            priority_value = min(priority_value + 2, ServiceOrderPriority.CRITICAL.value)
            notes.append("⚠️ Risco à segurança - prioridade elevada")
        
        # Fator 2: Afeta fornecimento de água
        if request.affects_water_supply:
            priority_value = min(priority_value + 1, ServiceOrderPriority.CRITICAL.value)
            notes.append("💧 Afeta fornecimento de água - prioridade elevada")
        
        # Fator 3: Múltiplos clientes afetados
        if request.affects_multiple_customers:
            if request.estimated_affected_customers > 100:
                priority_value = min(priority_value + 2, ServiceOrderPriority.CRITICAL.value)
                notes.append(f"👥 >100 clientes afetados - prioridade crítica")
            elif request.estimated_affected_customers > 20:
                priority_value = min(priority_value + 1, ServiceOrderPriority.CRITICAL.value)
                notes.append(f"👥 {request.estimated_affected_customers} clientes afetados")
        
        # Fator 4: Requer fechamento de rua
        if request.requires_street_closure:
            priority_value = min(priority_value + 1, ServiceOrderPriority.CRITICAL.value)
            notes.append("🚧 Requer fechamento de rua")
        
        # Atualiza prioridade
        request.priority = ServiceOrderPriority(priority_value)
        
        # Define tempo máximo de resposta baseado na prioridade
        response_times = {
            ServiceOrderPriority.CRITICAL: 2,   # 2 horas
            ServiceOrderPriority.URGENT: 4,     # 4 horas
            ServiceOrderPriority.HIGH: 8,       # 8 horas
            ServiceOrderPriority.MEDIUM: 24,    # 24 horas
            ServiceOrderPriority.LOW: 72        # 72 horas
        }
        request.max_response_time_hours = response_times[request.priority]
        
        notes.append(f"✅ Prioridade final: {request.priority.name}")
        notes.append(f"⏱️ Tempo máximo de resposta: {request.max_response_time_hours}h")
        
        request.processing_notes.extend(notes)
        
        # Passa para próximo handler
        return None


class TeamAllocationHandler(Handler[ServiceOrderRequest, ServiceOrderResponse]):
    """
    Handler 2: Aloca equipe adequada baseada no tipo e complexidade.
    
    Responsabilidade:
    - Selecionar equipe especializada
    - Determinar número de trabalhadores necessários
    - Verificar disponibilidade (em produção)
    """
    
    def __init__(self):
        super().__init__("TeamAllocationHandler")
        
        # Mapeamento tipo -> equipe
        self.team_mapping = {
            ServiceOrderType.EMERGENCY: "Equipe de Emergência",
            ServiceOrderType.CORRECTIVE: "Equipe de Manutenção Corretiva",
            ServiceOrderType.PREVENTIVE: "Equipe de Manutenção Preventiva",
            ServiceOrderType.INSTALLATION: "Equipe de Instalações",
            ServiceOrderType.INSPECTION: "Equipe de Inspeção",
            ServiceOrderType.METER_READING: "Equipe de Leitura",
            ServiceOrderType.METER_REPLACEMENT: "Equipe de Medidores",
            ServiceOrderType.NETWORK_EXPANSION: "Equipe de Obras"
        }
        
        # Número base de trabalhadores por tipo
        self.base_workers = {
            ServiceOrderType.EMERGENCY: 3,
            ServiceOrderType.CORRECTIVE: 2,
            ServiceOrderType.PREVENTIVE: 2,
            ServiceOrderType.INSTALLATION: 3,
            ServiceOrderType.INSPECTION: 1,
            ServiceOrderType.METER_READING: 1,
            ServiceOrderType.METER_REPLACEMENT: 2,
            ServiceOrderType.NETWORK_EXPANSION: 5
        }
    
    def can_handle(self, request: ServiceOrderRequest) -> bool:
        return request.priority is not None
    
    def process(self, request: ServiceOrderRequest) -> ServiceOrderResponse:
        """Aloca equipe"""
        
        notes = []
        
        # Seleciona equipe
        request.assigned_team = self.team_mapping.get(
            request.order_type,
            "Equipe Geral"
        )
        notes.append(f"👷 Equipe alocada: {request.assigned_team}")
        
        # Determina número de trabalhadores
        base_workers = self.base_workers.get(request.order_type, 2)
        
        # Ajustes baseados em fatores
        workers_needed = base_workers
        
        if request.requires_special_equipment:
            workers_needed += 1
            notes.append("🔧 Equipamento especial requerido - +1 trabalhador")
        
        if request.requires_street_closure:
            workers_needed += 1
            notes.append("🚧 Fechamento de rua - +1 trabalhador para sinalização")
        
        if request.estimated_affected_customers > 50:
            workers_needed += 1
            notes.append("👥 Muitos clientes afetados - equipe reforçada")
        
        request.required_workers = workers_needed
        notes.append(f"👥 Trabalhadores necessários: {workers_needed}")
        
        request.processing_notes.extend(notes)
        
        # Passa para próximo handler
        return None


class ResourceEstimationHandler(Handler[ServiceOrderRequest, ServiceOrderResponse]):
    """
    Handler 3: Estima duração, materiais e custo.
    
    Responsabilidade:
    - Estimar tempo de execução
    - Listar materiais necessários
    - Calcular custo estimado
    """
    
    def __init__(self):
        super().__init__("ResourceEstimationHandler")
        
        # Durações base por tipo (em horas)
        self.base_durations = {
            ServiceOrderType.EMERGENCY: 4,
            ServiceOrderType.CORRECTIVE: 3,
            ServiceOrderType.PREVENTIVE: 2,
            ServiceOrderType.INSTALLATION: 6,
            ServiceOrderType.INSPECTION: 1,
            ServiceOrderType.METER_READING: 0.5,
            ServiceOrderType.METER_REPLACEMENT: 2,
            ServiceOrderType.NETWORK_EXPANSION: 40
        }
        
        # Custo médio por hora de trabalho
        self.labor_cost_per_hour = Decimal("50.00")
        
        # Materiais comuns por tipo
        self.common_materials = {
            ServiceOrderType.METER_REPLACEMENT: [
                {"item": "Medidor de água", "quantity": 1, "cost": Decimal("150.00")},
                {"item": "Vedações", "quantity": 2, "cost": Decimal("10.00")}
            ],
            ServiceOrderType.EMERGENCY: [
                {"item": "Tubos PVC", "quantity": 5, "cost": Decimal("25.00")},
                {"item": "Conexões", "quantity": 10, "cost": Decimal("8.00")},
                {"item": "Material de vedação", "quantity": 1, "cost": Decimal("30.00")}
            ],
            ServiceOrderType.CORRECTIVE: [
                {"item": "Material de reparo", "quantity": 1, "cost": Decimal("50.00")}
            ]
        }
    
    def can_handle(self, request: ServiceOrderRequest) -> bool:
        return request.assigned_team is not None
    
    def process(self, request: ServiceOrderRequest) -> ServiceOrderResponse:
        """Estima recursos"""
        
        notes = []
        
        # Estima duração
        base_duration = self.base_durations.get(request.order_type, 3)
        duration = base_duration
        
        # Ajustes na duração
        if request.requires_special_equipment:
            duration *= 1.3
            notes.append("⏱️ Equipamento especial - +30% de tempo")
        
        if request.requires_street_closure:
            duration += 1  # 1h adicional para preparação
            notes.append("⏱️ Fechamento de rua - +1h para setup")
        
        if request.estimated_affected_customers > 50:
            duration *= 1.2
            notes.append("⏱️ Muitos clientes - +20% de tempo para cuidados")
        
        request.estimated_duration_hours = round(duration, 1)
        notes.append(f"⏱️ Duração estimada: {request.estimated_duration_hours}h")
        
        # Lista materiais necessários
        materials = self.common_materials.get(request.order_type, [])
        request.required_materials = materials.copy()
        
        if materials:
            notes.append(f"📦 {len(materials)} tipo(s) de material necessário(s)")
        
        # Calcula custo
        # Custo de mão de obra
        labor_cost = Decimal(str(duration)) * self.labor_cost_per_hour * request.required_workers
        
        # Custo de materiais
        materials_cost = sum(
            m["cost"] * m["quantity"] 
            for m in materials
        )
        
        # Custo de equipamento especial
        equipment_cost = Decimal(0)
        if request.requires_special_equipment:
            equipment_cost = Decimal("200.00") * len(request.special_equipment_list or [])
            if equipment_cost > 0:
                notes.append(f"🔧 Custo de equipamento especial: R$ {equipment_cost:.2f}")
        
        # Custo total
        total_cost = labor_cost + materials_cost + equipment_cost
        request.estimated_cost = total_cost
        
        notes.append(f"💰 Custo estimado: R$ {total_cost:.2f}")
        notes.append(f"   - Mão de obra: R$ {labor_cost:.2f}")
        notes.append(f"   - Materiais: R$ {materials_cost:.2f}")
        if equipment_cost > 0:
            notes.append(f"   - Equipamentos: R$ {equipment_cost:.2f}")
        
        request.processing_notes.extend(notes)
        
        # Passa para próximo handler
        return None


class ApprovalHandler(Handler[ServiceOrderRequest, ServiceOrderResponse]):
    """
    Handler 4: Determina se requer aprovação e se pode auto-aprovar.
    
    Responsabilidade:
    - Verificar se requer aprovação gerencial
    - Auto-aprovar ordens de baixo custo/prioridade
    - Encaminhar para aprovação manual se necessário
    """
    
    def __init__(
        self, 
        auto_approval_limit: Decimal = Decimal("1000.00"),
        critical_auto_approval_limit: Decimal = Decimal("5000.00")
    ):
        super().__init__("ApprovalHandler")
        self.auto_approval_limit = auto_approval_limit
        self.critical_auto_approval_limit = critical_auto_approval_limit
    
    def can_handle(self, request: ServiceOrderRequest) -> bool:
        return request.estimated_cost > 0
    
    def process(self, request: ServiceOrderRequest) -> ServiceOrderResponse:
        """Processa aprovação"""
        
        notes = request.processing_notes.copy()
        
        # Regras de aprovação automática
        auto_approved = False
        requires_approval = False
        
        # Regra 1: Emergências críticas com custo moderado
        if request.priority == ServiceOrderPriority.CRITICAL:
            if request.estimated_cost <= self.critical_auto_approval_limit:
                auto_approved = True
                notes.append(f"✅ Auto-aprovado - Emergência crítica (custo: R$ {request.estimated_cost:.2f})")
            else:
                requires_approval = True
                notes.append(f"⚠️ Requer aprovação - Emergência de alto custo (R$ {request.estimated_cost:.2f})")
        
        # Regra 2: Ordens de baixo custo
        elif request.estimated_cost <= self.auto_approval_limit:
            auto_approved = True
            notes.append(f"✅ Auto-aprovado - Baixo custo (R$ {request.estimated_cost:.2f})")
        
        # Regra 3: Manutenção preventiva programada
        elif request.order_type == ServiceOrderType.PREVENTIVE:
            if request.estimated_cost <= Decimal("2000.00"):
                auto_approved = True
                notes.append("✅ Auto-aprovado - Manutenção preventiva programada")
            else:
                requires_approval = True
                notes.append("⚠️ Requer aprovação - Manutenção preventiva de alto custo")
        
        # Regra 4: Requer equipamento especial caro
        elif request.requires_special_equipment and request.estimated_cost > Decimal("3000.00"):
            requires_approval = True
            notes.append("⚠️ Requer aprovação - Equipamento especial de alto custo")
        
        # Regra 5: Fechamento de rua
        elif request.requires_street_closure:
            requires_approval = True
            notes.append("⚠️ Requer aprovação - Fechamento de via pública")
        
        # Regra 6: Custo alto em geral
        elif request.estimated_cost > Decimal("2000.00"):
            requires_approval = True
            notes.append(f"⚠️ Requer aprovação - Alto custo (R$ {request.estimated_cost:.2f})")
        
        # Regra 7: Padrão - auto aprovar se não se enquadra em nenhuma regra acima
        else:
            auto_approved = True
            notes.append("✅ Auto-aprovado - Dentro dos parâmetros normais")
        
        request.auto_approved = auto_approved
        request.requires_approval = requires_approval
        
        # Gera número da ordem
        import uuid
        order_number = f"OS-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Retorna resposta final
        return ServiceOrderResponse(
            success=True,
            order_number=order_number,
            priority=request.priority,
            assigned_team=request.assigned_team,
            estimated_duration_hours=request.estimated_duration_hours,
            estimated_cost=request.estimated_cost,
            max_response_time_hours=request.max_response_time_hours,
            requires_approval=requires_approval,
            approved=auto_approved,
            message=f"Ordem de serviço {order_number} criada com sucesso",
            notes=notes
        )


# ==================== SPECIALIZED CHAINS ====================

class EmergencyOrderHandler(Handler[ServiceOrderRequest, ServiceOrderResponse]):
    """
    Handler especializado para emergências.
    Bypass de algumas validações para agilizar.
    """
    
    def __init__(self):
        super().__init__("EmergencyOrderHandler")
    
    def can_handle(self, request: ServiceOrderRequest) -> bool:
        # Apenas emergências críticas
        return (request.order_type == ServiceOrderType.EMERGENCY and 
                (request.has_safety_risk or 
                 request.affects_water_supply or 
                 request.estimated_affected_customers > 20))
    
    def process(self, request: ServiceOrderRequest) -> ServiceOrderResponse:
        """Processamento rápido de emergências"""
        
        # Define valores padrão para emergência
        request.priority = ServiceOrderPriority.CRITICAL
        request.assigned_team = "Equipe de Emergência 24h"
        request.estimated_duration_hours = 4
        request.estimated_cost = Decimal("2000.00")  # Custo médio de emergência
        request.required_workers = 3
        request.max_response_time_hours = 1  # 1 hora para emergências
        request.auto_approved = True  # Sempre auto-aprovado
        request.requires_approval = False
        
        import uuid
        order_number = f"EMG-{datetime.now().strftime('%Y%m%d%H%M')}-{str(uuid.uuid4())[:6].upper()}"
        
        notes = [
            "🚨 EMERGÊNCIA - Processamento prioritário",
            f"⚡ Equipe de emergência acionada",
            f"⏱️ Tempo máximo de resposta: 1 hora",
            f"✅ Aprovação automática concedida",
            f"💰 Orçamento estimado: R$ {request.estimated_cost:.2f}"
        ]
        
        if request.has_safety_risk:
            notes.append("⚠️ RISCO À SEGURANÇA - Máxima prioridade")
        
        if request.affects_water_supply:
            notes.append("💧 FORNECIMENTO AFETADO - Restauração urgente")
        
        return ServiceOrderResponse(
            success=True,
            order_number=order_number,
            priority=ServiceOrderPriority.CRITICAL,
            assigned_team=request.assigned_team,
            estimated_duration_hours=request.estimated_duration_hours,
            estimated_cost=request.estimated_cost,
            max_response_time_hours=request.max_response_time_hours,
            requires_approval=False,
            approved=True,
            message=f"🚨 ORDEM DE EMERGÊNCIA {order_number} - EQUIPE ACIONADA",
            notes=notes
        )


# ==================== FACTORY FUNCTIONS ====================

def create_standard_service_order_chain() -> Handler[ServiceOrderRequest, ServiceOrderResponse]:
    """
    Cadeia padrão para processamento de ordens de serviço.
    """
    return ChainBuilder("StandardServiceOrderChain") \
        .add(EmergencyOrderHandler()) \
        .add(OrderClassificationHandler()) \
        .add(TeamAllocationHandler()) \
        .add(ResourceEstimationHandler()) \
        .add(ApprovalHandler()) \
        .build()


def create_fast_track_chain() -> Handler[ServiceOrderRequest, ServiceOrderResponse]:
    """
    Cadeia rápida para ordens simples (leitura, inspeção).
    """
    return ChainBuilder("FastTrackChain") \
        .add(OrderClassificationHandler()) \
        .add(TeamAllocationHandler()) \
        .add(ApprovalHandler(auto_approval_limit=Decimal("5000.00"))) \
        .build()


def create_emergency_only_chain() -> Handler[ServiceOrderRequest, ServiceOrderResponse]:
    """
    Cadeia específica para emergências.
    """
    return ChainBuilder("EmergencyOnlyChain") \
        .add(EmergencyOrderHandler()) \
        .build()


# Exemplo de uso
if __name__ == "__main__":
    # Criar cadeia
    service_chain = create_standard_service_order_chain()
    
    # Teste 1: Emergência
    emergency_request = ServiceOrderRequest(
        order_type=ServiceOrderType.EMERGENCY,
        description="Ruptura de tubulação principal",
        location="Rua Principal, 123",
        reported_issue="Água jorrando na rua",
        affects_water_supply=True,
        affects_multiple_customers=True,
        estimated_affected_customers=150,
        has_safety_risk=True,
        requires_street_closure=True
    )
    
    result = service_chain.handle(emergency_request)
    print("=== EMERGÊNCIA ===")
    print(f"Ordem: {result.data['order_number']}")
    print(f"Prioridade: {result.data['priority']}")
    print(f"Equipe: {result.data['assigned_team']}")
    print(f"Aprovado: {result.data['approved']}")
    print("\nNotas:")
    for note in result.data['notes']:
        print(f"  - {note}")
    
    # Teste 2: Manutenção preventiva
    print("\n" + "="*50 + "\n")
    
    preventive_request = ServiceOrderRequest(
        order_type=ServiceOrderType.PREVENTIVE,
        description="Manutenção preventiva de válvulas",
        location="Setor Norte",
        affects_water_supply=False,
        affects_multiple_customers=False
    )
    
    result = service_chain.handle(preventive_request)
    print("=== MANUTENÇÃO PREVENTIVA ===")
    print(f"Ordem: {result.data['order_number']}")
    print(f"Prioridade: {result.data['priority']}")
    print(f"Custo estimado: R$ {result.data['estimated_cost']:.2f}")
    print(f"Duração: {result.data['estimated_duration_hours']}h")
    print(f"Aprovado: {result.data['approved']}")

