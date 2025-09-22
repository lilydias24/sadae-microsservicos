import httpx
from datetime import datetime

def generate_protocol_number():
    """Generate a unique protocol number for service orders"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"MAN{timestamp}"

# Simple service registry for local development
class ServiceRegistry:
    def __init__(self):
        self.services = {
            "auth": "http://auth-service:8001",
            "maintenance": "http://maintenance-service:8003"
        }

    def get_service_url(self, name):
        return self.services.get(name)

service_registry = ServiceRegistry()

async def make_service_request(base_url, path, method="GET", headers=None, json=None):
    url = f"{base_url}{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()
