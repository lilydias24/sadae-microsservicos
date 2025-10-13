"""
Chain of Responsibility - Validação de Contestações e Negociações
Core Service - Billing Module - Sistema SADAE

Implementa cadeias de handlers para validar e processar:
1. Contestações de faturas (contests)
2. Negociações de dívidas (debt negotiations)

Cada tipo tem sua própria cadeia de validação com múltiplos níveis.
"""

import sys
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

# Add shared modules to path
sys.path.insert(0, '/app/shared')

from chain_of_responsibility import Handler, Request, Response, ChainBuilder


class ContestReason(Enum):
    """Razões para contestação de fatura"""
    HIGH_CONSUMPTION = "high_consumption"
    BILLING_ERROR = "billing_error"
    METER_DEFECT = "meter_defect"
    LEAK_REPORTED = "leak_reported"
    SERVICE_INTERRUPTION = "service_interruption"
    DUPLICATE_CHARGE = "duplicate_charge"
    OTHER = "other"


class ContestRequest(Request):
    """
    Solicitação de contestação de fatura.
    """
    
    def __init__(
        self,
        bill_id: int,
        customer_id: int,
        current_amount: Decimal,
        contested_amount: Decimal,
        reason: ContestReason,
        description: str,
        evidence_files: Optional[List[str]] = None,
        previous_consumption_avg: Optional[Decimal] = None,
        has_leak_report: bool = False,
        has_maintenance_request: bool = False
    ):
        super().__init__()
        self.bill_id = bill_id
        self.customer_id = customer_id
        self.current_amount = Decimal(str(current_amount))
        self.contested_amount = Decimal(str(contested_amount))
        self.reason = reason
        self.description = description
        self.evidence_files = evidence_files or []
        self.previous_consumption_avg = Decimal(str(previous_consumption_avg)) if previous_consumption_avg else None
        self.has_leak_report = has_leak_report
        self.has_maintenance_request = has_maintenance_request
        
        # Dados a serem preenchidos pelos handlers
        self.validation_score: int = 0  # 0-100
        self.auto_approved: bool = False
        self.requires_manual_review: bool = False
        self.suggested_new_amount: Optional[Decimal] = None
        self.validation_notes: List[str] = []


class ContestResponse(Response):
    """
    Resposta de validação de contestação.
    """
    
    def __init__(
        self,
        success: bool,
        approved: bool = False,
        requires_review: bool = False,
        suggested_amount: Optional[Decimal] = None,
        message: str = "",
        validation_score: int = 0,
        notes: Optional[List[str]] = None
    ):
        super().__init__(success, data={
            "approved": approved,
            "requires_review": requires_review,
            "suggested_amount": float(suggested_amount) if suggested_amount else None,
            "validation_score": validation_score,
            "notes": notes or []
        }, message=message)
        self.approved = approved
        self.requires_review = requires_review
        self.suggested_amount = suggested_amount


class NegotiationRequest(Request):
    """
    Solicitação de negociação de dívida.
    """
    
    def __init__(
        self,
        customer_id: int,
        total_debt: Decimal,
        overdue_bills: List[Dict[str, Any]],
        proposed_installments: int,
        proposed_down_payment: Decimal,
        customer_income: Optional[Decimal] = None,
        payment_history_score: int = 50,  # 0-100
        has_active_negotiations: bool = False,
        debt_age_days: int = 0
    ):
        super().__init__()
        self.customer_id = customer_id
        self.total_debt = Decimal(str(total_debt))
        self.overdue_bills = overdue_bills
        self.proposed_installments = proposed_installments
        self.proposed_down_payment = Decimal(str(proposed_down_payment))
        self.customer_income = Decimal(str(customer_income)) if customer_income else None
        self.payment_history_score = payment_history_score
        self.has_active_negotiations = has_active_negotiations
        self.debt_age_days = debt_age_days
        
        # Dados a serem preenchidos
        self.approved: bool = False
        self.max_installments: int = 0
        self.min_down_payment: Decimal = Decimal(0)
        self.interest_rate: Decimal = Decimal(0)
        self.discount_percentage: Decimal = Decimal(0)
        self.validation_notes: List[str] = []


