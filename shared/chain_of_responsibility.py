"""
Chain of Responsibility Pattern - Base Module
Sistema SADAE - Implementação do padrão de design Chain of Responsibility

Permite que múltiplos objetos tenham a chance de processar uma solicitação,
evitando o acoplamento entre remetente e receptor.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, TypeVar, Generic
from enum import Enum
from datetime import datetime
import logging

# Setup logger
logger = logging.getLogger(__name__)

# Generic type for requests
TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


class HandlerResult(Enum):
    """Resultado do processamento do handler"""
    HANDLED = "handled"  # Request foi tratado com sucesso
    PASSED = "passed"    # Request passou para o próximo handler
    REJECTED = "rejected"  # Request foi rejeitado
    ERROR = "error"      # Erro durante processamento


class Request(ABC):
    """
    Classe base para solicitações na cadeia.
    Toda solicitação deve herdar desta classe.
    """
    def __init__(self, request_id: str = None, metadata: Dict[str, Any] = None):
        self.request_id = request_id or self._generate_id()
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.processing_history: List[Dict[str, Any]] = []
    
    @staticmethod
    def _generate_id() -> str:
        """Gera ID único para a requisição"""
        from uuid import uuid4
        return str(uuid4())
    
    def add_to_history(self, handler_name: str, result: HandlerResult, message: str = ""):
        """Adiciona entrada no histórico de processamento"""
        self.processing_history.append({
            "handler": handler_name,
            "result": result.value,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })


class Response:
    """
    Classe base para respostas da cadeia.
    """
    def __init__(
        self, 
        success: bool, 
        data: Any = None, 
        message: str = "", 
        metadata: Dict[str, Any] = None
    ):
        self.success = success
        self.data = data
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte resposta para dicionário"""
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class Handler(ABC, Generic[TRequest, TResponse]):
    """
    Handler abstrato - Define a interface para manipuladores na cadeia.
    
    Cada manipulador concreto deve:
    1. Implementar o método can_handle() para verificar se pode processar
    2. Implementar o método process() para processar a solicitação
    3. Opcionalmente definir seu sucessor na cadeia
    """
    
    def __init__(self, name: str = None):
        self._next_handler: Optional['Handler'] = None
        self.name = name or self.__class__.__name__
        logger.info(f"Handler '{self.name}' inicializado")
    
    def set_next(self, handler: 'Handler') -> 'Handler':
        """
        Define o próximo handler na cadeia.
        Retorna o handler passado para permitir encadeamento fluente.
        
        Exemplo:
            handler1.set_next(handler2).set_next(handler3)
        """
        self._next_handler = handler
        logger.debug(f"Handler '{self.name}' -> próximo: '{handler.name}'")
        return handler
    
    def handle(self, request: TRequest) -> TResponse:
        """
        Processa a solicitação ou a passa para o próximo handler.
        Este é o método principal chamado externamente.
        """
        logger.info(f"Handler '{self.name}' recebeu requisição: {getattr(request, 'request_id', 'N/A')}")
        
        try:
            # Verifica se este handler pode processar a solicitação
            if self.can_handle(request):
                logger.info(f"Handler '{self.name}' pode processar a requisição")
                result = self.process(request)
                
                # Adiciona ao histórico se a request suportar
                if isinstance(request, Request):
                    request.add_to_history(
                        self.name, 
                        HandlerResult.HANDLED, 
                        "Processado com sucesso"
                    )
                
                return result
            else:
                logger.info(f"Handler '{self.name}' não pode processar, passando adiante")
                
                # Adiciona ao histórico
                if isinstance(request, Request):
                    request.add_to_history(
                        self.name, 
                        HandlerResult.PASSED, 
                        "Passado para próximo handler"
                    )
                
                # Passa para o próximo handler, se existir
                if self._next_handler:
                    return self._next_handler.handle(request)
                else:
                    logger.warning(f"Fim da cadeia atingido sem processar a requisição")
                    return self._handle_unprocessed(request)
        
        except Exception as e:
            logger.error(f"Erro no handler '{self.name}': {str(e)}", exc_info=True)
            
            if isinstance(request, Request):
                request.add_to_history(
                    self.name, 
                    HandlerResult.ERROR, 
                    f"Erro: {str(e)}"
                )
            
            return self._handle_error(request, e)
    
    @abstractmethod
    def can_handle(self, request: TRequest) -> bool:
        """
        Verifica se este handler pode processar a solicitação.
        Retorna True se puder processar, False caso contrário.
        """
        pass
    
    @abstractmethod
    def process(self, request: TRequest) -> TResponse:
        """
        Processa a solicitação.
        Este método só é chamado se can_handle() retornar True.
        """
        pass
    
    def _handle_unprocessed(self, request: TRequest) -> TResponse:
        """
        Lida com solicitações que chegaram ao fim da cadeia sem serem processadas.
        Pode ser sobrescrito por subclasses.
        """
        logger.warning(f"Requisição não processada por nenhum handler na cadeia")
        return Response(
            success=False,
            message="Nenhum handler disponível para processar esta solicitação",
            metadata={"unprocessed": True}
        )
    
    def _handle_error(self, request: TRequest, error: Exception) -> TResponse:
        """
        Lida com erros durante o processamento.
        Pode ser sobrescrito por subclasses.
        """
        return Response(
            success=False,
            message=f"Erro durante processamento: {str(error)}",
            metadata={"error_type": error.__class__.__name__}
        )


