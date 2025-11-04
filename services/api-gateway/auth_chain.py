"""
Chain of Responsibility - Autenticação e Autorização
API Gateway - Sistema SADAE

Implementa uma cadeia de handlers para validar requisições:
1. Validação de token JWT
2. Verificação de expiração
3. Validação de permissões/roles
4. Verificação de recursos específicos
"""

import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import HTTPException, status

# Add shared modules to path
sys.path.append('/app/shared')

from chain_of_responsibility import Handler, Request, Response, ChainBuilder


class AuthRequest(Request):
    """
    Solicitação de autenticação/autorização.
    Contém todas as informações necessárias para validação.
    """
    
    def __init__(
        self,
        token: str,
        required_role: Optional[str] = None,
        required_permissions: Optional[List[str]] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        method: str = "GET",
        path: str = "/"
    ):
        super().__init__()
        self.token = token
        self.required_role = required_role
        self.required_permissions = required_permissions or []
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.method = method
        self.path = path
        self.user_data: Optional[Dict[str, Any]] = None
        self.validated = False


class AuthResponse(Response):
    """
    Resposta de autenticação.
    Contém informações do usuário autenticado e autorizado.
    """
    
    def __init__(
        self, 
        success: bool, 
        user_data: Optional[Dict[str, Any]] = None,
        message: str = "",
        denied_reason: Optional[str] = None
    ):
        super().__init__(success, data=user_data, message=message)
        self.user_data = user_data
        self.denied_reason = denied_reason


class TokenValidationHandler(Handler[AuthRequest, AuthResponse]):
    """
    Handler 1: Valida a existência e formato do token JWT.
    
    Responsabilidade:
    - Verificar se o token foi fornecido
    - Validar formato básico do token
    - Decodificar o token JWT
    """
    
    def __init__(self):
        super().__init__("TokenValidationHandler")
    
    def can_handle(self, request: AuthRequest) -> bool:
        """Este handler sempre tenta processar primeiro"""
        return True
    
    def process(self, request: AuthRequest) -> AuthResponse:
        """Valida o token JWT"""
        
        # Verifica se token foi fornecido
        if not request.token:
            return AuthResponse(
                success=False,
                message="Token de autenticação não fornecido",
                denied_reason="missing_token"
            )
        
        # Verifica formato básico Bearer token
        if not request.token.startswith("Bearer ") and len(request.token.split('.')) != 3:
            # Se não tem "Bearer " prefix, assume que é o token puro
            token = request.token
        else:
            token = request.token.replace("Bearer ", "")
        
        try:
            # Import verify_token from shared
            from auth import verify_token
            
            # Decodifica e valida o token
            user_data = verify_token(token)
            
            if not user_data:
                return AuthResponse(
                    success=False,
                    message="Token inválido ou expirado",
                    denied_reason="invalid_token"
                )
            
            # Armazena dados do usuário na request para próximos handlers
            request.user_data = user_data
            request.validated = True
            
            # Se não há requisitos adicionais, autoriza
            if not request.required_role and not request.required_permissions:
                return AuthResponse(
                    success=True,
                    user_data=user_data,
                    message="Autenticação bem-sucedida"
                )
            
            # Caso contrário, passa para próximo handler
            return None  # Sinaliza para passar adiante
            
        except Exception as e:
            return AuthResponse(
                success=False,
                message=f"Erro ao validar token: {str(e)}",
                denied_reason="token_validation_error"
            )


class TokenExpirationHandler(Handler[AuthRequest, AuthResponse]):
    """
    Handler 2: Verifica se o token está expirado.
    
    Responsabilidade:
    - Verificar campo 'exp' do token
    - Validar se ainda está dentro do período de validade
    """
    
    def __init__(self):
        super().__init__("TokenExpirationHandler")
    
    def can_handle(self, request: AuthRequest) -> bool:
        """Processa se o token já foi validado"""
        return request.validated and request.user_data is not None
    
    def process(self, request: AuthRequest) -> AuthResponse:
        """Verifica expiração do token"""
        
        user_data = request.user_data
        
        # Verifica se há campo de expiração
        if 'exp' in user_data:
            exp_timestamp = user_data['exp']
            
            # Verifica se expirou
            if datetime.fromtimestamp(exp_timestamp) < datetime.now():
                return AuthResponse(
                    success=False,
                    message="Token expirado",
                    denied_reason="token_expired"
                )
        
        # Token ainda válido, passa adiante se houver mais validações
        if request.required_role or request.required_permissions:
            return None  # Passa para próximo handler
        
        # Sem mais validações, autoriza
        return AuthResponse(
            success=True,
            user_data=user_data,
            message="Token válido"
        )


