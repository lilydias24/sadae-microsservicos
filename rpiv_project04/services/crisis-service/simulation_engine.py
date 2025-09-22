import asyncio
import random
import math
from typing import Dict, List, Any
from datetime import datetime, timedelta

class SimulationEngine:
    """Runs crisis simulations to predict impacts"""
    
    def __init__(self):
        # Base parameters for different scenarios
        self.scenario_configs = {
            "drought": {
                "water_reduction_factor": 0.3,
                "duration_multiplier": 1.5,
                "affected_infrastructure": ["reservoirs", "pumps", "distribution"],
                "population_impact_factor": 0.7
            },
            "flood": {
                "infrastructure_damage_factor": 0.4,
                "evacuation_factor": 0.2,
                "affected_infrastructure": ["pumps", "treatment", "distribution"],
                "population_impact_factor": 0.8
            },
            "contamination": {
                "water_quality_factor": 0.1,
                "treatment_capacity_factor": 0.5,
                "affected_infrastructure": ["treatment", "distribution"],
                "population_impact_factor": 1.0
            },
            "infrastructure_failure": {
                "service_disruption_factor": 0.6,
                "repair_time_factor": 2.0,
                "affected_infrastructure": ["pumps", "pipes", "distribution"],
                "population_impact_factor": 0.5
            }
        }
    
    async def run_simulation(self, scenario_type: str, parameters: Dict[str, Any], 
                           duration_days: int, affected_areas: List[str]) -> Dict[str, Any]:
        """Run a crisis simulation"""
        
        try:
            # Get scenario configuration
            config = self.scenario_configs.get(scenario_type, self.scenario_configs["drought"])
            
            # Initialize simulation state
            simulation_state = self._initialize_simulation_state(affected_areas, parameters)
            
            # Run simulation day by day
            daily_results = []
            for day in range(duration_days):
                day_result = await self._simulate_day(
                    day, scenario_type, config, parameters, simulation_state
                )
                daily_results.append(day_result)
                
                # Update simulation state
                self._update_simulation_state(simulation_state, day_result, config)
            
            # Generate final results
            final_results = self._generate_final_results(
                scenario_type, daily_results, simulation_state, affected_areas
            )
            
            return final_results
            
        except Exception as e:
            return {
                "error": f"Simulation failed: {str(e)}",
                "status": "failed"
            }
    
    def _initialize_simulation_state(self, affected_areas: List[str], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize simulation state"""
        
        # Base infrastructure capacity for each area
        area_capacity = {
            "Centro": {"population": 15000, "water_capacity": 2000, "reservoirs": 3},
            "Norte": {"population": 12000, "water_capacity": 1600, "reservoirs": 2},
            "Sul": {"population": 18000, "water_capacity": 2400, "reservoirs": 4},
            "Leste": {"population": 10000, "water_capacity": 1400, "reservoirs": 2},
            "Oeste": {"population": 14000, "water_capacity": 1800, "reservoirs": 3},
            "Industrial": {"population": 5000, "water_capacity": 3000, "reservoirs": 2}
        }
        
        state = {
            "areas": {},
            "total_population": 0,
            "total_capacity": 0,
            "day": 0,
            "cumulative_impact": 0
        }
        
        for area in affected_areas:
            if area in area_capacity:
                state["areas"][area] = {
                    **area_capacity[area],
                    "current_capacity": area_capacity[area]["water_capacity"],
                    "service_level": 1.0,  # 100% service
                    "infrastructure_health": 1.0,
                    "population_affected": 0
                }
                state["total_population"] += area_capacity[area]["population"]
                state["total_capacity"] += area_capacity[area]["water_capacity"]
        
        # Apply initial parameters
        severity = parameters.get("severity", 0.5)  # 0-1 scale
        state["severity"] = severity
        state["initial_impact"] = severity * 0.2  # Initial 20% impact at max severity
        
        return state
    
    async def _simulate_day(self, day: int, scenario_type: str, config: Dict[str, Any], 
                          parameters: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate one day of the crisis"""
        
        day_result = {
            "day": day,
            "scenario_type": scenario_type,
            "areas_affected": {},
            "total_people_affected": 0,
            "water_shortage_percentage": 0,
            "infrastructure_damage": 0,
            "emergency_actions_needed": []
        }
        
        severity = state["severity"]
        
        # Simulate each affected area
        for area_name, area_data in state["areas"].items():
            area_result = self._simulate_area_day(
                area_name, area_data, day, scenario_type, config, parameters, severity
            )
            day_result["areas_affected"][area_name] = area_result
            day_result["total_people_affected"] += area_result["people_affected"]
        
        # Calculate overall metrics
        if state["total_population"] > 0:
            day_result["affected_population_percentage"] = (
                day_result["total_people_affected"] / state["total_population"]
            ) * 100
        
        # Determine emergency actions needed
        day_result["emergency_actions_needed"] = self._determine_emergency_actions(
            day_result, scenario_type, severity
        )
        
        return day_result
    
    def _simulate_area_day(self, area_name: str, area_data: Dict[str, Any], day: int,
                          scenario_type: str, config: Dict[str, Any], 
                          parameters: Dict[str, Any], severity: float) -> Dict[str, Any]:
        """Simulate one day for a specific area"""
        
        # Calculate impact progression (gets worse over time, then may stabilize)
        time_factor = min(1.0, day / 7.0)  # Reaches full impact after 7 days
        current_impact = severity * time_factor
        
        # Apply scenario-specific effects
        if scenario_type == "drought":
            capacity_reduction = current_impact * config["water_reduction_factor"]
            area_data["current_capacity"] = area_data["water_capacity"] * (1 - capacity_reduction)
            
        elif scenario_type == "flood":
            infrastructure_damage = current_impact * config["infrastructure_damage_factor"]
            area_data["infrastructure_health"] = max(0.1, 1 - infrastructure_damage)
            area_data["current_capacity"] = area_data["water_capacity"] * area_data["infrastructure_health"]
            
        elif scenario_type == "contamination":
            treatment_impact = current_impact * config["treatment_capacity_factor"]
            area_data["current_capacity"] = area_data["water_capacity"] * (1 - treatment_impact)
            
        elif scenario_type == "infrastructure_failure":
            service_disruption = current_impact * config["service_disruption_factor"]
            area_data["service_level"] = max(0.1, 1 - service_disruption)
            area_data["current_capacity"] = area_data["water_capacity"] * area_data["service_level"]
        
        # Calculate people affected
        demand = area_data["population"] * 200  # 200L per person per day
        supply = area_data["current_capacity"] * 1000  # Convert to liters
        
        if supply < demand:
            shortage_percentage = ((demand - supply) / demand) * 100
            people_affected = int(area_data["population"] * (shortage_percentage / 100))
        else:
            shortage_percentage = 0
            people_affected = 0
        
        # Add some randomness for realism
        people_affected += random.randint(-int(people_affected * 0.1), int(people_affected * 0.1))
        people_affected = max(0, people_affected)
        
        return {
            "area": area_name,
            "people_affected": people_affected,
            "shortage_percentage": round(shortage_percentage, 2),
            "current_capacity": round(area_data["current_capacity"], 2),
            "service_level": round(area_data["service_level"], 2),
            "infrastructure_health": round(area_data.get("infrastructure_health", 1.0), 2)
        }
    
    def _update_simulation_state(self, state: Dict[str, Any], day_result: Dict[str, Any], 
                               config: Dict[str, Any]):
        """Update simulation state after each day"""
        state["day"] += 1
        state["cumulative_impact"] += day_result["total_people_affected"]
        
        # Some recovery might occur over time for certain scenarios
        recovery_factor = 0.02  # 2% recovery per day after day 10
        if state["day"] > 10:
            for area_data in state["areas"].values():
                if area_data["infrastructure_health"] < 1.0:
                    area_data["infrastructure_health"] = min(1.0, 
                        area_data["infrastructure_health"] + recovery_factor)
    
    def _determine_emergency_actions(self, day_result: Dict[str, Any], 
                                   scenario_type: str, severity: float) -> List[str]:
        """Determine what emergency actions are needed"""
        actions = []
        
        affected_percentage = day_result.get("affected_population_percentage", 0)
        
        if affected_percentage > 50:
            actions.append("Declarar estado de emergência")
            actions.append("Ativar plano de distribuição de água por caminhões-pipa")
            
        if affected_percentage > 30:
            actions.append("Implementar racionamento de água")
            actions.append("Ativar fontes alternativas de abastecimento")
            
        if affected_percentage > 20:
            actions.append("Intensificar monitoramento da rede")
            actions.append("Preparar equipes de emergência")
        
        # Scenario-specific actions
        if scenario_type == "flood" and affected_percentage > 15:
            actions.append("Evacuar áreas de risco")
            actions.append("Isolar estações de tratamento afetadas")
            
        elif scenario_type == "contamination" and affected_percentage > 10:
            actions.append("Suspender distribuição de água contaminada")
            actions.append("Ativar protocolo de descontaminação")
            
        elif scenario_type == "drought" and affected_percentage > 25:
            actions.append("Reduzir pressão na rede para conservar água")
            actions.append("Implementar uso prioritário para consumo humano")
        
        return actions
    
    def _generate_final_results(self, scenario_type: str, daily_results: List[Dict[str, Any]], 
                              state: Dict[str, Any], affected_areas: List[str]) -> Dict[str, Any]:
        """Generate final simulation results"""
        
        # Calculate summary statistics
        max_affected = max(day["total_people_affected"] for day in daily_results)
        avg_affected = sum(day["total_people_affected"] for day in daily_results) / len(daily_results)
        
        peak_day = max(daily_results, key=lambda x: x["total_people_affected"])
        
        # Calculate infrastructure impact
        final_infrastructure_health = []
        for area_data in state["areas"].values():
            final_infrastructure_health.append(area_data.get("infrastructure_health", 1.0))
        
        avg_infrastructure_health = sum(final_infrastructure_health) / len(final_infrastructure_health)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            scenario_type, max_affected, state["total_population"], avg_infrastructure_health
        )
        
        return {
            "scenario_type": scenario_type,
            "duration_days": len(daily_results),
            "affected_areas": affected_areas,
            "summary": {
                "total_population": state["total_population"],
                "max_people_affected": max_affected,
                "avg_people_affected": round(avg_affected),
                "peak_impact_day": peak_day["day"],
                "peak_impact_percentage": round((max_affected / state["total_population"]) * 100, 2),
                "cumulative_impact": state["cumulative_impact"],
                "final_infrastructure_health": round(avg_infrastructure_health * 100, 2)
            },
            "daily_progression": daily_results,
            "critical_days": [day for day in daily_results if day["total_people_affected"] > state["total_population"] * 0.3],
            "emergency_actions_summary": self._summarize_emergency_actions(daily_results),
            "recommendations": recommendations,
            "areas_impact": {
                area: {
                    "final_capacity": round(data["current_capacity"], 2),
                    "final_service_level": round(data["service_level"], 2),
                    "infrastructure_health": round(data.get("infrastructure_health", 1.0), 2)
                }
                for area, data in state["areas"].items()
            }
        }
    
    def _generate_recommendations(self, scenario_type: str, max_affected: int, 
                                total_population: int, infrastructure_health: float) -> List[str]:
        """Generate recommendations based on simulation results"""
        recommendations = []
        
        impact_percentage = (max_affected / total_population) * 100
        
        if impact_percentage > 40:
            recommendations.append("Investir em redundância do sistema de abastecimento")
            recommendations.append("Criar reservas estratégicas de água")
            recommendations.append("Desenvolver plano de emergência robusto")
            
        if impact_percentage > 25:
            recommendations.append("Melhorar sistema de monitoramento em tempo real")
            recommendations.append("Treinar equipes para resposta rápida")
            
        if infrastructure_health < 0.7:
            recommendations.append("Modernizar infraestrutura crítica")
            recommendations.append("Implementar manutenção preventiva mais rigorosa")
        
        # Scenario-specific recommendations
        if scenario_type == "drought":
            recommendations.append("Diversificar fontes de abastecimento")
            recommendations.append("Implementar programa de conservação de água")
            
        elif scenario_type == "flood":
            recommendations.append("Melhorar drenagem urbana")
            recommendations.append("Elevar equipamentos críticos acima do nível de inundação")
            
        elif scenario_type == "contamination":
            recommendations.append("Instalar sistemas de detecção de contaminação")
            recommendations.append("Criar protocolos de isolamento rápido")
        
        return recommendations
    
    def _summarize_emergency_actions(self, daily_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize emergency actions across all days"""
        action_counts = {}
        
        for day in daily_results:
            for action in day.get("emergency_actions_needed", []):
                action_counts[action] = action_counts.get(action, 0) + 1
        
        return action_counts
