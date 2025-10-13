"""
Audit Logger - Sistema de Auditoria para Chain of Responsibility
Sistema SADAE

Registra todas as decisões, processamentos e resultados das cadeias
para fins de auditoria, compliance e análise.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Níveis de auditoria"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditAction(Enum):
    """Tipos de ação auditadas"""
    CONTEST_VALIDATION = "contest_validation"
    NEGOTIATION_VALIDATION = "negotiation_validation"
    SERVICE_ORDER_PROCESSING = "service_order_processing"
    NOTIFICATION_SENT = "notification_sent"
    AUTO_APPROVAL = "auto_approval"
    AUTO_REJECTION = "auto_rejection"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class AuditEntry:
    """
    Entrada de auditoria com todas as informações relevantes.
    """
    
    def __init__(
        self,
        action: AuditAction,
        chain_name: str,
        request_id: str,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        level: AuditLevel = AuditLevel.INFO,
        decision: Optional[str] = None,
        score: Optional[float] = None,
        handler_sequence: Optional[List[str]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.timestamp = datetime.now()
        self.action = action
        self.chain_name = chain_name
        self.request_id = request_id
        self.user_id = user_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.level = level
        self.decision = decision
        self.score = score
        self.handler_sequence = handler_sequence or []
        self.input_data = input_data or {}
        self.output_data = output_data or {}
        self.processing_time_ms = processing_time_ms
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "chain_name": self.chain_name,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "level": self.level.value,
            "decision": self.decision,
            "score": self.score,
            "handler_sequence": self.handler_sequence,
            "input_data": self._sanitize_data(self.input_data),
            "output_data": self._sanitize_data(self.output_data),
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata
        }
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove dados sensíveis antes de logar"""
        if not data:
            return {}
        
        # Lista de campos sensíveis que não devem ser logados
        sensitive_fields = {'password', 'token', 'credit_card', 'ssn', 'cpf'}
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                # Converte Decimals e outros tipos para tipos serializáveis
                try:
                    json.dumps(value)
                    sanitized[key] = value
                except (TypeError, ValueError):
                    sanitized[key] = str(value)
        
        return sanitized
    
    def to_json(self) -> str:
        """Converte para JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class AuditLogger:
    """
    Logger centralizado de auditoria.
    Suporta múltiplos backends: arquivo, banco de dados, serviço externo.
    """
    
    def __init__(
        self,
        log_to_file: bool = True,
        log_to_db: bool = True,
        log_file_path: str = "/var/log/sadae/audit.log",
        db_session_factory=None
    ):
        self.log_to_file = log_to_file
        self.log_to_db = log_to_db
        self.log_file_path = log_file_path
        self.db_session_factory = db_session_factory
        
        # Configurar file logger
        if self.log_to_file:
            self._setup_file_logger()
    
    def _setup_file_logger(self):
        """Configura logger de arquivo"""
        import os
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - AUDIT - %(message)s')
        )
        
        audit_logger = logging.getLogger('audit')
        audit_logger.addHandler(file_handler)
        audit_logger.setLevel(logging.INFO)
    
    def log(self, entry: AuditEntry):
        """
        Registra entrada de auditoria em todos os backends configurados.
        """
        try:
            # Log para arquivo
            if self.log_to_file:
                self._log_to_file(entry)
            
            # Log para banco de dados
            if self.log_to_db and self.db_session_factory:
                self._log_to_database(entry)
            
            # Log console (para desenvolvimento)
            self._log_to_console(entry)
            
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {e}", exc_info=True)
    
    def _log_to_file(self, entry: AuditEntry):
        """Registra em arquivo"""
        audit_logger = logging.getLogger('audit')
        audit_logger.info(entry.to_json())
    
    def _log_to_database(self, entry: AuditEntry):
        """Registra em banco de dados"""
        try:
            from database_models import AuditLog
            
            db = self.db_session_factory()
            
            audit_record = AuditLog(
                timestamp=entry.timestamp,
                action=entry.action.value,
                chain_name=entry.chain_name,
                request_id=entry.request_id,
                user_id=entry.user_id,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                level=entry.level.value,
                decision=entry.decision,
                score=entry.score,
                handler_sequence=json.dumps(entry.handler_sequence),
                input_data=json.dumps(entry.input_data),
                output_data=json.dumps(entry.output_data),
                processing_time_ms=entry.processing_time_ms,
                extra_data=json.dumps(entry.metadata)
            )
            
            db.add(audit_record)
            db.commit()
            
        except ImportError:
            # Modelo não disponível, skip database logging
            pass
        except Exception as e:
            logger.error(f"Erro ao salvar auditoria no banco: {e}")
    
    def _log_to_console(self, entry: AuditEntry):
        """Log para console (desenvolvimento)"""
        icon_map = {
            AuditLevel.INFO: "ℹ️",
            AuditLevel.WARNING: "⚠️",
            AuditLevel.ERROR: "❌",
            AuditLevel.CRITICAL: "🚨"
        }
        
        icon = icon_map.get(entry.level, "📝")
        
        print(f"\n{icon} AUDIT LOG - {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Action: {entry.action.value}")
        print(f"   Chain: {entry.chain_name}")
        print(f"   Decision: {entry.decision}")
        if entry.score is not None:
            print(f"   Score: {entry.score}")
        if entry.handler_sequence:
            print(f"   Handlers: {' → '.join(entry.handler_sequence)}")
        if entry.processing_time_ms:
            print(f"   Processing Time: {entry.processing_time_ms:.2f}ms")


# Instância global do audit logger
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Retorna instância global do audit logger"""
    global _global_audit_logger
    
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger(
            log_to_file=True,
            log_to_db=True,
            log_file_path="/tmp/sadae_audit.log"  # Temp para desenvolvimento
        )
    
    return _global_audit_logger


