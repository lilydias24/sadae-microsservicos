import uuid
import os
from datetime import datetime
from typing import Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

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
        self.services = {
            "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
            "monitoring": os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8002"),
            "maintenance": os.getenv("MAINTENANCE_SERVICE_URL", "http://maintenance-service:8003"),
            "billing": os.getenv("BILLING_SERVICE_URL", "http://billing-service:8004"),
            "crisis": os.getenv("CRISIS_SERVICE_URL", "http://crisis-service:8005"),
            "support": os.getenv("SUPPORT_SERVICE_URL", "http://support-service:8006"),
            "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8007"),
        }
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL by name"""
        return self.services.get(service_name)

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
