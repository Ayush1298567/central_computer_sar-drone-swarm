"""
Mission Planner

Handles mission planning logic and optimization.
"""

from typing import Dict, List, Optional
import math


class MissionPlanner:
    """Service for mission planning and optimization"""

    def __init__(self):
        pass

    def calculate_search_pattern(self, center_lat: float, center_lng: float,
                               area_size_km2: float, altitude: float) -> Dict:
        """Calculate optimal search pattern for the mission area"""
        # Simple circular pattern calculation for demonstration
        radius_km = math.sqrt(area_size_km2 / math.pi)

        return {
            'pattern': 'circular',
            'center': {'lat': center_lat, 'lng': center_lng},
            'radius_km': radius_km,
            'waypoints': self._generate_circular_waypoints(center_lat, center_lng, radius_km),
            'estimated_duration': self._estimate_duration(area_size_km2, altitude)
        }

    def _generate_circular_waypoints(self, center_lat: float, center_lng: float,
                                   radius_km: float, num_points: int = 8) -> List[Dict]:
        """Generate waypoints for circular search pattern"""
        waypoints = []
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            lat_offset = radius_km * math.cos(angle) / 111.32  # Rough km to degrees conversion
            lng_offset = radius_km * math.sin(angle) / (111.32 * math.cos(math.radians(center_lat)))

            waypoints.append({
                'lat': center_lat + lat_offset,
                'lng': center_lng + lng_offset,
                'altitude': 100  # Default waypoint altitude
            })

        return waypoints

    def _estimate_duration(self, area_size_km2: float, altitude: float) -> int:
        """Estimate mission duration in minutes"""
        # Simple estimation: assume average drone speed of 10 m/s
        # Add time for altitude changes and safety margins
        base_time = (math.sqrt(area_size_km2) * 1000) / 10  # Convert km to meters, divide by speed
        altitude_time = altitude / 5  # 5 m/s climb rate
        safety_margin = base_time * 0.2  # 20% safety margin

        total_seconds = base_time + altitude_time + safety_margin
        return math.ceil(total_seconds / 60)  # Convert to minutes

    def optimize_drone_assignment(self, mission_area: float, available_drones: List[Dict]) -> List[Dict]:
        """Optimize drone assignment for mission coverage"""
        # Simple optimization: assign drones based on area coverage capability
        assignments = []

        for drone in available_drones:
            if drone.get('status') == 'online':
                # Simple assignment logic
                assignments.append({
                    'drone_id': drone['id'],
                    'assigned_area': mission_area / len([d for d in available_drones if d.get('status') == 'online'])
                })

        return assignments