def set_audit_logger(logger: AuditLogger):
    """Define audit logger customizado"""
    global _global_audit_logger
    _global_audit_logger = logger


# Funções de conveniência para logging rápido

def audit_contest_decision(
    request_id: str,
    user_id: int,
    bill_id: int,
    decision: str,
    score: float,
    handler_sequence: List[str],
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    processing_time_ms: float
):
    """Log de decisão de contestação"""
    entry = AuditEntry(
        action=AuditAction.CONTEST_VALIDATION,
        chain_name="ContestValidationChain",
        request_id=request_id,
        user_id=user_id,
        entity_type="bill_contest",
        entity_id=bill_id,
        level=AuditLevel.INFO,
        decision=decision,
        score=score,
        handler_sequence=handler_sequence,
        input_data=input_data,
        output_data=output_data,
        processing_time_ms=processing_time_ms
    )
    
    get_audit_logger().log(entry)


def audit_negotiation_decision(
    request_id: str,
    user_id: int,
    customer_id: int,
    decision: str,
    handler_sequence: List[str],
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    processing_time_ms: float
):
    """Log de decisão de negociação"""
    entry = AuditEntry(
        action=AuditAction.NEGOTIATION_VALIDATION,
        chain_name="NegotiationValidationChain",
        request_id=request_id,
        user_id=user_id,
        entity_type="debt_negotiation",
        entity_id=customer_id,
        level=AuditLevel.INFO,
        decision=decision,
        handler_sequence=handler_sequence,
        input_data=input_data,
        output_data=output_data,
        processing_time_ms=processing_time_ms
    )
    
    get_audit_logger().log(entry)


def audit_service_order_processing(
    request_id: str,
    user_id: int,
    order_number: str,
    decision: str,
    handler_sequence: List[str],
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    processing_time_ms: float
):
    """Log de processamento de ordem de serviço"""
    entry = AuditEntry(
        action=AuditAction.SERVICE_ORDER_PROCESSING,
        chain_name="ServiceOrderProcessingChain",
        request_id=request_id,
        user_id=user_id,
        entity_type="service_order",
        decision=decision,
        handler_sequence=handler_sequence,
        input_data=input_data,
        output_data=output_data,
        processing_time_ms=processing_time_ms,
        metadata={"order_number": order_number}
    )
    
    get_audit_logger().log(entry)


def audit_auto_approval(
    chain_name: str,
    request_id: str,
    user_id: int,
    entity_type: str,
    entity_id: int,
    reason: str,
    score: Optional[float] = None
):
    """Log de aprovação automática"""
    entry = AuditEntry(
        action=AuditAction.AUTO_APPROVAL,
        chain_name=chain_name,
        request_id=request_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        level=AuditLevel.WARNING,  # Warning para destacar aprovações automáticas
        decision="auto_approved",
        score=score,
        metadata={"reason": reason}
    )
    
    get_audit_logger().log(entry)


def audit_manual_review_required(
    chain_name: str,
    request_id: str,
    user_id: int,
    entity_type: str,
    entity_id: int,
    reason: str,
    score: Optional[float] = None
):
    """Log de requisição de revisão manual"""
    entry = AuditEntry(
        action=AuditAction.MANUAL_REVIEW_REQUIRED,
        chain_name=chain_name,
        request_id=request_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        level=AuditLevel.INFO,
        decision="manual_review_required",
        score=score,
        metadata={"reason": reason}
    )
    
    get_audit_logger().log(entry)

