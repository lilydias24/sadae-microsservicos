"""
Smart water meter simulator for testing the billing service
"""
import asyncio
import random
import httpx
from datetime import datetime, timedelta
import sys

# Add shared modules to path
sys.path.append('/app/shared')

class MeterSimulator:
    """Simulate smart water meter readings"""
    
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url
        self.meters = [
            {
                "meter_id": "WM001",
                "customer_id": 1,
                "location": "Residência - Rua A, 123",
                "base_consumption": 15.0,  # m³ per month
                "current_reading": 1000.0
            },
            {
                "meter_id": "WM002", 
                "customer_id": 2,
                "location": "Comércio - Av. B, 456",
                "base_consumption": 45.0,
                "current_reading": 2500.0
            },
            {
                "meter_id": "WM003",
                "customer_id": 3,
                "location": "Residência - Rua C, 789",
                "base_consumption": 12.0,
                "current_reading": 800.0
            }
        ]
        self.running = False
    
    async def create_meters(self):
        """Create water meters in the system"""
        async with httpx.AsyncClient() as client:
            for meter in self.meters:
                try:
                    response = await client.post(
                        f"{self.base_url}/meters",
                        json={
                            "meter_id": meter["meter_id"],
                            "customer_id": meter["customer_id"],
                            "location": meter["location"],
                            "installation_date": "2023-01-01T00:00:00"
                        },
                        headers={"Authorization": "Bearer test-token"}
                    )
                    if response.status_code == 200:
                        print(f"Created meter: {meter['meter_id']}")
                except Exception as e:
                    print(f"Error creating meter {meter['meter_id']}: {e}")
    
    async def generate_reading(self, meter: dict) -> dict:
        """Generate a realistic meter reading"""
        # Daily consumption (monthly consumption / 30)
        daily_consumption = meter["base_consumption"] / 30
        
        # Add some randomness (±20%)
        variation = random.uniform(0.8, 1.2)
        actual_consumption = daily_consumption * variation
        
        # Update current reading
        meter["current_reading"] += actual_consumption
        
        return {
            "meter_id": meter["meter_id"],
            "reading_value": round(meter["current_reading"], 2),
            "reading_date": datetime.utcnow().isoformat()
        }
    
    async def send_reading(self, reading: dict):
        """Send reading to billing service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/readings",
                    json=reading
                )
                if response.status_code == 200:
                    print(f"Sent reading: {reading['meter_id']} = {reading['reading_value']} m³")
                else:
                    print(f"Error sending reading: {response.status_code}")
            except Exception as e:
                print(f"Error sending reading: {e}")
    
    async def simulate_monthly_readings(self):
        """Simulate a month of daily readings"""
        print("Simulating monthly readings...")
        
        for day in range(30):
            print(f"Day {day + 1}/30")
            
            for meter in self.meters:
                reading = await self.generate_reading(meter)
                await self.send_reading(reading)
            
            # Wait a bit between days (speed up simulation)
            await asyncio.sleep(1)
        
        print("Monthly simulation completed!")
    
    async def run_continuous_simulation(self, interval: int = 3600):
        """Run continuous meter readings (hourly by default)"""
        self.running = True
        print(f"Starting continuous meter simulation (interval: {interval}s)")
        
        while self.running:
            for meter in self.meters:
                # Generate hourly reading (1/24 of daily consumption)
                hourly_consumption = (meter["base_consumption"] / 30) / 24
                variation = random.uniform(0.5, 1.5)
                meter["current_reading"] += hourly_consumption * variation
                
                reading = {
                    "meter_id": meter["meter_id"],
                    "reading_value": round(meter["current_reading"], 2),
                    "reading_date": datetime.utcnow().isoformat()
                }
                
                await self.send_reading(reading)
            
            await asyncio.sleep(interval)
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        print("Stopping meter simulation")

async def main():
    """Main function to run the simulator"""
    simulator = MeterSimulator()
    
    print("Creating water meters...")
    await simulator.create_meters()
    
    print("\nChoose simulation mode:")
    print("1. Monthly simulation (30 days in ~30 seconds)")
    print("2. Continuous simulation (hourly readings)")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        await simulator.simulate_monthly_readings()
    elif choice == "2":
        try:
            await simulator.run_continuous_simulation(interval=10)  # Every 10 seconds for testing
        except KeyboardInterrupt:
            simulator.stop_simulation()
            print("Simulation stopped by user")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())