class RoleValidationHandler(Handler[AuthRequest, AuthResponse]):
    """
    Handler 3: Valida se o usuário tem o role necessário.
    
    Responsabilidade:
    - Verificar se usuário possui o role/papel requerido
    - Validar hierarquia de roles (admin > manager > operator > citizen)
    """
    
    # Hierarquia de roles (maior número = maior privilégio)
    ROLE_HIERARCHY = {
        "citizen": 1,
        "support_agent": 2,
        "operator": 3,
        "maintenance_manager": 4,
        "financial_manager": 4,
        "crisis_manager": 5,
        "admin": 10
    }
    
    def __init__(self):
        super().__init__("RoleValidationHandler")
    
    def can_handle(self, request: AuthRequest) -> bool:
        """Processa se há role requerido e token está validado"""
        return (request.validated and 
                request.user_data is not None and 
                request.required_role is not None)
    
    def process(self, request: AuthRequest) -> AuthResponse:
        """Valida role do usuário"""
        
        user_data = request.user_data
        user_role = user_data.get('role', 'citizen')
        required_role = request.required_role
        
        # Obtém níveis hierárquicos
        user_level = self.ROLE_HIERARCHY.get(user_role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)
        
        # Verifica se usuário tem privilégio suficiente
        if user_level < required_level:
            return AuthResponse(
                success=False,
                message=f"Acesso negado. Role '{required_role}' requerido, usuário tem '{user_role}'",
                denied_reason="insufficient_role"
            )
        
        # Role validado, verifica se há mais validações
        if request.required_permissions:
            return None  # Passa para próximo handler
        
        # Sem mais validações, autoriza
        return AuthResponse(
            success=True,
            user_data=user_data,
            message=f"Usuário autorizado com role '{user_role}'"
        )


class PermissionValidationHandler(Handler[AuthRequest, AuthResponse]):
    """
    Handler 4: Valida permissões específicas do usuário.
    
    Responsabilidade:
    - Verificar se usuário possui permissões específicas
    - Validar permissões granulares (read, write, delete, etc.)
    """
    
    def __init__(self):
        super().__init__("PermissionValidationHandler")
    
    def can_handle(self, request: AuthRequest) -> bool:
        """Processa se há permissões requeridas"""
        return (request.validated and 
                request.user_data is not None and 
                request.required_permissions)
    
    def process(self, request: AuthRequest) -> AuthResponse:
        """Valida permissões do usuário"""
        
        user_data = request.user_data
        user_permissions = user_data.get('permissions', [])
        required_permissions = request.required_permissions
        
        # Verifica se usuário tem todas as permissões requeridas
        missing_permissions = [p for p in required_permissions if p not in user_permissions]
        
        if missing_permissions:
            return AuthResponse(
                success=False,
                message=f"Permissões insuficientes. Faltam: {', '.join(missing_permissions)}",
                denied_reason="insufficient_permissions"
            )
        
        # Permissões validadas, verifica se há validação de recursos
        if request.resource_id:
            return None  # Passa para próximo handler
        
        # Sem mais validações, autoriza
        return AuthResponse(
            success=True,
            user_data=user_data,
            message="Permissões validadas"
        )


class ResourceOwnershipHandler(Handler[AuthRequest, AuthResponse]):
    """
    Handler 5: Valida se o usuário tem acesso ao recurso específico.
    
    Responsabilidade:
    - Verificar se usuário é dono do recurso
    - Validar se usuário tem permissão para acessar recurso específico
    - Exemplo: citizen só pode ver suas próprias faturas
    """
    
    def __init__(self):
        super().__init__("ResourceOwnershipHandler")
    
    def can_handle(self, request: AuthRequest) -> bool:
        """Processa se há recurso específico para validar"""
        return (request.validated and 
                request.user_data is not None and 
                request.resource_id is not None)
    
    def process(self, request: AuthRequest) -> AuthResponse:
        """Valida propriedade/acesso ao recurso"""
        
        user_data = request.user_data
        user_id = user_data.get('id') or user_data.get('user_id')
        user_role = user_data.get('role', 'citizen')
        
        # Admins e managers têm acesso a todos os recursos
        if user_role in ['admin', 'crisis_manager', 'financial_manager', 'maintenance_manager']:
            return AuthResponse(
                success=True,
                user_data=user_data,
                message="Acesso autorizado (role privilegiado)"
            )
        
        # Citizens só podem acessar seus próprios recursos
        if user_role == 'citizen':
            resource_owner_id = self._get_resource_owner(
                request.resource_type, 
                request.resource_id
            )
            
            if resource_owner_id and str(resource_owner_id) != str(user_id):
                return AuthResponse(
                    success=False,
                    message="Acesso negado. Você não tem permissão para acessar este recurso",
                    denied_reason="not_resource_owner"
                )
        
        # Autorizado
        return AuthResponse(
            success=True,
            user_data=user_data,
            message="Acesso ao recurso autorizado"
        )
    
    def _get_resource_owner(self, resource_type: Optional[str], resource_id: str) -> Optional[int]:
        """
        Obtém o ID do dono do recurso.
        Em produção, isso consultaria o banco de dados.
        """
        # TODO: Implementar consulta real ao banco de dados
        # Por enquanto, retorna None para não bloquear
        return None