class ChainBuilder(Generic[TRequest, TResponse]):
    """
    Builder para construir cadeias de handlers de forma fluente.
    
    Exemplo:
        chain = (ChainBuilder()
            .add(Handler1())
            .add(Handler2())
            .add(Handler3())
            .build())
        
        result = chain.handle(request)
    """
    
    def __init__(self, name: str = "unnamed_chain"):
        self.handlers: List[Handler] = []
        self.name = name
        logger.info(f"ChainBuilder '{self.name}' criado")
    
    def add(self, handler: Handler[TRequest, TResponse]) -> 'ChainBuilder':
        """Adiciona um handler à cadeia"""
        self.handlers.append(handler)
        logger.debug(f"Handler '{handler.name}' adicionado à cadeia '{self.name}'")
        return self
    
    def build(self) -> Handler[TRequest, TResponse]:
        """
        Constrói a cadeia linkando todos os handlers.
        Retorna o primeiro handler da cadeia.
        """
        if not self.handlers:
            raise ValueError("Não é possível construir uma cadeia vazia")
        
        # Link handlers
        for i in range(len(self.handlers) - 1):
            self.handlers[i].set_next(self.handlers[i + 1])
        
        logger.info(f"Cadeia '{self.name}' construída com {len(self.handlers)} handlers")
        return self.handlers[0]
    
    def build_with_fallback(self, fallback_handler: Handler[TRequest, TResponse]) -> Handler[TRequest, TResponse]:
        """
        Constrói a cadeia e adiciona um handler de fallback no final.
        """
        chain = self.build()
        self.handlers[-1].set_next(fallback_handler)
        logger.info(f"Fallback handler '{fallback_handler.name}' adicionado à cadeia '{self.name}'")
        return chain


class ConditionalHandler(Handler[TRequest, TResponse]):
    """
    Handler condicional que processa apenas se uma condição for satisfeita.
    Útil para criar handlers inline sem criar novas classes.
    """
    
    def __init__(
        self, 
        name: str,
        condition_fn: callable,
        process_fn: callable
    ):
        super().__init__(name)
        self._condition_fn = condition_fn
        self._process_fn = process_fn
    
    def can_handle(self, request: TRequest) -> bool:
        return self._condition_fn(request)
    
    def process(self, request: TRequest) -> TResponse:
        return self._process_fn(request)


class LoggingHandler(Handler[TRequest, TResponse]):
    """
    Handler decorador que adiciona logging a qualquer handler.
    """
    
    def __init__(self, wrapped_handler: Handler[TRequest, TResponse], verbose: bool = True):
        super().__init__(f"Logging[{wrapped_handler.name}]")
        self.wrapped_handler = wrapped_handler
        self.verbose = verbose
    
    def can_handle(self, request: TRequest) -> bool:
        if self.verbose:
            logger.info(f"Verificando se '{self.wrapped_handler.name}' pode processar...")
        return self.wrapped_handler.can_handle(request)
    
    def process(self, request: TRequest) -> TResponse:
        if self.verbose:
            logger.info(f"'{self.wrapped_handler.name}' processando requisição...")
        
        start_time = datetime.now()
        result = self.wrapped_handler.process(request)
        duration = (datetime.now() - start_time).total_seconds()
        
        if self.verbose:
            logger.info(f"'{self.wrapped_handler.name}' concluído em {duration:.3f}s")
        
        return result


# Utility functions

def create_simple_chain(*handlers: Handler) -> Handler:
    """
    Cria uma cadeia simples a partir de uma lista de handlers.
    
    Exemplo:
        chain = create_simple_chain(handler1, handler2, handler3)
    """
    if not handlers:
        raise ValueError("Pelo menos um handler deve ser fornecido")
    
    for i in range(len(handlers) - 1):
        handlers[i].set_next(handlers[i + 1])
    
    return handlers[0]


def chain_with_logging(*handlers: Handler, verbose: bool = True) -> Handler:
    """
    Cria uma cadeia com logging automático em todos os handlers.
    """
    logged_handlers = [LoggingHandler(h, verbose) for h in handlers]
    return create_simple_chain(*logged_handlers)

