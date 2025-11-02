"""
Sensor data simulator for testing the monitoring service
"""
import asyncio
import random
import httpx
from datetime import datetime, timedelta
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import SensorType

class SensorSimulator:
    """Simulate sensor data for testing"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.sensors = [
            {
                "id": "PRESS_001",
                "name": "Pressure Sensor 1",
                "type": SensorType.PRESSURE,
                "location": "Zona Norte - Reservatório Principal",
                "unit": "bar",
                "base_value": 3.5,
                "variation": 0.5
            },
            {
                "id": "FLOW_001",
                "name": "Flow Sensor 1",
                "type": SensorType.FLOW,
                "location": "Adutora Principal",
                "unit": "L/s",
                "base_value": 150.0,
                "variation": 20.0
            },
            {
                "id": "QUAL_001",
                "name": "Water Quality Sensor 1",
                "type": SensorType.WATER_QUALITY,
                "location": "Estação de Tratamento",
                "unit": "%",
                "base_value": 85.0,
                "variation": 5.0
            },
            {
                "id": "RAIN_001",
                "name": "Rain Gauge 1",
                "type": SensorType.PRECIPITATION,
                "location": "Estação Meteorológica",
                "unit": "mm/h",
                "base_value": 0.0,
                "variation": 2.0
            },
            {
                "id": "RIVER_001",
                "name": "River Level Sensor 1",
                "type": SensorType.RIVER_LEVEL,
                "location": "Rio Principal",
                "unit": "m",
                "base_value": 2.5,
                "variation": 0.3
            }
        ]
        self.running = False
    
    async def create_sensors(self):
        """Create sensors in the system"""
        async with httpx.AsyncClient() as client:
            for sensor in self.sensors:
                try:
                    response = await client.post(
                        f"{self.base_url}/sensors",
                        json={
                            "id": sensor["id"],
                            "name": sensor["name"],
                            "sensor_type": sensor["type"],
                            "location": sensor["location"],
                            "unit": sensor["unit"],
                            "min_threshold": 0.0,
                            "max_threshold": sensor["base_value"] * 2
                        },
                        headers={"Authorization": "Bearer test-token"}
                    )
                    if response.status_code == 200:
                        print(f"Created sensor: {sensor['name']}")
                except Exception as e:
                    print(f"Error creating sensor {sensor['name']}: {e}")

    async def ensure_sensor_exists(self, sensor: dict):
        """Ensure sensor exists; if not, create it."""
        async with httpx.AsyncClient() as client:
            try:
                # Try get
                resp = await client.get(f"{self.base_url}/sensors/{sensor['id']}")
                if resp.status_code == 200:
                    return True
            except Exception:
                pass

            # Create if missing
            try:
                create_resp = await client.post(
                    f"{self.base_url}/sensors",
                    json={
                        "id": sensor["id"],
                        "name": sensor["name"],
                        "sensor_type": sensor["type"],
                        "location": sensor["location"],
                        "unit": sensor["unit"],
                        "min_threshold": 0.0,
                        "max_threshold": sensor["base_value"] * 2
                    },
                    headers={"Authorization": "Bearer test-token"}
                )
                if create_resp.status_code == 200:
                    print(f"Ensured sensor exists: {sensor['name']}")
                    return True
            except Exception as e:
                print(f"Error ensuring sensor {sensor['name']}: {e}")
        return False
    
    async def generate_reading(self, sensor: dict) -> dict:
        """Generate a realistic sensor reading"""
        base_value = sensor["base_value"]
        variation = sensor["variation"]
        
        # Add some randomness
        value = base_value + random.uniform(-variation, variation)
        
        # Special cases for different sensor types
        if sensor["type"] == SensorType.PRECIPITATION:
            # Rain is often 0, with occasional bursts
            if random.random() < 0.8:
                value = 0.0
            else:
                value = random.uniform(0.1, 10.0)
        
        elif sensor["type"] == SensorType.WATER_QUALITY:
            # Water quality should stay within reasonable bounds
            value = max(0, min(100, value))
        
        # Ensure non-negative values for most sensors
        if sensor["type"] != SensorType.PRESSURE:
            value = max(0, value)
        
        return {
            "sensor_id": sensor["id"],
            "sensor_type": sensor["type"],
            "value": round(value, 2),
            "unit": sensor["unit"],
            "location": sensor["location"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def send_reading(self, reading: dict):
        """Send reading to monitoring service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/readings",
                    json=reading
                )
                if response.status_code == 200:
                    print(f"Sent reading: {reading['sensor_id']} = {reading['value']} {reading['unit']}")
                else:
                    # If not found, try to create the sensor then resend once
                    if response.status_code == 404:
                        sensor = next((s for s in self.sensors if s["id"] == reading["sensor_id"]), None)
                        if sensor and await self.ensure_sensor_exists(sensor):
                            retry = await client.post(f"{self.base_url}/readings", json=reading)
                            if retry.status_code == 200:
                                print(f"Sent reading after ensure: {reading['sensor_id']} = {reading['value']} {reading['unit']}")
                                return
                    print(f"Error sending reading: {response.status_code}")
            except Exception as e:
                print(f"Error sending reading: {e}")
    
    async def simulate_anomaly(self, sensor: dict):
        """Simulate an anomalous reading"""
        reading = await self.generate_reading(sensor)
        
        # Make it anomalous
        if sensor["type"] == SensorType.PRESSURE:
            reading["value"] = random.choice([0.1, 15.0])  # Very low or very high
        elif sensor["type"] == SensorType.FLOW:
            reading["value"] = random.uniform(500, 1000)  # Very high flow
        elif sensor["type"] == SensorType.WATER_QUALITY:
            reading["value"] = random.uniform(10, 30)  # Poor quality
        
        await self.send_reading(reading)
        print(f"Sent ANOMALOUS reading: {reading['sensor_id']} = {reading['value']} {reading['unit']}")
    
    async def run_simulation(self, interval: int = 10, anomaly_chance: float = 0.05):
        """Run continuous sensor simulation"""
        self.running = True
        print(f"Starting sensor simulation (interval: {interval}s, anomaly chance: {anomaly_chance})")
        
        while self.running:
            for sensor in self.sensors:
                # Decide if this should be an anomaly
                if random.random() < anomaly_chance:
                    await self.simulate_anomaly(sensor)
                else:
                    reading = await self.generate_reading(sensor)
                    await self.send_reading(reading)
            
            await asyncio.sleep(interval)
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        print("Stopping sensor simulation")

async def main():
    """Main function to run the simulator"""
    simulator = SensorSimulator()
    
    print("Creating sensors...")
    await simulator.create_sensors()
    
    print("Starting simulation...")
    try:
        await simulator.run_simulation(interval=5, anomaly_chance=0.1)
    except KeyboardInterrupt:
        simulator.stop_simulation()
        print("Simulation stopped by user")

if __name__ == "__main__":
    asyncio.run(main())


