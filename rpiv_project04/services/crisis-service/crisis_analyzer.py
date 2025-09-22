import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import statistics

class CrisisAnalyzer:
    """Analyzes sensor data to detect critical events"""
    
    def __init__(self):
        # Critical thresholds for different parameters
        self.thresholds = {
            "water_level": {
                "flood_risk": 8.0,  # meters
                "drought_risk": 1.0  # meters
            },
            "pressure": {
                "critical_low": 1.0,  # bar
                "critical_high": 8.0   # bar
            },
            "flow_rate": {
                "critical_low": 10.0,  # L/s
                "critical_high": 1000.0  # L/s
            },
            "water_quality": {
                "contamination_risk": 0.7  # quality index
            },
            "precipitation": {
                "flood_risk": 50.0  # mm/hour
            }
        }
    
    async def analyze_readings(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze sensor readings for critical conditions"""
        critical_events = []
        
        try:
            # Group readings by location/area
            location_groups = self._group_by_location(readings)
            
            for location, location_readings in location_groups.items():
                # Analyze each parameter type
                events = await self._analyze_location_readings(location, location_readings)
                critical_events.extend(events)
            
            # Analyze patterns across multiple locations
            pattern_events = await self._analyze_regional_patterns(readings)
            critical_events.extend(pattern_events)
            
        except Exception as e:
            print(f"Error analyzing readings: {e}")
        
        return critical_events
    
    def _group_by_location(self, readings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group readings by location"""
        groups = {}
        
        for reading in readings:
            location = reading.get("location", "unknown")
            if location not in groups:
                groups[location] = []
            groups[location].append(reading)
        
        return groups
    
    async def _analyze_location_readings(self, location: str, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze readings for a specific location"""
        events = []
        
        # Get latest readings by parameter type
        latest_readings = self._get_latest_by_parameter(readings)
        
        # Check water level for flood/drought risk
        if "water_level" in latest_readings:
            level_events = self._check_water_level_risks(location, latest_readings["water_level"])
            events.extend(level_events)
        
        # Check pressure anomalies
        if "pressure" in latest_readings:
            pressure_events = self._check_pressure_anomalies(location, latest_readings["pressure"])
            events.extend(pressure_events)
        
        # Check flow rate anomalies
        if "flow_rate" in latest_readings:
            flow_events = self._check_flow_anomalies(location, latest_readings["flow_rate"])
            events.extend(flow_events)
        
        # Check water quality
        if "water_quality" in latest_readings:
            quality_events = self._check_water_quality(location, latest_readings["water_quality"])
            events.extend(quality_events)
        
        # Check precipitation for flood risk
        if "precipitation" in latest_readings:
            precip_events = self._check_precipitation_risk(location, latest_readings["precipitation"])
            events.extend(precip_events)
        
        return events
    
    def _get_latest_by_parameter(self, readings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Get latest readings grouped by parameter type"""
        parameter_groups = {}
        
        for reading in readings:
            param_type = reading.get("parameter_type", "unknown")
            if param_type not in parameter_groups:
                parameter_groups[param_type] = []
            parameter_groups[param_type].append(reading)
        
        # Sort by timestamp and get recent readings
        for param_type in parameter_groups:
            parameter_groups[param_type].sort(
                key=lambda x: x.get("timestamp", ""), 
                reverse=True
            )
            # Keep only last 10 readings for analysis
            parameter_groups[param_type] = parameter_groups[param_type][:10]
        
        return parameter_groups
    
    def _check_water_level_risks(self, location: str, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for flood or drought risks based on water level"""
        events = []
        
        if not readings:
            return events
        
        latest_reading = readings[0]
        water_level = latest_reading.get("value", 0)
        
        # Flood risk
        if water_level > self.thresholds["water_level"]["flood_risk"]:
            events.append({
                "event_type": "flood_risk",
                "description": f"Nível de água crítico detectado: {water_level}m (limite: {self.thresholds['water_level']['flood_risk']}m)",
                "severity": "high" if water_level > self.thresholds["water_level"]["flood_risk"] * 1.2 else "medium",
                "location": location,
                "coordinates": latest_reading.get("coordinates"),
                "affected_population": self._estimate_affected_population(location, "flood"),
                "sensor_data": {
                    "sensor_id": latest_reading.get("sensor_id"),
                    "water_level": water_level,
                    "threshold": self.thresholds["water_level"]["flood_risk"],
                    "timestamp": latest_reading.get("timestamp")
                },
                "created_by": 1  # System user
            })
        
        # Drought risk
        elif water_level < self.thresholds["water_level"]["drought_risk"]:
            events.append({
                "event_type": "drought_risk",
                "description": f"Nível de água baixo detectado: {water_level}m (limite: {self.thresholds['water_level']['drought_risk']}m)",
                "severity": "medium" if water_level > self.thresholds["water_level"]["drought_risk"] * 0.5 else "high",
                "location": location,
                "coordinates": latest_reading.get("coordinates"),
                "affected_population": self._estimate_affected_population(location, "drought"),
                "sensor_data": {
                    "sensor_id": latest_reading.get("sensor_id"),
                    "water_level": water_level,
                    "threshold": self.thresholds["water_level"]["drought_risk"],
                    "timestamp": latest_reading.get("timestamp")
                },
                "created_by": 1  # System user
            })
        
        return events
    
    def _check_pressure_anomalies(self, location: str, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for pressure anomalies"""
        events = []
        
        if not readings:
            return events
        
        latest_reading = readings[0]
        pressure = latest_reading.get("value", 0)
        
        if pressure < self.thresholds["pressure"]["critical_low"]:
            events.append({
                "event_type": "pressure_drop",
                "description": f"Pressão crítica baixa detectada: {pressure} bar",
                "severity": "high",
                "location": location,
                "coordinates": latest_reading.get("coordinates"),
                "affected_population": self._estimate_affected_population(location, "pressure_drop"),
                "sensor_data": {
                    "sensor_id": latest_reading.get("sensor_id"),
                    "pressure": pressure,
                    "threshold": self.thresholds["pressure"]["critical_low"],
                    "timestamp": latest_reading.get("timestamp")
                },
                "created_by": 1
            })
        
        elif pressure > self.thresholds["pressure"]["critical_high"]:
            events.append({
                "event_type": "pressure_surge",
                "description": f"Pressão crítica alta detectada: {pressure} bar",
                "severity": "high",
                "location": location,
                "coordinates": latest_reading.get("coordinates"),
                "affected_population": self._estimate_affected_population(location, "pressure_surge"),
                "sensor_data": {
                    "sensor_id": latest_reading.get("sensor_id"),
                    "pressure": pressure,
                    "threshold": self.thresholds["pressure"]["critical_high"],
                    "timestamp": latest_reading.get("timestamp")
                },
                "created_by": 1
            })
        
        return events
    
    def _check_flow_anomalies(self, location: str, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for flow rate anomalies"""
        events = []
        
        if not readings:
            return events
        
        latest_reading = readings[0]
        flow_rate = latest_reading.get("value", 0)
        
        if flow_rate < self.thresholds["flow_rate"]["critical_low"]:
            events.append({
                "event_type": "low_flow",
                "description": f"Vazão crítica baixa detectada: {flow_rate} L/s",
                "severity": "medium",
                "location": location,
                "coordinates": latest_reading.get("coordinates"),
                "affected_population": self._estimate_affected_population(location, "low_flow"),
                "sensor_data": {
                    "sensor_id": latest_reading.get("sensor_id"),
                    "flow_rate": flow_rate,
                    "threshold": self.thresholds["flow_rate"]["critical_low"],
                    "timestamp": latest_reading.get("timestamp")
                },
                "created_by": 1
            })
        
        elif flow_rate > self.thresholds["flow_rate"]["critical_high"]:
            events.append({
                "event_type": "high_flow",
                "description": f"Vazão crítica alta detectada: {flow_rate} L/s",
                "severity": "medium",
                "location": location,
                "coordinates": latest_reading.get("coordinates"),
                "affected_population": self._estimate_affected_population(location, "high_flow"),
                "sensor_data": {
                    "sensor_id": latest_reading.get("sensor_id"),
                    "flow_rate": flow_rate,
                    "threshold": self.thresholds["flow_rate"]["critical_high"],
                    "timestamp": latest_reading.get("timestamp")
                },
                "created_by": 1
            })
        
        return events
    
    def _check_water_quality(self, location: str, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for water quality issues"""
        events = []
        
        if not readings:
            return events
        
        latest_reading = readings[0]
        quality_index = latest_reading.get("value", 1.0)
        
        if quality_index < self.thresholds["water_quality"]["contamination_risk"]:
            events.append({
                "event_type": "water_contamination",
                "description": f"Possível contaminação da água detectada. Índice de qualidade: {quality_index}",
                "severity": "critical",
                "location": location,
                "coordinates": latest_reading.get("coordinates"),
                "affected_population": self._estimate_affected_population(location, "contamination"),
                "sensor_data": {
                    "sensor_id": latest_reading.get("sensor_id"),
                    "quality_index": quality_index,
                    "threshold": self.thresholds["water_quality"]["contamination_risk"],
                    "timestamp": latest_reading.get("timestamp")
                },
                "created_by": 1
            })
        
        return events
    
    def _check_precipitation_risk(self, location: str, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for precipitation-related flood risk"""
        events = []
        
        if not readings:
            return events
        
        latest_reading = readings[0]
        precipitation = latest_reading.get("value", 0)
        
        if precipitation > self.thresholds["precipitation"]["flood_risk"]:
            events.append({
                "event_type": "heavy_rainfall",
                "description": f"Precipitação intensa detectada: {precipitation} mm/h",
                "severity": "high" if precipitation > self.thresholds["precipitation"]["flood_risk"] * 1.5 else "medium",
                "location": location,
                "coordinates": latest_reading.get("coordinates"),
                "affected_population": self._estimate_affected_population(location, "flood"),
                "sensor_data": {
                    "sensor_id": latest_reading.get("sensor_id"),
                    "precipitation": precipitation,
                    "threshold": self.thresholds["precipitation"]["flood_risk"],
                    "timestamp": latest_reading.get("timestamp")
                },
                "created_by": 1
            })
        
        return events
    
    async def _analyze_regional_patterns(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze patterns across multiple locations"""
        events = []
        
        try:
            # Look for widespread anomalies
            pressure_readings = [r for r in readings if r.get("parameter_type") == "pressure"]
            
            if len(pressure_readings) >= 3:
                # Check for widespread pressure drops (possible major leak)
                low_pressure_count = sum(1 for r in pressure_readings 
                                       if r.get("value", 0) < self.thresholds["pressure"]["critical_low"] * 1.5)
                
                if low_pressure_count >= len(pressure_readings) * 0.6:  # 60% of sensors
                    events.append({
                        "event_type": "system_wide_pressure_drop",
                        "description": f"Queda de pressão sistêmica detectada em {low_pressure_count} sensores",
                        "severity": "critical",
                        "location": "Sistema Regional",
                        "affected_population": 50000,  # Estimate for regional event
                        "sensor_data": {
                            "affected_sensors": low_pressure_count,
                            "total_sensors": len(pressure_readings),
                            "pattern": "widespread_pressure_drop"
                        },
                        "created_by": 1
                    })
            
        except Exception as e:
            print(f"Error analyzing regional patterns: {e}")
        
        return events
    
    def _estimate_affected_population(self, location: str, event_type: str) -> int:
        """Estimate affected population based on location and event type"""
        # Simplified population estimation
        base_population = {
            "Centro": 15000,
            "Norte": 12000,
            "Sul": 18000,
            "Leste": 10000,
            "Oeste": 14000,
            "Industrial": 5000
        }
        
        # Event type multipliers
        multipliers = {
            "flood": 0.8,
            "drought": 0.6,
            "contamination": 1.0,
            "pressure_drop": 0.4,
            "pressure_surge": 0.2
        }
        
        pop = base_population.get(location, 8000)
        multiplier = multipliers.get(event_type, 0.5)
        
        return int(pop * multiplier)