class NegotiationResponse(Response):
    """
    Resposta de validação de negociação.
    """
    
    def __init__(
        self,
        success: bool,
        approved: bool = False,
        max_installments: int = 0,
        min_down_payment: Decimal = Decimal(0),
        interest_rate: Decimal = Decimal(0),
        discount_percentage: Decimal = Decimal(0),
        message: str = "",
        notes: Optional[List[str]] = None
    ):
        super().__init__(success, data={
            "approved": approved,
            "max_installments": max_installments,
            "min_down_payment": float(min_down_payment),
            "interest_rate": float(interest_rate),
            "discount_percentage": float(discount_percentage),
            "notes": notes or []
        }, message=message)
        self.approved = approved


# ==================== CONTEST VALIDATION HANDLERS ====================

class ContestEligibilityHandler(Handler[ContestRequest, ContestResponse]):
    """
    Handler 1: Verifica elegibilidade básica para contestação.
    
    Valida:
    - Fatura não está muito antiga (< 90 dias)
    - Cliente não tem muitas contestações ativas
    - Fatura ainda não foi contestada anteriormente
    """
    
    def __init__(self, max_active_contests: int = 3, max_bill_age_days: int = 90):
        super().__init__("ContestEligibilityHandler")
        self.max_active_contests = max_active_contests
        self.max_bill_age_days = max_bill_age_days
    
    def can_handle(self, request: ContestRequest) -> bool:
        return True  # Sempre o primeiro na cadeia
    
    def process(self, request: ContestRequest) -> ContestResponse:
        """Valida elegibilidade"""
        
        notes = []
        
        # TODO: Em produção, consultar banco de dados
        # Por enquanto, validação básica
        
        # Validação 1: Valor da contestação não pode ser maior que o valor da fatura
        if request.contested_amount > request.current_amount:
            return ContestResponse(
                success=False,
                message="Valor contestado não pode ser maior que o valor da fatura",
                notes=["Valor inválido"]
            )
        
        # Validação 2: Descrição mínima
        if len(request.description.strip()) < 20:
            return ContestResponse(
                success=False,
                message="Descrição da contestação deve ter pelo menos 20 caracteres",
                notes=["Descrição insuficiente"]
            )
        
        # Validação 3: Motivo deve ser válido
        if request.reason not in ContestReason:
            return ContestResponse(
                success=False,
                message="Motivo de contestação inválido",
                notes=["Motivo inválido"]
            )
        
        notes.append("Elegibilidade verificada")
        request.validation_score += 10
        request.validation_notes.extend(notes)
        
        # Passa para próximo handler
        return None


