import httpx
import asyncio
from datetime import datetime

async def test_readings():
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test reading creation
            reading_data = {
                "sensor_id": "TEST_001",
                "sensor_type": "PRESSURE",
                "value": 3.5,
                "unit": "bar",
                "location": "Test Location",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            print(f"Sending reading: {reading_data}")
            response = await client.post(
                'http://monitoring-service:8002/readings',
                json=reading_data
            )
            print(f'Readings endpoint - Status: {response.status_code}, Response: {response.text}')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_readings())
