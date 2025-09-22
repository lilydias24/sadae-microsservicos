import asyncio
import math
import random
from typing import List, Dict, Any, Tuple

class RouteCalculator:
    """Calculates evacuation routes avoiding blocked areas"""
    
    def __init__(self):
        # Predefined safe zones and key locations
        self.safe_zones = {
            "Centro_Safe": {"lat": -29.6842, "lng": -50.8094, "name": "Centro de Evacuação Central", "capacity": 5000},
            "Norte_Safe": {"lat": -29.6700, "lng": -50.8000, "name": "Escola Norte", "capacity": 2000},
            "Sul_Safe": {"lat": -29.7000, "lng": -50.8200, "name": "Ginásio Sul", "capacity": 3000},
            "Leste_Safe": {"lat": -29.6800, "lng": -50.7900, "name": "Centro Comunitário Leste", "capacity": 1500},
            "Oeste_Safe": {"lat": -29.6900, "lng": -50.8300, "name": "Parque Oeste", "capacity": 4000}
        }
        
        # Key intersection points for routing
        self.key_points = {
            "Centro": {"lat": -29.6842, "lng": -50.8094},
            "Norte": {"lat": -29.6700, "lng": -50.8000},
            "Sul": {"lat": -29.7000, "lng": -50.8200},
            "Leste": {"lat": -29.6800, "lng": -50.7900},
            "Oeste": {"lat": -29.6900, "lng": -50.8300},
            "Industrial": {"lat": -29.6950, "lng": -50.7850}
        }
    
    async def calculate_evacuation_routes(self, affected_area: str, blocked_points: List[Dict[str, Any]], 
                                        safe_zones: List[Dict[str, Any]], max_routes: int = 5) -> List[Dict[str, Any]]:
        """Calculate evacuation routes for an affected area"""
        
        try:
            # Get starting points in the affected area
            start_points = self._get_area_start_points(affected_area)
            
            # Combine provided safe zones with predefined ones
            all_safe_zones = self._merge_safe_zones(safe_zones)
            
            # Calculate routes from each start point to safe zones
            all_routes = []
            
            for start_point in start_points:
                for safe_zone in all_safe_zones:
                    route = await self._calculate_single_route(
                        start_point, safe_zone, blocked_points
                    )
                    if route:
                        all_routes.append(route)
            
            # Select best routes
            best_routes = self._select_best_routes(all_routes, max_routes)
            
            return best_routes
            
        except Exception as e:
            print(f"Error calculating evacuation routes: {e}")
            return []
    
    def _get_area_start_points(self, affected_area: str) -> List[Dict[str, Any]]:
        """Get starting points for evacuation in the affected area"""
        
        if affected_area in self.key_points:
            base_point = self.key_points[affected_area]
            
            # Generate multiple start points around the area
            start_points = []
            for i in range(3):  # 3 start points per area
                # Add some variation to create multiple evacuation points
                lat_offset = (random.random() - 0.5) * 0.01  # ~1km variation
                lng_offset = (random.random() - 0.5) * 0.01
                
                start_points.append({
                    "lat": base_point["lat"] + lat_offset,
                    "lng": base_point["lng"] + lng_offset,
                    "name": f"{affected_area} - Ponto {i+1}",
                    "area": affected_area
                })
            
            return start_points
        else:
            # Default fallback point
            return [{
                "lat": -29.6842,
                "lng": -50.8094,
                "name": f"{affected_area} - Centro",
                "area": affected_area
            }]
    
    def _merge_safe_zones(self, provided_zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge provided safe zones with predefined ones"""
        
        all_zones = list(self.safe_zones.values())
        
        # Add provided safe zones
        for zone in provided_zones:
            if "lat" in zone and "lng" in zone:
                all_zones.append({
                    "lat": zone["lat"],
                    "lng": zone["lng"],
                    "name": zone.get("name", "Zona Segura"),
                    "capacity": zone.get("capacity", 1000)
                })
        
        return all_zones
    
    async def _calculate_single_route(self, start_point: Dict[str, Any], 
                                    safe_zone: Dict[str, Any], 
                                    blocked_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate a single route from start to safe zone"""
        
        try:
            # Calculate direct distance
            direct_distance = self._calculate_distance(
                start_point["lat"], start_point["lng"],
                safe_zone["lat"], safe_zone["lng"]
            )
            
            # Check if direct route is blocked
            waypoints = []
            total_distance = direct_distance
            
            if self._is_route_blocked(start_point, safe_zone, blocked_points):
                # Find alternative route with waypoints
                waypoints = self._find_alternative_waypoints(start_point, safe_zone, blocked_points)
                total_distance = self._calculate_route_distance(start_point, waypoints, safe_zone)
            
            # Estimate travel time (assuming 5 km/h walking speed)
            estimated_time = int((total_distance / 5.0) * 60)  # Minutes
            
            # Calculate route capacity (based on safe zone capacity and route difficulty)
            route_difficulty = len(waypoints) + (1 if len(blocked_points) > 0 else 0)
            capacity = max(100, safe_zone.get("capacity", 1000) // (route_difficulty + 1))
            
            return {
                "name": f"Rota {start_point['name']} → {safe_zone['name']}",
                "start_point": start_point,
                "end_point": safe_zone,
                "waypoints": waypoints,
                "distance_km": round(total_distance, 2),
                "estimated_time": estimated_time,
                "capacity": capacity,
                "difficulty": "baixa" if route_difficulty <= 1 else "média" if route_difficulty <= 3 else "alta",
                "blocked_points_avoided": len([bp for bp in blocked_points if self._point_affects_route(bp, start_point, safe_zone)])
            }
            
        except Exception as e:
            print(f"Error calculating single route: {e}")
            return None
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in km
        r = 6371
        
        return r * c
    
    def _is_route_blocked(self, start: Dict[str, Any], end: Dict[str, Any], 
                         blocked_points: List[Dict[str, Any]]) -> bool:
        """Check if direct route is blocked by any blocked points"""
        
        for blocked in blocked_points:
            if "lat" in blocked and "lng" in blocked:
                # Check if blocked point is close to the direct route
                distance_to_start = self._calculate_distance(
                    start["lat"], start["lng"], blocked["lat"], blocked["lng"]
                )
                distance_to_end = self._calculate_distance(
                    end["lat"], end["lng"], blocked["lat"], blocked["lng"]
                )
                direct_distance = self._calculate_distance(
                    start["lat"], start["lng"], end["lat"], end["lng"]
                )
                
                # If blocked point is close to the route line, consider it blocked
                if (distance_to_start + distance_to_end) <= (direct_distance * 1.2):
                    return True
        
        return False
    
    def _find_alternative_waypoints(self, start: Dict[str, Any], end: Dict[str, Any], 
                                  blocked_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find waypoints to avoid blocked areas"""
        
        waypoints = []
        
        # Simple algorithm: create waypoints that go around blocked areas
        for blocked in blocked_points:
            if "lat" in blocked and "lng" in blocked:
                # Create waypoint that goes around the blocked area
                # This is a simplified approach - in reality, you'd use proper pathfinding
                
                # Calculate perpendicular offset
                lat_offset = 0.005  # ~500m offset
                lng_offset = 0.005
                
                # Alternate between left and right offsets
                if len(waypoints) % 2 == 0:
                    waypoint_lat = blocked["lat"] + lat_offset
                    waypoint_lng = blocked["lng"] + lng_offset
                else:
                    waypoint_lat = blocked["lat"] - lat_offset
                    waypoint_lng = blocked["lng"] - lng_offset
                
                waypoints.append({
                    "lat": waypoint_lat,
                    "lng": waypoint_lng,
                    "name": f"Desvio {len(waypoints) + 1}",
                    "type": "detour"
                })
        
        return waypoints
    
    def _calculate_route_distance(self, start: Dict[str, Any], waypoints: List[Dict[str, Any]], 
                                end: Dict[str, Any]) -> float:
        """Calculate total distance of route with waypoints"""
        
        total_distance = 0
        current_point = start
        
        # Distance through waypoints
        for waypoint in waypoints:
            distance = self._calculate_distance(
                current_point["lat"], current_point["lng"],
                waypoint["lat"], waypoint["lng"]
            )
            total_distance += distance
            current_point = waypoint
        
        # Distance from last waypoint (or start) to end
        final_distance = self._calculate_distance(
            current_point["lat"], current_point["lng"],
            end["lat"], end["lng"]
        )
        total_distance += final_distance
        
        return total_distance
    
    def _point_affects_route(self, blocked_point: Dict[str, Any], 
                           start: Dict[str, Any], end: Dict[str, Any]) -> bool:
        """Check if a blocked point affects a specific route"""
        
        if "lat" not in blocked_point or "lng" not in blocked_point:
            return False
        
        # Calculate if blocked point is within reasonable distance of the route
        distance_to_start = self._calculate_distance(
            start["lat"], start["lng"], blocked_point["lat"], blocked_point["lng"]
        )
        distance_to_end = self._calculate_distance(
            end["lat"], end["lng"], blocked_point["lat"], blocked_point["lng"]
        )
        direct_distance = self._calculate_distance(
            start["lat"], start["lng"], end["lat"], end["lng"]
        )
        
        # If the sum of distances to blocked point is close to direct distance,
        # the blocked point is likely on or near the route
        return (distance_to_start + distance_to_end) <= (direct_distance * 1.3)
    
    def _select_best_routes(self, all_routes: List[Dict[str, Any]], max_routes: int) -> List[Dict[str, Any]]:
        """Select the best routes based on multiple criteria"""
        
        if not all_routes:
            return []
        
        # Score routes based on multiple factors
        for route in all_routes:
            score = 0
            
            # Shorter distance is better
            distance_score = max(0, 100 - (route["distance_km"] * 10))
            
            # Higher capacity is better
            capacity_score = min(100, route["capacity"] / 50)
            
            # Fewer waypoints (simpler route) is better
            simplicity_score = max(0, 100 - (len(route["waypoints"]) * 20))
            
            # Avoiding more blocked points is better
            avoidance_score = route["blocked_points_avoided"] * 10
            
            # Combined score
            route["score"] = (distance_score * 0.3 + capacity_score * 0.3 + 
                            simplicity_score * 0.2 + avoidance_score * 0.2)
        
        # Sort by score and return top routes
        sorted_routes = sorted(all_routes, key=lambda x: x["score"], reverse=True)
        
        # Ensure diversity - don't return too many routes to the same safe zone
        selected_routes = []
        used_safe_zones = set()
        
        for route in sorted_routes:
            if len(selected_routes) >= max_routes:
                break
            
            safe_zone_name = route["end_point"]["name"]
            if safe_zone_name not in used_safe_zones or len(selected_routes) < max_routes // 2:
                selected_routes.append(route)
                used_safe_zones.add(safe_zone_name)
        
        return selected_routes