class ContestValueAnalysisHandler(Handler[ContestRequest, ContestResponse]):
    """
    Handler 2: Analisa o valor da contestação.
    
    Valida:
    - Diferença percentual entre valor atual e contestado
    - Comparação com média de consumo histórico
    - Variação aceitável de consumo
    """
    
    def __init__(self):
        super().__init__("ContestValueAnalysisHandler")
        self.max_variation_percent = 50  # 50% de variação aceitável
    
    def can_handle(self, request: ContestRequest) -> bool:
        return request.validation_score >= 10  # Passou pela elegibilidade
    
    def process(self, request: ContestRequest) -> ContestResponse:
        """Analisa valor contestado"""
        
        notes = []
        
        # Calcula diferença percentual
        difference = request.current_amount - request.contested_amount
        difference_percent = (difference / request.current_amount * 100) if request.current_amount > 0 else 0
        
        notes.append(f"Diferença: {difference_percent:.1f}%")
        
        # Análise baseada em consumo histórico
        if request.previous_consumption_avg:
            current_vs_avg = (request.current_amount / request.previous_consumption_avg - 1) * 100
            
            notes.append(f"Variação vs média histórica: {current_vs_avg:.1f}%")
            
            # Se consumo atual é muito maior que a média
            if current_vs_avg > self.max_variation_percent:
                request.validation_score += 20
                notes.append("Consumo anormalmente alto detectado")
                
                # Sugerir valor baseado na média + margem
                suggested = request.previous_consumption_avg * Decimal("1.25")  # 25% acima da média
                request.suggested_new_amount = min(suggested, request.current_amount)
            else:
                request.validation_score += 5
                notes.append("Consumo dentro da variação esperada")
        
        # Se a diferença é pequena (< 10%), pode aprovar automaticamente
        if difference_percent < 10:
            request.validation_score += 15
            notes.append("Diferença pequena, baixo risco")
        elif difference_percent < 30:
            request.validation_score += 10
            notes.append("Diferença moderada")
        else:
            request.validation_score += 5
            notes.append("Diferença significativa, requer análise")
            request.requires_manual_review = True
        
        request.validation_notes.extend(notes)
        
        # Passa para próximo handler
        return None


class ContestEvidenceHandler(Handler[ContestRequest, ContestResponse]):
    """
    Handler 3: Analisa evidências fornecidas.
    
    Valida:
    - Presença de arquivos/fotos
    - Relatórios de vazamento
    - Ordens de manutenção relacionadas
    """
    
    def __init__(self):
        super().__init__("ContestEvidenceHandler")
    
    def can_handle(self, request: ContestRequest) -> bool:
        return request.validation_score >= 15
    
    def process(self, request: ContestRequest) -> ContestResponse:
        """Analisa evidências"""
        
        notes = []
        
        # Verifica arquivos de evidência
        if request.evidence_files and len(request.evidence_files) > 0:
            request.validation_score += 15
            notes.append(f"{len(request.evidence_files)} arquivo(s) de evidência anexado(s)")
        else:
            notes.append("Sem evidências documentais")
        
        # Verifica relatório de vazamento
        if request.has_leak_report:
            request.validation_score += 20
            notes.append("Há relatório de vazamento registrado - forte evidência")
            
            # Vazamento pode justificar desconto significativo
            if request.reason == ContestReason.LEAK_REPORTED:
                request.validation_score += 10
                # Sugerir redução de 40-60% se há vazamento
                request.suggested_new_amount = request.current_amount * Decimal("0.5")
        
        # Verifica ordem de manutenção
        if request.has_maintenance_request:
            request.validation_score += 10
            notes.append("Há ordem de manutenção relacionada")
        
        # Análise por tipo de motivo
        reason_scores = {
            ContestReason.METER_DEFECT: 15,  # Defeito no medidor é grave
            ContestReason.LEAK_REPORTED: 15,  # Vazamento é evidência forte
            ContestReason.BILLING_ERROR: 10,  # Erro de faturamento
            ContestReason.SERVICE_INTERRUPTION: 10,
            ContestReason.DUPLICATE_CHARGE: 20,  # Cobrança duplicada é crítico
            ContestReason.HIGH_CONSUMPTION: 5,  # Menos peso sem evidências
            ContestReason.OTHER: 3
        }
        
        score_bonus = reason_scores.get(request.reason, 0)
        request.validation_score += score_bonus
        notes.append(f"Motivo '{request.reason.value}' adicionou {score_bonus} pontos")
        
        request.validation_notes.extend(notes)
        
        # Passa para próximo handler
        return None


