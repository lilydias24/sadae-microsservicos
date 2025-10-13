import uuid
import os
from datetime import datetime
from typing import Dict, Any
from enum import Enum
import httpx
import logging

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User roles enumeration"""
    CITIZEN = "citizen"
    ADMIN = "admin"
    SUPPORT_AGENT = "support_agent"
    MANAGER = "manager"

def generate_protocol_number() -> str:
    """Generate a unique protocol number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"SADAE-{timestamp}-{unique_id}"

async def make_service_request(
    service_url: str, 
    endpoint: str, 
    method: str = "GET", 
    data: Dict[Any, Any] = None,
    headers: Dict[str, str] = None
) -> Dict[Any, Any]:
    """Make HTTP request to another microservice"""
    url = f"{service_url}{endpoint}"
    
    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

class ServiceRegistry:
    """Service registry for microservices communication"""
    
    def __init__(self):
        core_service_url = os.getenv("CORE_SERVICE_URL", "http://core-service:8002")
        self.services = {
            "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
            "core": core_service_url,
            "monitoring": os.getenv("MONITORING_SERVICE_URL", core_service_url),
            "maintenance": os.getenv("MAINTENANCE_SERVICE_URL", core_service_url),
            "billing": os.getenv("BILLING_SERVICE_URL", core_service_url),
            "crisis": os.getenv("CRISIS_SERVICE_URL", core_service_url),
            "support": os.getenv("SUPPORT_SERVICE_URL", core_service_url),
            "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8007"),
        }
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL by name"""
        url = self.services.get(service_name)

        if url is None and service_name != "core":
            # Fallback to core service for domain-specific modules that reside there
            url = self.services.get("core")

        return url

# Global service registry instance
service_registry = ServiceRegistry()

async def send_notification(service: str, message: str, data: Dict[str, Any] = None):
    """Send notification to a service (simplified implementation)"""
    logger.info(f"Sending notification to {service}: {message}")
    if data:
        logger.info(f"Notification data: {data}")
    
    # In a real implementation, this would send HTTP requests to notification services
    # For now, just log the notification
    return {"status": "sent", "service": service, "message": message}
