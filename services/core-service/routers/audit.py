"""
Audit Router - Endpoints para consulta de logs de auditoria
Sistema SADAE

Permite consultar, filtrar e analisar todos os logs de decisões
das cadeias de responsabilidade.
"""

import sys
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

# Add shared modules to path
sys.path.insert(0, '/app/shared')

try:
    from auth import verify_token
    from utils import UserRole
except ImportError:
    class UserRole:
        ADMIN = "admin"
        FINANCIAL_MANAGER = "financial_manager"
        MAINTENANCE_MANAGER = "maintenance_manager"
    
    def verify_token(token):
        return {"id": 1, "role": "admin"}

from database import get_db
from database_models import AuditLog

router = APIRouter()
security = HTTPBearer()


async def verify_user_token(authorization: str) -> dict:
    """Verify JWT token and return user info"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    token = authorization.split(" ")[1]
    user = verify_token(token)  # ✅ Não é async
    return user


def require_admin_or_manager(user: dict):
    """Verifica se usuário é admin, manager ou operador"""
    allowed_roles = [
        UserRole.ADMIN,
        UserRole.OPERATOR,  # ✅ Operadores podem acessar auditoria
        UserRole.FINANCIAL_MANAGER,
        UserRole.MAINTENANCE_MANAGER
    ]
    
    if user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores, gestores e operadores podem acessar logs de auditoria."
        )


@router.get("/logs")
async def get_audit_logs(
    action: Optional[str] = None,
    chain_name: Optional[str] = None,
    user_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    decision: Optional[str] = None,
    level: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    📊 Consultar logs de auditoria
    
    Permite filtrar por múltiplos critérios:
    - action: Tipo de ação (contest_validation, negotiation_validation, etc.)
    - chain_name: Nome da cadeia executada
    - user_id: ID do usuário que iniciou a ação
    - entity_type: Tipo de entidade (bill_contest, debt_negotiation, service_order)
    - entity_id: ID da entidade
    - decision: Decisão tomada (approved, rejected, manual_review)
    - level: Nível do log (info, warning, error, critical)
    - start_date/end_date: Período de tempo
    """
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    require_admin_or_manager(user)
    
    query = db.query(AuditLog)
    
    # Aplicar filtros
    filters = []
    
    if action:
        filters.append(AuditLog.action == action)
    if chain_name:
        filters.append(AuditLog.chain_name == chain_name)
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type)
    if entity_id:
        filters.append(AuditLog.entity_id == entity_id)
    if decision:
        filters.append(AuditLog.decision == decision)
    if level:
        filters.append(AuditLog.level == level)
    if start_date:
        filters.append(AuditLog.timestamp >= start_date)
    if end_date:
        filters.append(AuditLog.timestamp <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Ordenar por timestamp DESC (mais recentes primeiro)
    query = query.order_by(desc(AuditLog.timestamp))
    
    # Paginação
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    # Formatar resposta
    import json
    result_logs = []
    for log in logs:
        result_logs.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "chain_name": log.chain_name,
            "request_id": log.request_id,
            "user_id": log.user_id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "level": log.level,
            "decision": log.decision,
            "score": log.score,
            "handler_sequence": json.loads(log.handler_sequence) if log.handler_sequence else [],
            "input_data": json.loads(log.input_data) if log.input_data else {},
            "output_data": json.loads(log.output_data) if log.output_data else {},
            "processing_time_ms": log.processing_time_ms,
            "metadata": json.loads(log.extra_data) if log.extra_data else {}
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": result_logs
    }


