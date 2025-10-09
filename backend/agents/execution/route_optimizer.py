"""
Route Optimizer Agent
Optimizes drone flight paths and search patterns
"""

import asyncio
import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

class RouteOptimizerAgent(BaseAgent):
    """Optimizes drone routes and search patterns"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("route_optimizer", redis_service, websocket_manager)
        self.optimization_cache: Dict[str, Dict[str, Any]] = {}
    
    async def start_agent(self) -> None:
        """Start the route optimizer"""
        await self.subscribe_to_channel("task.assignment_created")
        await self.subscribe_to_channel("drone.route_request")
        await self.subscribe_to_channel("mission.zone_update")
        logger.info("Route Optimizer Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the route optimizer"""
        logger.info("Route Optimizer Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "task.assignment_created":
                await self._handle_assignment_created(message)
            elif channel == "drone.route_request":
                await self._handle_route_request(message)
            elif channel == "mission.zone_update":
                await self._handle_zone_update(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_assignment_created(self, message: Dict[str, Any]) -> None:
        """Handle new task assignment created"""
        assignment = message.get("assignment", {})
        assignment_id = assignment.get("assignment_id")
        
        if not assignment_id:
            return
        
        logger.info(f"Optimizing route for assignment {assignment_id}")
        
        # Optimize the route for this assignment
        optimized_route = await self._optimize_assignment_route(assignment)
        
        if optimized_route:
            # Cache the optimized route
            self.optimization_cache[assignment_id] = optimized_route
            
            # Publish optimized route
            await self.publish_message("route.optimized", {
                "assignment_id": assignment_id,
                "optimized_route": optimized_route
            })
            
            logger.info(f"Route optimized for assignment {assignment_id}")
    
    async def _handle_route_request(self, message: Dict[str, Any]) -> None:
        """Handle route optimization request from drone"""
        drone_id = message.get("drone_id")
        assignment_id = message.get("assignment_id")
        current_position = message.get("current_position", {})
        
        if not assignment_id:
            return
        
        # Check if we have cached optimization
        if assignment_id in self.optimization_cache:
            optimized_route = self.optimization_cache[assignment_id]
        else:
            # Create new optimization
            assignment = message.get("assignment", {})
            optimized_route = await self._optimize_assignment_route(assignment)
            if optimized_route:
                self.optimization_cache[assignment_id] = optimized_route
        
        if optimized_route:
            # Send optimized route to drone
            await self.publish_message("drone.optimized_route", {
                "drone_id": drone_id,
                "assignment_id": assignment_id,
                "route": optimized_route
            })
    
    async def _handle_zone_update(self, message: Dict[str, Any]) -> None:
        """Handle zone update that requires route reoptimization"""
        assignment_id = message.get("assignment_id")
        updated_zone = message.get("zone", {})
        
        if assignment_id in self.optimization_cache:
            # Reoptimize with updated zone
            assignment = self.optimization_cache[assignment_id].get("original_assignment", {})
            assignment["zone"] = updated_zone
            
            optimized_route = await self._optimize_assignment_route(assignment)
            if optimized_route:
                self.optimization_cache[assignment_id] = optimized_route
                
                # Publish updated route
                await self.publish_message("route.reoptimized", {
                    "assignment_id": assignment_id,
                    "optimized_route": optimized_route
                })
    
    async def _optimize_assignment_route(self, assignment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize route for a specific assignment"""
        try:
            zone = assignment.get("zone", {})
            search_pattern = assignment.get("search_pattern", "grid")
            waypoints = assignment.get("waypoints", [])
            
            if not waypoints:
                # Generate waypoints if not provided
                waypoints = await self._generate_zone_waypoints(zone)
            
            if not waypoints:
                return None
            
            # Optimize based on search pattern
            if search_pattern == "grid":
                optimized_waypoints = await self._optimize_grid_pattern(waypoints, zone)
            elif search_pattern == "spiral":
                optimized_waypoints = await self._optimize_spiral_pattern(waypoints, zone)
            elif search_pattern == "zigzag":
                optimized_waypoints = await self._optimize_zigzag_pattern(waypoints, zone)
            else:
                optimized_waypoints = waypoints
            
            # Calculate route metrics
            total_distance = self._calculate_total_distance(optimized_waypoints)
            estimated_time = self._calculate_estimated_time(optimized_waypoints, assignment.get("speed", 8))
            
            optimized_route = {
                "assignment_id": assignment.get("assignment_id"),
                "drone_id": assignment.get("drone_id"),
                "waypoints": optimized_waypoints,
                "total_distance": total_distance,
                "estimated_time": estimated_time,
                "search_pattern": search_pattern,
                "optimization_metadata": {
                    "waypoint_count": len(optimized_waypoints),
                    "optimization_algorithm": search_pattern,
                    "created_at": asyncio.get_event_loop().time()
                },
                "original_assignment": assignment
            }
            
            return optimized_route
        
        except Exception as e:
            logger.error(f"Error optimizing route: {e}")
            return None
    
    async def _generate_zone_waypoints(self, zone: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate waypoints for a zone"""
        waypoints = []
        
        if not zone:
            return waypoints
        
        # Calculate zone bounds
        north = zone.get("north", 37.8)
        south = zone.get("south", 37.7)
        east = zone.get("east", -122.4)
        west = zone.get("west", -122.5)
        
        # Generate grid waypoints
        lat_step = 0.0005  # ~50m spacing
        lng_step = 0.0005
        
        current_lat = south
        while current_lat <= north:
            current_lng = west
            while current_lng <= east:
                waypoints.append({
                    "lat": current_lat,
                    "lng": current_lng,
                    "alt": 50,
                    "type": "search_point",
                    "sequence": len(waypoints)
                })
                current_lng += lng_step
            current_lat += lat_step
        
        return waypoints
    
    async def _optimize_grid_pattern(self, waypoints: List[Dict[str, Any]], 
                                   zone: Dict[str, float]) -> List[Dict[str, Any]]:
        """Optimize grid search pattern"""
        if not waypoints:
            return waypoints
        
        # Sort waypoints for efficient grid traversal
        # Group by latitude, then sort by longitude within each group
        waypoints_by_lat = {}
        for wp in waypoints:
            lat = round(wp["lat"], 6)  # Round to avoid floating point issues
            if lat not in waypoints_by_lat:
                waypoints_by_lat[lat] = []
            waypoints_by_lat[lat].append(wp)
        
        # Sort latitudes
        sorted_lats = sorted(waypoints_by_lat.keys())
        
        optimized_waypoints = []
        for i, lat in enumerate(sorted_lats):
            lat_waypoints = waypoints_by_lat[lat]
            # Sort by longitude
            lat_waypoints.sort(key=lambda x: x["lng"])
            
            # Alternate direction for each row (zigzag pattern)
            if i % 2 == 1:
                lat_waypoints.reverse()
            
            optimized_waypoints.extend(lat_waypoints)
        
        # Update sequence numbers
        for i, wp in enumerate(optimized_waypoints):
            wp["sequence"] = i
        
        return optimized_waypoints
    
    async def _optimize_spiral_pattern(self, waypoints: List[Dict[str, Any]], 
                                     zone: Dict[str, float]) -> List[Dict[str, Any]]:
        """Optimize spiral search pattern"""
        if not waypoints:
            return waypoints
        
        # Calculate center point
        center_lat = (zone.get("north", 37.8) + zone.get("south", 37.7)) / 2
        center_lng = (zone.get("east", -122.4) + zone.get("west", -122.5)) / 2
        
        # Sort waypoints by distance from center
        def distance_from_center(wp):
            lat_diff = wp["lat"] - center_lat
            lng_diff = wp["lng"] - center_lng
            return math.sqrt(lat_diff**2 + lng_diff**2)
        
        optimized_waypoints = sorted(waypoints, key=distance_from_center)
        
        # Update sequence numbers
        for i, wp in enumerate(optimized_waypoints):
            wp["sequence"] = i
        
        return optimized_waypoints
    
    async def _optimize_zigzag_pattern(self, waypoints: List[Dict[str, Any]], 
                                     zone: Dict[str, float]) -> List[Dict[str, Any]]:
        """Optimize zigzag search pattern"""
        # Similar to grid but with more pronounced zigzag
        return await self._optimize_grid_pattern(waypoints, zone)
    
    def _calculate_total_distance(self, waypoints: List[Dict[str, Any]]) -> float:
        """Calculate total distance for waypoint sequence"""
        if len(waypoints) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(waypoints)):
            prev_wp = waypoints[i-1]
            curr_wp = waypoints[i]
            
            distance = self._calculate_distance(
                prev_wp["lat"], prev_wp["lng"],
                curr_wp["lat"], curr_wp["lng"]
            )
            total_distance += distance
        
        return total_distance
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters"""
        # Haversine formula
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_estimated_time(self, waypoints: List[Dict[str, Any]], speed: float) -> float:
        """Calculate estimated time for route in seconds"""
        total_distance = self._calculate_total_distance(waypoints)
        return total_distance / speed if speed > 0 else 0
    
    async def optimize_multi_drone_routes(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize routes for multiple drones to avoid conflicts"""
        optimized_assignments = []
        
        for assignment in assignments:
            optimized_route = await self._optimize_assignment_route(assignment)
            if optimized_route:
                optimized_assignments.append(optimized_route)
        
        # Check for route conflicts and adjust
        optimized_assignments = await self._resolve_route_conflicts(optimized_assignments)
        
        return optimized_assignments
    
    async def _resolve_route_conflicts(self, assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve conflicts between multiple drone routes"""
        # Simple conflict resolution - stagger start times
        for i, assignment in enumerate(assignments):
            if "start_delay" not in assignment:
                assignment["start_delay"] = i * 30  # 30 second delay between drones
        
        return assignments
    
    async def get_route_efficiency_metrics(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Get efficiency metrics for a route"""
        if assignment_id not in self.optimization_cache:
            return None
        
        route = self.optimization_cache[assignment_id]
        
        return {
            "assignment_id": assignment_id,
            "total_distance": route.get("total_distance", 0),
            "estimated_time": route.get("estimated_time", 0),
            "waypoint_count": len(route.get("waypoints", [])),
            "efficiency_score": self._calculate_efficiency_score(route)
        }
    
    def _calculate_efficiency_score(self, route: Dict[str, Any]) -> float:
        """Calculate efficiency score for a route (0-1, higher is better)"""
        waypoints = route.get("waypoints", [])
        if not waypoints:
            return 0.0
        
        # Calculate coverage efficiency
        total_distance = route.get("total_distance", 0)
        waypoint_count = len(waypoints)
        
        if total_distance == 0 or waypoint_count == 0:
            return 0.0
        
        # Efficiency based on distance per waypoint (lower is better)
        distance_per_waypoint = total_distance / waypoint_count
        max_efficient_distance = 100  # meters per waypoint
        
        efficiency = max(0, 1 - (distance_per_waypoint / max_efficient_distance))
        return min(1.0, efficiency)