class ContestAutoApprovalHandler(Handler[ContestRequest, ContestResponse]):
    """
    Handler 4: Decide se pode aprovar automaticamente.
    
    Critérios para auto-aprovação:
    - Score alto (>= 70)
    - Valor da contestação baixo (< 30% do valor total)
    - Evidências fortes
    """
    
    def __init__(self, auto_approval_threshold: int = 70):
        super().__init__("ContestAutoApprovalHandler")
        self.threshold = auto_approval_threshold
    
    def can_handle(self, request: ContestRequest) -> bool:
        return request.validation_score > 0
    
    def process(self, request: ContestRequest) -> ContestResponse:
        """Decide aprovação automática"""
        
        notes = request.validation_notes.copy()
        
        # Verifica score
        if request.validation_score >= self.threshold:
            # Auto-aprovar
            notes.append(f"Score {request.validation_score} >= {self.threshold} - Aprovado automaticamente")
            
            # Determina valor aprovado
            approved_amount = request.suggested_new_amount or request.contested_amount
            
            return ContestResponse(
                success=True,
                approved=True,
                requires_review=False,
                suggested_amount=approved_amount,
                message="Contestação aprovada automaticamente",
                validation_score=request.validation_score,
                notes=notes
            )
        
        elif request.validation_score >= 50:
            # Requerer revisão manual
            notes.append(f"Score {request.validation_score} - Requer revisão manual")
            
            return ContestResponse(
                success=True,
                approved=False,
                requires_review=True,
                suggested_amount=request.suggested_new_amount,
                message="Contestação requer análise manual",
                validation_score=request.validation_score,
                notes=notes
            )
        
        else:
            # Rejeitar
            notes.append(f"Score {request.validation_score} muito baixo - Rejeitado")
            
            return ContestResponse(
                success=True,
                approved=False,
                requires_review=False,
                suggested_amount=None,
                message="Contestação rejeitada - evidências insuficientes",
                validation_score=request.validation_score,
                notes=notes
            )


# ==================== NEGOTIATION VALIDATION HANDLERS ====================

class NegotiationEligibilityHandler(Handler[NegotiationRequest, NegotiationResponse]):
    """
    Handler 1: Verifica elegibilidade para negociação.
    
    Valida:
    - Valor mínimo de dívida
    - Não tem negociações ativas
    - Número de parcelas dentro do limite
    """
    
    def __init__(self, min_debt: Decimal = Decimal("100"), max_installments: int = 24):
        super().__init__("NegotiationEligibilityHandler")
        self.min_debt = min_debt
        self.max_installments = max_installments
    
    def can_handle(self, request: NegotiationRequest) -> bool:
        return True
    
    def process(self, request: NegotiationRequest) -> NegotiationResponse:
        """Valida elegibilidade para negociar"""
        
        notes = []
        
        # Validação 1: Valor mínimo
        if request.total_debt < self.min_debt:
            return NegotiationResponse(
                success=False,
                message=f"Valor de dívida muito baixo. Mínimo: R$ {self.min_debt}",
                notes=["Dívida abaixo do mínimo"]
            )
        
        # Validação 2: Negociações ativas
        if request.has_active_negotiations:
            return NegotiationResponse(
                success=False,
                message="Cliente já possui negociação ativa",
                notes=["Negociação duplicada não permitida"]
            )
        
        # Validação 3: Número de parcelas
        if request.proposed_installments > self.max_installments:
            notes.append(f"Parcelas solicitadas ({request.proposed_installments}) excede máximo ({self.max_installments})")
            request.proposed_installments = self.max_installments
        
        notes.append("Elegível para negociação")
        request.validation_notes.extend(notes)
        
        return None