@router.get("/logs/{log_id}")
async def get_audit_log_detail(
    log_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Obter detalhes completos de um log específico"""
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    require_admin_or_manager(user)
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log de auditoria não encontrado"
        )
    
    import json
    return {
        "id": log.id,
        "timestamp": log.timestamp.isoformat(),
        "action": log.action,
        "chain_name": log.chain_name,
        "request_id": log.request_id,
        "user_id": log.user_id,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "level": log.level,
        "decision": log.decision,
        "score": log.score,
        "handler_sequence": json.loads(log.handler_sequence) if log.handler_sequence else [],
        "input_data": json.loads(log.input_data) if log.input_data else {},
        "output_data": json.loads(log.output_data) if log.output_data else {},
        "processing_time_ms": log.processing_time_ms,
        "metadata": json.loads(log.metadata) if log.metadata else {}
    }


@router.get("/stats")
async def get_audit_stats(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
 
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    require_admin_or_manager(user)
    
    query = db.query(AuditLog)
    
    # Filtrar por período se fornecido
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    # Total de logs
    total_logs = query.count()
    
    # Decisões por tipo
    decisions = db.query(
        AuditLog.decision,
        func.count(AuditLog.id).label('count')
    ).filter(AuditLog.decision.isnot(None))
    
    if start_date:
        decisions = decisions.filter(AuditLog.timestamp >= start_date)
    if end_date:
        decisions = decisions.filter(AuditLog.timestamp <= end_date)
    
    decisions = decisions.group_by(AuditLog.decision).all()
    
    # Por chain
    by_chain = db.query(
        AuditLog.chain_name,
        func.count(AuditLog.id).label('count')
    )
    
    if start_date:
        by_chain = by_chain.filter(AuditLog.timestamp >= start_date)
    if end_date:
        by_chain = by_chain.filter(AuditLog.timestamp <= end_date)
    
    by_chain = by_chain.group_by(AuditLog.chain_name).all()
    
    # Por ação
    by_action = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    )
    
    if start_date:
        by_action = by_action.filter(AuditLog.timestamp >= start_date)
    if end_date:
        by_action = by_action.filter(AuditLog.timestamp <= end_date)
    
    by_action = by_action.group_by(AuditLog.action).all()
    
    # Tempo médio de processamento
    avg_processing_time = db.query(
        func.avg(AuditLog.processing_time_ms)
    ).filter(AuditLog.processing_time_ms.isnot(None))
    
    if start_date:
        avg_processing_time = avg_processing_time.filter(AuditLog.timestamp >= start_date)
    if end_date:
        avg_processing_time = avg_processing_time.filter(AuditLog.timestamp <= end_date)
    
    avg_processing_time = avg_processing_time.scalar()
    
    # Score médio
    avg_score = db.query(
        func.avg(AuditLog.score)
    ).filter(AuditLog.score.isnot(None))
    
    if start_date:
        avg_score = avg_score.filter(AuditLog.timestamp >= start_date)
    if end_date:
        avg_score = avg_score.filter(AuditLog.timestamp <= end_date)
    
    avg_score = avg_score.scalar()
    
    # Auto-aprovações
    auto_approvals = query.filter(AuditLog.action == "auto_approval").count()
    manual_reviews = query.filter(AuditLog.action == "manual_review_required").count()
    
    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        "total_logs": total_logs,
        "auto_approvals": auto_approvals,
        "manual_reviews": manual_reviews,
        "auto_approval_rate": (auto_approvals / total_logs * 100) if total_logs > 0 else 0,
        "avg_processing_time_ms": round(avg_processing_time, 2) if avg_processing_time else 0,
        "avg_score": round(avg_score, 2) if avg_score else 0,
        "by_decision": {d.decision: d.count for d in decisions},
        "by_chain": {c.chain_name: c.count for c in by_chain},
        "by_action": {a.action: a.count for a in by_action}
    }


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    🔍 Trilha de auditoria para uma entidade específica
    
    Mostra todo o histórico de decisões relacionadas a uma entidade
    (ex: todos os logs relacionados a uma contestação específica)
    """
    user = await verify_user_token(f"Bearer {credentials.credentials}")
    require_admin_or_manager(user)
    
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(desc(AuditLog.timestamp)).all()
    
    import json
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "chain_name": log.chain_name,
            "decision": log.decision,
            "score": log.score,
            "handler_sequence": json.loads(log.handler_sequence) if log.handler_sequence else [],
            "processing_time_ms": log.processing_time_ms
        })
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total_events": len(result),
        "audit_trail": result
    }