class RateLimitHandler(Handler[AuthRequest, AuthResponse]):
    """
    Handler 6 (Opcional): Verifica rate limiting do usuário.
    
    Responsabilidade:
    - Verificar se usuário excedeu limite de requisições
    - Implementar throttling por IP ou user_id
    """
    
    def __init__(self, max_requests_per_minute: int = 60):
        super().__init__("RateLimitHandler")
        self.max_requests = max_requests_per_minute
        self.request_counts: Dict[str, List[datetime]] = {}
    
    def can_handle(self, request: AuthRequest) -> bool:
        """Sempre verifica rate limit se estiver na cadeia"""
        return request.validated and request.user_data is not None
    
    def process(self, request: AuthRequest) -> AuthResponse:
        """Verifica rate limiting"""
        
        user_data = request.user_data
        user_id = str(user_data.get('id') or user_data.get('user_id', 'anonymous'))
        
        now = datetime.now()
        
        # Limpa requisições antigas (> 1 minuto)
        if user_id in self.request_counts:
            self.request_counts[user_id] = [
                ts for ts in self.request_counts[user_id]
                if (now - ts).total_seconds() < 60
            ]
        else:
            self.request_counts[user_id] = []
        
        # Verifica se excedeu limite
        if len(self.request_counts[user_id]) >= self.max_requests:
            return AuthResponse(
                success=False,
                message="Limite de requisições excedido. Tente novamente em alguns instantes",
                denied_reason="rate_limit_exceeded"
            )
        
        # Adiciona timestamp da requisição atual
        self.request_counts[user_id].append(now)
        
        # Autorizado
        return AuthResponse(
            success=True,
            user_data=user_data,
            message="Rate limit OK"
        )


# Factory functions para criar cadeias pré-configuradas

def create_basic_auth_chain() -> Handler[AuthRequest, AuthResponse]:
    """
    Cria cadeia básica de autenticação (apenas validação de token).
    
    Uso: Endpoints públicos que requerem apenas autenticação.
    """
    return ChainBuilder("BasicAuthChain") \
        .add(TokenValidationHandler()) \
        .add(TokenExpirationHandler()) \
        .build()


def create_role_based_auth_chain() -> Handler[AuthRequest, AuthResponse]:
    """
    Cria cadeia de autenticação com validação de roles.
    
    Uso: Endpoints que requerem roles específicos.
    """
    return ChainBuilder("RoleBasedAuthChain") \
        .add(TokenValidationHandler()) \
        .add(TokenExpirationHandler()) \
        .add(RoleValidationHandler()) \
        .build()


def create_full_auth_chain(enable_rate_limit: bool = False) -> Handler[AuthRequest, AuthResponse]:
    """
    Cria cadeia completa de autenticação com todas as validações.
    
    Uso: Endpoints sensíveis que requerem validação completa.
    """
    builder = ChainBuilder("FullAuthChain") \
        .add(TokenValidationHandler()) \
        .add(TokenExpirationHandler()) \
        .add(RoleValidationHandler()) \
        .add(PermissionValidationHandler()) \
        .add(ResourceOwnershipHandler())
    
    if enable_rate_limit:
        builder.add(RateLimitHandler())
    
    return builder.build()


def create_permission_based_auth_chain() -> Handler[AuthRequest, AuthResponse]:
    """
    Cria cadeia de autenticação baseada em permissões granulares.
    
    Uso: Endpoints com controle fino de permissões.
    """
    return ChainBuilder("PermissionBasedAuthChain") \
        .add(TokenValidationHandler()) \
        .add(TokenExpirationHandler()) \
        .add(PermissionValidationHandler()) \
        .build()


# Exemplo de uso:
if __name__ == "__main__":
    # Criar cadeia completa
    auth_chain = create_full_auth_chain(enable_rate_limit=True)
    
    # Criar requisição
    request = AuthRequest(
        token="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        required_role="operator",
        required_permissions=["billing:read", "billing:write"],
        resource_id="123",
        resource_type="bill"
    )
    
    # Processar
    response = auth_chain.handle(request)
    
    if response.success:
        print(f"✅ Autorizado: {response.message}")
        print(f"User: {response.user_data}")
    else:
        print(f"❌ Negado: {response.message}")
        print(f"Razão: {response.denied_reason}")