class NegotiationCreditAnalysisHandler(Handler[NegotiationRequest, NegotiationResponse]):
    """
    Handler 2: Análise de crédito e histórico de pagamento.
    
    Determina:
    - Número máximo de parcelas permitido
    - Taxa de juros aplicável
    - Desconto possível
    """
    
    def __init__(self):
        super().__init__("NegotiationCreditAnalysisHandler")
    
    def can_handle(self, request: NegotiationRequest) -> bool:
        return len(request.validation_notes) > 0  # Passou pela elegibilidade
    
    def process(self, request: NegotiationRequest) -> NegotiationResponse:
        """Analisa crédito do cliente"""
        
        notes = []
        
        # Análise baseada no score de histórico de pagamento (0-100)
        score = request.payment_history_score
        
        # Determina máximo de parcelas baseado no score
        if score >= 80:
            request.max_installments = 24
            request.interest_rate = Decimal("0.5")  # 0.5% ao mês
            request.discount_percentage = Decimal("15")  # 15% de desconto à vista
            notes.append("Excelente histórico - condições premium")
        elif score >= 60:
            request.max_installments = 18
            request.interest_rate = Decimal("1.0")
            request.discount_percentage = Decimal("10")
            notes.append("Bom histórico - condições padrão")
        elif score >= 40:
            request.max_installments = 12
            request.interest_rate = Decimal("1.5")
            request.discount_percentage = Decimal("5")
            notes.append("Histórico regular - condições reduzidas")
        else:
            request.max_installments = 6
            request.interest_rate = Decimal("2.0")
            request.discount_percentage = Decimal("0")
            notes.append("Histórico fraco - condições mínimas")
        
        # Ajuste baseado na idade da dívida
        if request.debt_age_days > 180:  # Mais de 6 meses
            # Dívidas antigas podem ter mais desconto para recuperação
            request.discount_percentage += Decimal("5")
            notes.append("Dívida antiga - desconto adicional de 5%")
        
        # Análise de capacidade de pagamento (se informado)
        if request.customer_income:
            # Parcela não deve exceder 30% da renda
            max_installment_value = request.customer_income * Decimal("0.3")
            min_installments = int((request.total_debt / max_installment_value).to_integral_value())
            
            if min_installments > request.max_installments:
                notes.append(f"Renda insuficiente - mínimo {min_installments} parcelas necessário")
                request.max_installments = min(min_installments, 36)  # Máximo absoluto de 36
        
        request.validation_notes.extend(notes)
        
        return None


class NegotiationDownPaymentHandler(Handler[NegotiationRequest, NegotiationResponse]):
    """
    Handler 3: Valida e calcula entrada mínima.
    
    Define:
    - Percentual mínimo de entrada
    - Valida se entrada proposta é suficiente
    """
    
    def __init__(self, min_down_payment_percent: Decimal = Decimal("10")):
        super().__init__("NegotiationDownPaymentHandler")
        self.min_percent = min_down_payment_percent
    
    def can_handle(self, request: NegotiationRequest) -> bool:
        return request.max_installments > 0
    
    def process(self, request: NegotiationRequest) -> NegotiationResponse:
        """Valida entrada"""
        
        notes = []
        
        # Calcula entrada mínima
        min_down = request.total_debt * (self.min_percent / Decimal("100"))
        request.min_down_payment = min_down
        
        # Valida entrada proposta
        if request.proposed_down_payment < min_down:
            notes.append(f"Entrada proposta (R$ {request.proposed_down_payment}) abaixo do mínimo (R$ {min_down})")
            
            return NegotiationResponse(
                success=False,
                message=f"Entrada mínima requerida: R$ {min_down:.2f}",
                notes=notes + request.validation_notes
            )
        
        # Entrada OK
        notes.append(f"Entrada de R$ {request.proposed_down_payment} aprovada (mínimo: R$ {min_down})")
        
        # Se entrada é alta (>30%), pode dar desconto adicional
        down_percent = (request.proposed_down_payment / request.total_debt) * Decimal("100")
        if down_percent > 30:
            bonus_discount = Decimal("5")
            request.discount_percentage += bonus_discount
            notes.append(f"Entrada alta ({down_percent:.1f}%) - desconto adicional de {bonus_discount}%")
        
        request.validation_notes.extend(notes)
        
        return None


