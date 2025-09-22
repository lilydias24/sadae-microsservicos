import asyncio
from typing import Tuple
from datetime import datetime, timedelta
import statistics
import sys

# Add shared modules to path
sys.path.append('/app/shared')
from models import SensorType, AlertLevel

class AnomalyDetector:
    """Anomaly detection system for sensor readings"""
    
    def __init__(self):
        # Default thresholds for different sensor types
        self.default_thresholds = {
            SensorType.PRESSURE: {"min": 0.5, "max": 10.0, "deviation_factor": 2.0},
            SensorType.FLOW: {"min": 0.0, "max": 1000.0, "deviation_factor": 2.5},
            SensorType.WATER_QUALITY: {"min": 0.0, "max": 100.0, "deviation_factor": 1.5},
            SensorType.PRECIPITATION: {"min": 0.0, "max": 200.0, "deviation_factor": 3.0},
            SensorType.RIVER_LEVEL: {"min": 0.0, "max": 50.0, "deviation_factor": 2.0}
        }
        
        # Cache for historical data analysis
        self.historical_cache = {}
    
    async def detect(self, reading) -> Tuple[bool, AlertLevel]:
        """
        Detect if a sensor reading is anomalous
        Returns: (is_anomaly, severity_level)
        """
        sensor_type = SensorType(reading.sensor_type)
        value = reading.value
        sensor_id = reading.sensor_id
        
        # Get thresholds for this sensor type
        thresholds = self.default_thresholds.get(sensor_type, {})
        
        # Check absolute thresholds
        min_threshold = thresholds.get("min", float('-inf'))
        max_threshold = thresholds.get("max", float('inf'))
        
        if value < min_threshold or value > max_threshold:
            # Determine severity based on how far outside the threshold
            if sensor_type == SensorType.PRESSURE:
                if value < min_threshold * 0.5 or value > max_threshold * 1.5:
                    return True, AlertLevel.CRITICAL
                elif value < min_threshold * 0.8 or value > max_threshold * 1.2:
                    return True, AlertLevel.HIGH
                else:
                    return True, AlertLevel.MEDIUM
            
            elif sensor_type == SensorType.FLOW:
                if value > max_threshold * 1.3:
                    return True, AlertLevel.CRITICAL
                elif value > max_threshold * 1.1:
                    return True, AlertLevel.HIGH
                else:
                    return True, AlertLevel.MEDIUM
            
            elif sensor_type == SensorType.WATER_QUALITY:
                if value < 20 or value > 95:  # Critical water quality issues
                    return True, AlertLevel.CRITICAL
                elif value < 40 or value > 85:
                    return True, AlertLevel.HIGH
                else:
                    return True, AlertLevel.MEDIUM
            
            else:
                return True, AlertLevel.MEDIUM
        
        # Check for statistical anomalies (sudden changes)
        historical_anomaly = await self._check_statistical_anomaly(sensor_id, sensor_type, value)
        if historical_anomaly:
            return True, AlertLevel.MEDIUM
        
        return False, AlertLevel.LOW
    
    async def _check_statistical_anomaly(self, sensor_id: str, sensor_type: SensorType, current_value: float) -> bool:
        """Check for statistical anomalies based on historical data"""
        try:
            # This would typically query the database for recent readings
            # For now, we'll use a simplified approach
            
            # Get recent readings from cache or database
            cache_key = f"{sensor_id}_{sensor_type}"
            if cache_key not in self.historical_cache:
                self.historical_cache[cache_key] = []
            
            recent_readings = self.historical_cache[cache_key]
            
            # Add current reading to cache
            recent_readings.append({
                "value": current_value,
                "timestamp": datetime.utcnow()
            })
            
            # Keep only last 50 readings
            if len(recent_readings) > 50:
                recent_readings = recent_readings[-50:]
                self.historical_cache[cache_key] = recent_readings
            
            # Need at least 10 readings for statistical analysis
            if len(recent_readings) < 10:
                return False
            
            # Calculate statistics
            values = [r["value"] for r in recent_readings[:-1]]  # Exclude current reading
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0
            
            if stdev == 0:
                return False
            
            # Check if current value is more than 2 standard deviations away
            deviation_factor = self.default_thresholds.get(sensor_type, {}).get("deviation_factor", 2.0)
            z_score = abs(current_value - mean) / stdev
            
            return z_score > deviation_factor
            
        except Exception as e:
            print(f"Error in statistical anomaly detection: {e}")
            return False
    
    def get_threshold(self, sensor_id: str, sensor_type: SensorType) -> float:
        """Get threshold value for a sensor"""
        thresholds = self.default_thresholds.get(SensorType(sensor_type), {})
        return thresholds.get("max", 100.0)
    
    async def update_thresholds(self, sensor_id: str, sensor_type: SensorType, min_val: float, max_val: float):
        """Update thresholds for a specific sensor"""
        # This would typically update the database
        # For now, we'll update the default thresholds
        if sensor_type not in self.default_thresholds:
            self.default_thresholds[sensor_type] = {}
        
        self.default_thresholds[sensor_type]["min"] = min_val
        self.default_thresholds[sensor_type]["max"] = max_val
