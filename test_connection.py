import httpx
import asyncio

async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get('http://monitoring-service:8002/health')
            print(f'Health check - Status: {response.status_code}, Response: {response.text}')
            
            # Test if we can reach the service at all
            response = await client.get('http://monitoring-service:8002/')
            print(f'Root endpoint - Status: {response.status_code}, Response: {response.text}')
            
    except Exception as e:
        print(f'Connection error: {e}')

if __name__ == "__main__":
    asyncio.run(test_connection())