class NegotiationApprovalHandler(Handler[NegotiationRequest, NegotiationResponse]):
    """
    Handler 4: Aprovação final da negociação.
    
    Consolida todas as análises e retorna os termos da negociação.
    """
    
    def __init__(self):
        super().__init__("NegotiationApprovalHandler")
    
    def can_handle(self, request: NegotiationRequest) -> bool:
        return request.min_down_payment > 0
    
    def process(self, request: NegotiationRequest) -> NegotiationResponse:
        """Aprova negociação"""
        
        notes = request.validation_notes.copy()
        
        # Calcula valor final com desconto
        total_with_discount = request.total_debt * (Decimal("100") - request.discount_percentage) / Decimal("100")
        
        notes.append(f"✅ Negociação aprovada!")
        notes.append(f"Total original: R$ {request.total_debt:.2f}")
        notes.append(f"Desconto: {request.discount_percentage}%")
        notes.append(f"Total com desconto: R$ {total_with_discount:.2f}")
        notes.append(f"Entrada: R$ {request.proposed_down_payment:.2f}")
        notes.append(f"Saldo: R$ {total_with_discount - request.proposed_down_payment:.2f}")
        notes.append(f"Parcelas: até {request.max_installments}x")
        notes.append(f"Taxa de juros: {request.interest_rate}% a.m.")
        
        return NegotiationResponse(
            success=True,
            approved=True,
            max_installments=request.max_installments,
            min_down_payment=request.min_down_payment,
            interest_rate=request.interest_rate,
            discount_percentage=request.discount_percentage,
            message="Negociação aprovada com sucesso",
            notes=notes
        )


# ==================== FACTORY FUNCTIONS ====================

def create_contest_validation_chain() -> Handler[ContestRequest, ContestResponse]:
    """
    Cria cadeia completa de validação de contestações.
    """
    return ChainBuilder("ContestValidationChain") \
        .add(ContestEligibilityHandler()) \
        .add(ContestValueAnalysisHandler()) \
        .add(ContestEvidenceHandler()) \
        .add(ContestAutoApprovalHandler()) \
        .build()


def create_negotiation_validation_chain() -> Handler[NegotiationRequest, NegotiationResponse]:
    """
    Cria cadeia completa de validação de negociações.
    """
    return ChainBuilder("NegotiationValidationChain") \
        .add(NegotiationEligibilityHandler()) \
        .add(NegotiationCreditAnalysisHandler()) \
        .add(NegotiationDownPaymentHandler()) \
        .add(NegotiationApprovalHandler()) \
        .build()


# Exemplo de uso
if __name__ == "__main__":
    # Teste de contestação
    contest_chain = create_contest_validation_chain()
    
    contest_req = ContestRequest(
        bill_id=123,
        customer_id=456,
        current_amount=Decimal("500.00"),
        contested_amount=Decimal("200.00"),
        reason=ContestReason.LEAK_REPORTED,
        description="Houve vazamento no encanamento, consumo anormalmente alto",
        evidence_files=["foto1.jpg", "foto2.jpg"],
        previous_consumption_avg=Decimal("150.00"),
        has_leak_report=True
    )
    
    result = contest_chain.handle(contest_req)
    print(f"Contestação: {result.message}")
    print(f"Aprovado: {result.approved}")
    print(f"Score: {result.data['validation_score']}")
    
    # Teste de negociação
    negotiation_chain = create_negotiation_validation_chain()
    
    neg_req = NegotiationRequest(
        customer_id=456,
        total_debt=Decimal("1500.00"),
        overdue_bills=[{"id": 1, "amount": 500}, {"id": 2, "amount": 1000}],
        proposed_installments=12,
        proposed_down_payment=Decimal("300.00"),
        payment_history_score=75,
        debt_age_days=120
    )
    
    result = negotiation_chain.handle(neg_req)
    print(f"\nNegociação: {result.message}")
    print(f"Aprovado: {result.approved}")
    print(f"Parcelas: {result.data['max_installments']}")

