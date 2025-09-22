import time
import random
from typing import Optional, Dict, Any
import httpx

def generate_protocol_number() -> str:
    return f"PR-{int(time.time())}-{random.randint(1000,9999)}"

class ServiceRegistry:
    def __init__(self):
        # URLs base simplificadas; podem ser lidas de env vars no futuro
        self._services = {
            "auth": "http://localhost:8001",
            "notification": "http://localhost:8003",
        }

    def get_service_url(self, name: str) -> str:
        return self._services.get(name, "http://localhost:8000")

service_registry = ServiceRegistry()

async def make_service_request(base_url: str, path: str, *, method: str = "GET", headers: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None):
    url = f"{base_url}{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.request(method, url, headers=headers, json=data)
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return {"status_code": resp.status_code}


