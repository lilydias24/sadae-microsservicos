"""
Chain of Responsibility - Sistema de Notificações Multi-Canal
Sistema SADAE

Implementa cadeia de handlers para enviar notificações através de múltiplos canais:
1. Email
2. SMS
3. Push Notification
4. WhatsApp
5. Webhook

Se um canal falhar, tenta o próximo automaticamente.
"""

import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging

sys.path.append('/app/shared')

from chain_of_responsibility import Handler, Request, Response, ChainBuilder

logger = logging.getLogger(__name__)


class NotificationPriority(Enum):
    """Prioridade da notificação"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Canais de notificação disponíveis"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"
    WEBHOOK = "webhook"


class NotificationRequest(Request):
    """
    Solicitação de envio de notificação.
    """
    
    def __init__(
        self,
        recipient_id: int,
        recipient_name: str,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        recipient_device_token: Optional[str] = None,
        title: str = "",
        message: str = "",
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        preferred_channels: Optional[List[NotificationChannel]] = None,
        fallback_enabled: bool = True,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(metadata=metadata)
        self.recipient_id = recipient_id
        self.recipient_name = recipient_name
        self.recipient_email = recipient_email
        self.recipient_phone = recipient_phone
        self.recipient_device_token = recipient_device_token
        self.title = title
        self.message = message
        self.priority = priority
        self.preferred_channels = preferred_channels or []
        self.fallback_enabled = fallback_enabled
        self.template_name = template_name
        self.template_data = template_data or {}
        self.attachments = attachments or []
        
        # Tracking
        self.attempted_channels: List[str] = []
        self.successful_channel: Optional[str] = None
        self.failed_channels: List[Dict[str, str]] = []


class NotificationResponse(Response):
    """
    Resposta de envio de notificação.
    """
    
    def __init__(
        self,
        success: bool,
        channel_used: Optional[str] = None,
        message: str = "",
        attempted_channels: Optional[List[str]] = None,
        failed_channels: Optional[List[Dict[str, str]]] = None,
        delivery_id: Optional[str] = None
    ):
        super().__init__(success, data={
            "channel_used": channel_used,
            "attempted_channels": attempted_channels or [],
            "failed_channels": failed_channels or [],
            "delivery_id": delivery_id
        }, message=message)
        self.channel_used = channel_used
        self.delivery_id = delivery_id


class BaseNotificationHandler(Handler[NotificationRequest, NotificationResponse]):
    """
    Handler base para notificações.
    Fornece funcionalidades comuns a todos os canais.
    """
    
    def __init__(self, channel: NotificationChannel, enabled: bool = True):
        super().__init__(f"{channel.value.upper()}NotificationHandler")
        self.channel = channel
        self.enabled = enabled
    
    def can_handle(self, request: NotificationRequest) -> bool:
        """
        Verifica se este handler pode processar a notificação.
        """
        if not self.enabled:
            logger.info(f"Canal {self.channel.value} desabilitado")
            return False
        
        # Se há canais preferidos, verifica se este está incluído
        if request.preferred_channels and self.channel not in request.preferred_channels:
            logger.info(f"Canal {self.channel.value} não está nos canais preferidos")
            return False
        
        # Verifica se tem as informações necessárias para este canal
        return self._has_required_info(request)
    
    def _has_required_info(self, request: NotificationRequest) -> bool:
        """
        Verifica se a request tem as informações necessárias para este canal.
        Deve ser implementado pelas subclasses.
        """
        return True
    
    def process(self, request: NotificationRequest) -> NotificationResponse:
        """
        Processa o envio da notificação.
        """
        request.attempted_channels.append(self.channel.value)
        
        try:
            # Renderiza a mensagem usando template se disponível
            rendered_message = self._render_message(request)
            
            # Envia a notificação
            delivery_id = self._send(request, rendered_message)
            
            if delivery_id:
                logger.info(f"✅ Notificação enviada via {self.channel.value} - ID: {delivery_id}")
                request.successful_channel = self.channel.value
                
                return NotificationResponse(
                    success=True,
                    channel_used=self.channel.value,
                    message=f"Notificação enviada com sucesso via {self.channel.value}",
                    attempted_channels=request.attempted_channels,
                    delivery_id=delivery_id
                )
            else:
                raise Exception("Falha ao enviar notificação")
        
        except Exception as e:
            logger.error(f"❌ Erro ao enviar via {self.channel.value}: {str(e)}")
            request.failed_channels.append({
                "channel": self.channel.value,
                "error": str(e)
            })
            
            # Se fallback está habilitado, passa para próximo handler
            if request.fallback_enabled and self._next_handler:
                logger.info(f"Tentando canal alternativo...")
                return None  # Passa para próximo
            else:
                return NotificationResponse(
                    success=False,
                    message=f"Falha ao enviar via {self.channel.value}: {str(e)}",
                    attempted_channels=request.attempted_channels,
                    failed_channels=request.failed_channels
                )
    
    def _render_message(self, request: NotificationRequest) -> str:
        """
        Renderiza a mensagem usando template se disponível.
        """
        if request.template_name and request.template_data:
            # Em produção, usar sistema de templates (Jinja2, etc.)
            # Por enquanto, retorna mensagem simples
            return request.message
        return request.message
    
    def _send(self, request: NotificationRequest, message: str) -> Optional[str]:
        """
        Envia a notificação através do canal específico.
        Deve ser implementado pelas subclasses.
        Retorna delivery_id se sucesso, None se falhar.
        """
        raise NotImplementedError()


class EmailNotificationHandler(BaseNotificationHandler):
    """
    Handler para envio de emails.
    """
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None, enabled: bool = True):
        super().__init__(NotificationChannel.EMAIL, enabled)
        self.smtp_config = smtp_config or {}
    
    def _has_required_info(self, request: NotificationRequest) -> bool:
        """Email requer endereço de email"""
        has_email = bool(request.recipient_email)
        if not has_email:
            logger.debug("Email do destinatário não fornecido")
        return has_email
    
    def _send(self, request: NotificationRequest, message: str) -> Optional[str]:
        """
        Envia email.
        """
        try:
            # Em produção, usar biblioteca de email (smtplib, sendgrid, etc.)
            logger.info(f"📧 Enviando email para {request.recipient_email}")
            logger.info(f"   Assunto: {request.title}")
            logger.info(f"   Mensagem: {message[:100]}...")
            
            # Simula envio bem-sucedido
            delivery_id = f"email_{request.request_id}_{datetime.now().timestamp()}"
            
            # TODO: Implementar envio real
            # import smtplib
            # from email.mime.text import MIMEText
            # msg = MIMEText(message)
            # msg['Subject'] = request.title
            # msg['From'] = self.smtp_config.get('from_email')
            # msg['To'] = request.recipient_email
            # ... enviar via SMTP
            
            return delivery_id
        
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            raise


class SMSNotificationHandler(BaseNotificationHandler):
    """
    Handler para envio de SMS.
    """
    
    def __init__(self, sms_provider_config: Optional[Dict[str, Any]] = None, enabled: bool = True):
        super().__init__(NotificationChannel.SMS, enabled)
        self.provider_config = sms_provider_config or {}
    
    def _has_required_info(self, request: NotificationRequest) -> bool:
        """SMS requer número de telefone"""
        has_phone = bool(request.recipient_phone)
        if not has_phone:
            logger.debug("Telefone do destinatário não fornecido")
        return has_phone
    
    def _send(self, request: NotificationRequest, message: str) -> Optional[str]:
        """
        Envia SMS.
        """
        try:
            logger.info(f"📱 Enviando SMS para {request.recipient_phone}")
            logger.info(f"   Mensagem: {message[:100]}...")
            
            # Limita mensagem a 160 caracteres (padrão SMS)
            sms_message = message[:160]
            if len(message) > 160:
                sms_message = message[:157] + "..."
            
            # Simula envio bem-sucedido
            delivery_id = f"sms_{request.request_id}_{datetime.now().timestamp()}"
            
            # TODO: Implementar envio real via Twilio, AWS SNS, etc.
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     body=sms_message,
            #     from_=self.provider_config.get('from_number'),
            #     to=request.recipient_phone
            # )
            
            return delivery_id
        
        except Exception as e:
            logger.error(f"Erro ao enviar SMS: {e}")
            raise


class PushNotificationHandler(BaseNotificationHandler):
    """
    Handler para envio de push notifications (mobile).
    """
    
    def __init__(self, fcm_config: Optional[Dict[str, Any]] = None, enabled: bool = True):
        super().__init__(NotificationChannel.PUSH, enabled)
        self.fcm_config = fcm_config or {}
    
    def _has_required_info(self, request: NotificationRequest) -> bool:
        """Push requer device token"""
        has_token = bool(request.recipient_device_token)
        if not has_token:
            logger.debug("Device token não fornecido")
        return has_token
    
    def _send(self, request: NotificationRequest, message: str) -> Optional[str]:
        """
        Envia push notification.
        """
        try:
            logger.info(f"🔔 Enviando push notification para device token {request.recipient_device_token[:20]}...")
            logger.info(f"   Título: {request.title}")
            logger.info(f"   Mensagem: {message[:100]}...")
            
            # Simula envio bem-sucedido
            delivery_id = f"push_{request.request_id}_{datetime.now().timestamp()}"
            
            # TODO: Implementar envio real via Firebase Cloud Messaging
            # import firebase_admin
            # from firebase_admin import messaging
            # message = messaging.Message(
            #     notification=messaging.Notification(
            #         title=request.title,
            #         body=message
            #     ),
            #     token=request.recipient_device_token
            # )
            # response = messaging.send(message)
            
            return delivery_id
        
        except Exception as e:
            logger.error(f"Erro ao enviar push: {e}")
            raise


class WhatsAppNotificationHandler(BaseNotificationHandler):
    """
    Handler para envio de mensagens via WhatsApp Business API.
    """
    
    def __init__(self, whatsapp_config: Optional[Dict[str, Any]] = None, enabled: bool = True):
        super().__init__(NotificationChannel.WHATSAPP, enabled)
        self.whatsapp_config = whatsapp_config or {}
    
    def _has_required_info(self, request: NotificationRequest) -> bool:
        """WhatsApp requer número de telefone"""
        has_phone = bool(request.recipient_phone)
        if not has_phone:
            logger.debug("Telefone do destinatário não fornecido")
        return has_phone
    
    def _send(self, request: NotificationRequest, message: str) -> Optional[str]:
        """
        Envia mensagem via WhatsApp.
        """
        try:
            logger.info(f"💬 Enviando WhatsApp para {request.recipient_phone}")
            logger.info(f"   Mensagem: {message[:100]}...")
            
            # Simula envio bem-sucedido
            delivery_id = f"whatsapp_{request.request_id}_{datetime.now().timestamp()}"
            
            # TODO: Implementar envio real via WhatsApp Business API
            # import requests
            # headers = {"Authorization": f"Bearer {self.whatsapp_config.get('token')}"}
            # data = {
            #     "messaging_product": "whatsapp",
            #     "to": request.recipient_phone,
            #     "type": "text",
            #     "text": {"body": message}
            # }
            # response = requests.post(
            #     f"https://graph.facebook.com/v17.0/{phone_number_id}/messages",
            #     headers=headers,
            #     json=data
            # )
            
            return delivery_id
        
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {e}")
            raise


class WebhookNotificationHandler(BaseNotificationHandler):
    """
    Handler para envio via webhook (integrações customizadas).
    """
    
    def __init__(self, webhook_url: Optional[str] = None, enabled: bool = True):
        super().__init__(NotificationChannel.WEBHOOK, enabled)
        self.webhook_url = webhook_url
    
    def _has_required_info(self, request: NotificationRequest) -> bool:
        """Webhook requer URL configurada"""
        return bool(self.webhook_url)
    
    def _send(self, request: NotificationRequest, message: str) -> Optional[str]:
        """
        Envia via webhook.
        """
        try:
            logger.info(f"🔗 Enviando webhook para {self.webhook_url}")
            
            payload = {
                "recipient_id": request.recipient_id,
                "recipient_name": request.recipient_name,
                "title": request.title,
                "message": message,
                "priority": request.priority.value,
                "timestamp": datetime.now().isoformat(),
                "metadata": request.metadata
            }
            
            # Simula envio bem-sucedido
            delivery_id = f"webhook_{request.request_id}_{datetime.now().timestamp()}"
            
            # TODO: Implementar POST real
            # import requests
            # response = requests.post(
            #     self.webhook_url,
            #     json=payload,
            #     timeout=10
            # )
            # response.raise_for_status()
            
            return delivery_id
        
        except Exception as e:
            logger.error(f"Erro ao enviar webhook: {e}")
            raise


# ==================== FACTORY FUNCTIONS ====================

def create_email_first_chain(
    smtp_config: Optional[Dict] = None,
    sms_config: Optional[Dict] = None
) -> Handler[NotificationRequest, NotificationResponse]:
    """
    Cadeia que tenta Email primeiro, depois SMS como fallback.
    """
    return ChainBuilder("EmailFirstChain") \
        .add(EmailNotificationHandler(smtp_config)) \
        .add(SMSNotificationHandler(sms_config)) \
        .build()


def create_priority_based_chain(
    configs: Optional[Dict[str, Any]] = None
) -> Handler[NotificationRequest, NotificationResponse]:
    """
    Cadeia baseada em prioridade:
    - CRITICAL: SMS -> WhatsApp -> Email -> Push
    - HIGH: WhatsApp -> SMS -> Email -> Push
    - MEDIUM/LOW: Email -> Push -> SMS
    """
    configs = configs or {}
    
    # Para este exemplo, criamos cadeia genérica
    # Em produção, escolher ordem baseada na prioridade
    return ChainBuilder("PriorityBasedChain") \
        .add(SMSNotificationHandler(configs.get('sms'))) \
        .add(WhatsAppNotificationHandler(configs.get('whatsapp'))) \
        .add(EmailNotificationHandler(configs.get('email'))) \
        .add(PushNotificationHandler(configs.get('fcm'))) \
        .build()


def create_full_notification_chain(
    configs: Optional[Dict[str, Any]] = None,
    channel_order: Optional[List[NotificationChannel]] = None
) -> Handler[NotificationRequest, NotificationResponse]:
    """
    Cria cadeia completa com todos os canais na ordem especificada.
    """
    configs = configs or {}
    
    # Ordem padrão se não especificada
    if not channel_order:
        channel_order = [
            NotificationChannel.EMAIL,
            NotificationChannel.PUSH,
            NotificationChannel.SMS,
            NotificationChannel.WHATSAPP,
            NotificationChannel.WEBHOOK
        ]
    
    builder = ChainBuilder("FullNotificationChain")
    
    # Mapa de canais para handlers
    handler_map = {
        NotificationChannel.EMAIL: lambda: EmailNotificationHandler(configs.get('email')),
        NotificationChannel.SMS: lambda: SMSNotificationHandler(configs.get('sms')),
        NotificationChannel.PUSH: lambda: PushNotificationHandler(configs.get('fcm')),
        NotificationChannel.WHATSAPP: lambda: WhatsAppNotificationHandler(configs.get('whatsapp')),
        NotificationChannel.WEBHOOK: lambda: WebhookNotificationHandler(configs.get('webhook_url'))
    }
    
    # Adiciona handlers na ordem especificada
    for channel in channel_order:
        if channel in handler_map:
            builder.add(handler_map[channel]())
    
    return builder.build()


# Exemplo de uso
if __name__ == "__main__":
    # Criar cadeia de notificações
    notification_chain = create_full_notification_chain()
    
    # Criar request
    notif_request = NotificationRequest(
        recipient_id=123,
        recipient_name="João Silva",
        recipient_email="joao@example.com",
        recipient_phone="+5511999999999",
        title="Fatura Disponível",
        message="Sua fatura de água no valor de R$ 150,00 está disponível.",
        priority=NotificationPriority.MEDIUM,
        fallback_enabled=True
    )
    
    # Enviar
    result = notification_chain.handle(notif_request)
    
    if result.success:
        print(f"✅ Notificação enviada via {result.channel_used}")
        print(f"Delivery ID: {result.delivery_id}")
    else:
        print(f"❌ Falha ao enviar notificação: {result.message}")
        print(f"Canais tentados: {result.data['attempted_channels']}")

