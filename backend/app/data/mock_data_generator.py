"""
Mock Data Generator for SAR Drone System Testing
Generates realistic telemetry, mission, and discovery data for development and testing
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np
import json
import math
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class GPSPoint:
    """GPS coordinate with timestamp"""
    lat: float
    lng: float
    alt: float
    timestamp: datetime
    accuracy: float = 1.0

@dataclass
class DroneTelemetry:
    """Complete drone telemetry data"""
    drone_id: str
    timestamp: datetime
    position: GPSPoint
    attitude: Dict[str, float]  # roll, pitch, yaw
    velocity: Dict[str, float]  # x, y, z
    battery_level: float
    signal_strength: int
    flight_mode: str
    mission_id: str

@dataclass
class MissionData:
    """Mission configuration and parameters"""
    mission_id: str
    mission_type: str
    search_area: List[GPSPoint]
    terrain_type: str
    weather_conditions: Dict[str, Any]
    search_pattern: str
    drone_count: int
    start_time: datetime
    duration_hours: float

class MockDataGenerator:
    """Generate realistic mock data for SAR system testing"""
    
    def __init__(self):
        # Real-world SAR mission scenarios
        self.mission_scenarios = [
            {
                "name": "Mountain Rescue",
                "terrain_type": "mountain",
                "search_pattern": "spiral",
                "weather": {"wind_speed": 12.5, "visibility": 8.0, "temperature": -5.0},
                "search_area": "mountain_region"
            },
            {
                "name": "Forest Search",
                "terrain_type": "forest", 
                "search_pattern": "grid",
                "weather": {"wind_speed": 3.2, "visibility": 15.0, "temperature": 18.0},
                "search_area": "forest_region"
            },
            {
                "name": "Urban Search",
                "terrain_type": "urban",
                "search_pattern": "sector",
                "weather": {"wind_speed": 8.1, "visibility": 10.0, "temperature": 22.0},
                "search_area": "urban_region"
            },
            {
                "name": "Water Rescue",
                "terrain_type": "water",
                "search_pattern": "lawnmower",
                "weather": {"wind_speed": 15.8, "visibility": 12.0, "temperature": 16.0},
                "search_area": "water_region"
            }
        ]
        
        # Real geographic regions for testing
        self.search_regions = {
            "mountain_region": {
                "center": (46.5197, 6.6323),  # Swiss Alps
                "radius": 0.05,  # ~5km radius
                "elevation_range": (1000, 3000)
            },
            "forest_region": {
                "center": (47.3769, 8.5417),  # Swiss forest
                "radius": 0.03,
                "elevation_range": (400, 800)
            },
            "urban_region": {
                "center": (47.3769, 8.5417),  # Zurich city
                "radius": 0.02,
                "elevation_range": (400, 500)
            },
            "water_region": {
                "center": (47.3667, 8.5333),  # Lake Zurich
                "radius": 0.04,
                "elevation_range": (400, 420)
            }
        }
        
        # Drone specifications
        self.drone_specs = {
            "battery_capacity": 100,  # %
            "max_flight_time": 25,  # minutes
            "max_speed": 15,  # m/s
            "operating_altitude": (50, 120),  # meters
            "signal_range": 2000  # meters
        }
    
    def generate_mission(self, scenario_name: str = None) -> MissionData:
        """Generate a realistic SAR mission"""
        if not scenario_name:
            scenario_name = random.choice(self.mission_scenarios)["name"]
        
        scenario = next((s for s in self.mission_scenarios if s["name"] == scenario_name), self.mission_scenarios[0])
        
        mission_id = f"mission_{uuid.uuid4().hex[:8]}"
        region_info = self.search_regions[scenario["search_area"]]
        
        # Generate search area polygon
        search_area = self._generate_search_area_polygon(
            region_info["center"],
            region_info["radius"],
            scenario["search_pattern"]
        )
        
        return MissionData(
            mission_id=mission_id,
            mission_type="search_and_rescue",
            search_area=search_area,
            terrain_type=scenario["terrain_type"],
            weather_conditions=scenario["weather"],
            search_pattern=scenario["search_pattern"],
            drone_count=random.randint(2, 6),
            start_time=datetime.utcnow(),
            duration_hours=random.uniform(2.0, 8.0)
        )
    
    def _generate_search_area_polygon(self, center: Tuple[float, float], radius: float, pattern: str) -> List[GPSPoint]:
        """Generate search area polygon based on pattern"""
        lat_center, lng_center = center
        points = []
        
        if pattern == "grid":
            # Rectangular grid pattern
            for i in range(5):
                for j in range(5):
                    lat = lat_center + (i - 2) * radius * 0.2
                    lng = lng_center + (j - 2) * radius * 0.2
                    points.append(GPSPoint(lat, lng, 100.0, datetime.utcnow()))
        
        elif pattern == "spiral":
            # Spiral pattern from center
            for i in range(20):
                angle = i * 0.3
                distance = min(i * 0.01, radius)
                lat = lat_center + distance * math.cos(angle)
                lng = lng_center + distance * math.sin(angle)
                points.append(GPSPoint(lat, lng, 100.0, datetime.utcnow()))
        
        elif pattern == "sector":
            # Sector-based pattern
            for sector in range(6):
                for i in range(4):
                    angle = sector * math.pi / 3 + i * 0.1
                    distance = (i + 1) * radius * 0.2
                    lat = lat_center + distance * math.cos(angle)
                    lng = lng_center + distance * math.sin(angle)
                    points.append(GPSPoint(lat, lng, 100.0, datetime.utcnow()))
        
        else:  # lawnmower or default
            # Lawnmower pattern
            for i in range(8):
                for j in range(3):
                    lat = lat_center + (i - 4) * radius * 0.1
                    lng = lng_center + (j - 1) * radius * 0.3
                    points.append(GPSPoint(lat, lng, 100.0, datetime.utcnow()))
        
        return points
    
    def generate_telemetry_stream(self, mission: MissionData, drone_count: int = None, duration_minutes: int = 30) -> List[DroneTelemetry]:
        """Generate realistic telemetry stream for mission"""
        if drone_count is None:
            drone_count = mission.drone_count
        
        telemetry_data = []
        start_time = mission.start_time
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Generate telemetry for each drone
        for drone_idx in range(drone_count):
            drone_id = f"drone_{drone_idx + 1:02d}"
            
            # Generate flight path for this drone
            flight_path = self._generate_flight_path(mission, drone_idx, duration_minutes)
            
            current_time = start_time
            step_seconds = 2  # Telemetry every 2 seconds
            
            while current_time < end_time:
                # Find closest point in flight path
                path_point = self._get_path_point_at_time(flight_path, current_time, start_time)
                
                # Add realistic variations
                telemetry = self._add_telemetry_variations(
                    drone_id, current_time, path_point, mission
                )
                
                telemetry_data.append(telemetry)
                current_time += timedelta(seconds=step_seconds)
        
        return telemetry_data
    
    def _generate_flight_path(self, mission: MissionData, drone_idx: int, duration_minutes: int) -> List[GPSPoint]:
        """Generate realistic flight path based on search pattern"""
        region_info = self.search_regions[mission.search_area if hasattr(mission, 'search_area') else 'forest_region']
        lat_center, lng_center = region_info["center"]
        radius = region_info["radius"]
        
        path_points = []
        start_time = mission.start_time
        
        # Generate path based on search pattern
        if mission.search_pattern == "grid":
            path_points = self._generate_grid_path(lat_center, lng_center, radius, duration_minutes, start_time, drone_idx)
        elif mission.search_pattern == "spiral":
            path_points = self._generate_spiral_path(lat_center, lng_center, radius, duration_minutes, start_time)
        elif mission.search_pattern == "sector":
            path_points = self._generate_sector_path(lat_center, lng_center, radius, duration_minutes, start_time, drone_idx)
        else:  # lawnmower
            path_points = self._generate_lawnmower_path(lat_center, lng_center, radius, duration_minutes, start_time, drone_idx)
        
        return path_points
    
    def _generate_grid_path(self, lat_center: float, lng_center: float, radius: float, duration_minutes: int, start_time: datetime, drone_idx: int) -> List[GPSPoint]:
        """Generate grid search pattern path"""
        points = []
        grid_size = 5
        time_per_point = (duration_minutes * 60) / (grid_size * grid_size)
        
        # Offset for multiple drones
        drone_offset = drone_idx * 0.01
        
        for row in range(grid_size):
            for col in range(grid_size):
                lat = lat_center + (row - grid_size//2) * radius * 0.4 + drone_offset
                lng = lng_center + (col - grid_size//2) * radius * 0.4 + drone_offset
                alt = random.uniform(80, 120)
                
                timestamp = start_time + timedelta(seconds=len(points) * time_per_point)
                points.append(GPSPoint(lat, lng, alt, timestamp))
        
        return points
    
    def _generate_spiral_path(self, lat_center: float, lng_center: float, radius: float, duration_minutes: int, start_time: datetime) -> List[GPSPoint]:
        """Generate spiral search pattern path"""
        points = []
        total_points = duration_minutes * 30  # 2-second intervals
        max_radius = radius * 0.8
        
        for i in range(total_points):
            progress = i / total_points
            angle = progress * 8 * math.pi  # Multiple spirals
            distance = progress * max_radius
            
            lat = lat_center + distance * math.cos(angle)
            lng = lng_center + distance * math.sin(angle)
            alt = random.uniform(80, 120)
            
            timestamp = start_time + timedelta(seconds=i * 2)
            points.append(GPSPoint(lat, lng, alt, timestamp))
        
        return points
    
    def _generate_sector_path(self, lat_center: float, lng_center: float, radius: float, duration_minutes: int, start_time: datetime, drone_idx: int) -> List[GPSPoint]:
        """Generate sector search pattern path"""
        points = []
        sectors = 6
        sector_size = duration_minutes / sectors
        drone_sector = drone_idx % sectors
        
        for i in range(int(sector_size * 30)):  # 2-second intervals
            progress = i / (sector_size * 30)
            angle = (drone_sector + progress) * math.pi / 3
            distance = progress * radius * 0.8
            
            lat = lat_center + distance * math.cos(angle)
            lng = lng_center + distance * math.sin(angle)
            alt = random.uniform(80, 120)
            
            timestamp = start_time + timedelta(seconds=i * 2)
            points.append(GPSPoint(lat, lng, alt, timestamp))
        
        return points
    
    def _generate_lawnmower_path(self, lat_center: float, lng_center: float, radius: float, duration_minutes: int, start_time: datetime, drone_idx: int) -> List[GPSPoint]:
        """Generate lawnmower search pattern path"""
        points = []
        rows = 8
        time_per_row = (duration_minutes * 60) / rows
        
        # Offset for multiple drones
        drone_offset = drone_idx * 0.02
        
        for row in range(rows):
            for col in range(10):  # Points per row
                lat = lat_center + (row - rows//2) * radius * 0.3 + drone_offset
                lng = lng_center + (col - 5) * radius * 0.2
                alt = random.uniform(80, 120)
                
                timestamp = start_time + timedelta(seconds=(row * time_per_row + col * time_per_row / 10))
                points.append(GPSPoint(lat, lng, alt, timestamp))
        
        return points
    
    def _get_path_point_at_time(self, flight_path: List[GPSPoint], current_time: datetime, start_time: datetime) -> GPSPoint:
        """Get interpolated path point at specific time"""
        elapsed_seconds = (current_time - start_time).total_seconds()
        
        # Find closest points for interpolation
        if not flight_path:
            return GPSPoint(0, 0, 100, current_time)
        
        # Simple linear interpolation
        total_duration = (flight_path[-1].timestamp - start_time).total_seconds()
        progress = min(elapsed_seconds / total_duration, 1.0) if total_duration > 0 else 0.0
        
        point_index = progress * (len(flight_path) - 1)
        lower_idx = int(point_index)
        upper_idx = min(lower_idx + 1, len(flight_path) - 1)
        
        if lower_idx == upper_idx:
            return flight_path[lower_idx]
        
        # Interpolate between points
        weight = point_index - lower_idx
        lower_point = flight_path[lower_idx]
        upper_point = flight_path[upper_idx]
        
        return GPSPoint(
            lat=lower_point.lat + weight * (upper_point.lat - lower_point.lat),
            lng=lower_point.lng + weight * (upper_point.lng - lower_point.lng),
            alt=lower_point.alt + weight * (upper_point.alt - lower_point.alt),
            timestamp=current_time
        )
    
    def _add_telemetry_variations(self, drone_id: str, timestamp: datetime, position: GPSPoint, mission: MissionData) -> DroneTelemetry:
        """Add realistic variations to telemetry data"""
        # Add GPS noise
        lat_noise = random.gauss(0, 0.0001)  # ~10m accuracy
        lng_noise = random.gauss(0, 0.0001)
        alt_noise = random.gauss(0, 2.0)  # ~2m altitude accuracy
        
        # Calculate battery consumption over time
        mission_duration = (timestamp - mission.start_time).total_seconds() / 3600  # hours
        battery_drain_rate = 4.0  # % per hour
        battery_level = max(100 - (mission_duration * battery_drain_rate), 10)
        
        # Add battery variations
        battery_level += random.gauss(0, 2.0)
        battery_level = max(min(battery_level, 100), 0)
        
        # Calculate signal strength based on distance from center
        region_center = self.search_regions.get(mission.search_area if hasattr(mission, 'search_area') else 'forest_region', {}).get('center', (47.3769, 8.5417))
        distance = self._calculate_distance(position.lat, position.lng, region_center[0], region_center[1])
        max_distance = 2000  # meters
        signal_strength = max(100 - (distance / max_distance * 80), 20)
        signal_strength += random.gauss(0, 5)
        signal_strength = max(min(signal_strength, 100), 10)
        
        # Generate attitude data
        attitude = {
            "roll": random.gauss(0, 5),  # degrees
            "pitch": random.gauss(0, 5),
            "yaw": random.uniform(0, 360)
        }
        
        # Generate velocity data
        velocity = {
            "x": random.gauss(0, 2),  # m/s
            "y": random.gauss(0, 2),
            "z": random.gauss(0, 0.5)
        }
        
        # Determine flight mode
        flight_modes = ["AUTO", "GUIDED", "STABILIZE"]
        flight_mode = random.choice(flight_modes)
        
        return DroneTelemetry(
            drone_id=drone_id,
            timestamp=timestamp,
            position=GPSPoint(
                lat=position.lat + lat_noise,
                lng=position.lng + lng_noise,
                alt=position.alt + alt_noise,
                timestamp=timestamp,
                accuracy=random.uniform(0.5, 2.0)
            ),
            attitude=attitude,
            velocity=velocity,
            battery_level=battery_level,
            signal_strength=int(signal_strength),
            flight_mode=flight_mode,
            mission_id=mission.mission_id
        )
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two GPS points in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def generate_discovery_data(self, mission: MissionData, telemetry_data: List[DroneTelemetry]) -> List[Dict[str, Any]]:
        """Generate realistic discovery data based on telemetry"""
        discoveries = []
        
        # Randomly place discoveries along flight paths
        num_discoveries = random.randint(0, 3)
        
        for i in range(num_discoveries):
            # Select random telemetry point as discovery location
            telemetry_point = random.choice(telemetry_data)
            
            discovery_types = ["person", "vehicle", "structure", "debris", "unknown"]
            discovery_type = random.choice(discovery_types)
            
            # Generate confidence based on discovery type and conditions
            base_confidence = {
                "person": 0.75,
                "vehicle": 0.85,
                "structure": 0.90,
                "debris": 0.60,
                "unknown": 0.45
            }.get(discovery_type, 0.50)
            
            # Adjust confidence based on weather conditions
            weather_factor = 1.0
            if mission.weather_conditions.get("visibility", 10) < 5:
                weather_factor *= 0.8
            if mission.weather_conditions.get("wind_speed", 0) > 15:
                weather_factor *= 0.9
            
            confidence = min(base_confidence * weather_factor, 1.0)
            
            discovery = {
                "discovery_id": f"discovery_{uuid.uuid4().hex[:8]}",
                "mission_id": mission.mission_id,
                "drone_id": telemetry_point.drone_id,
                "discovery_type": discovery_type,
                "confidence": confidence,
                "position": {
                    "lat": telemetry_point.position.lat + random.gauss(0, 0.0005),
                    "lng": telemetry_point.position.lng + random.gauss(0, 0.0005),
                    "alt": telemetry_point.position.alt
                },
                "timestamp": telemetry_point.timestamp,
                "metadata": {
                    "detection_method": "computer_vision",
                    "image_quality": random.uniform(0.6, 0.95),
                    "weather_conditions": mission.weather_conditions,
                    "terrain_type": mission.terrain_type
                },
                "priority": "high" if discovery_type == "person" and confidence > 0.7 else "medium"
            }
            
            discoveries.append(discovery)
        
        return discoveries
    
    def export_to_json(self, data: Any, filename: str):
        """Export data to JSON file"""
        try:
            # Convert dataclasses to dict
            if isinstance(data, list):
                json_data = []
                for item in data:
                    if hasattr(item, '__dict__'):
                        json_data.append(self._dataclass_to_dict(item))
                    else:
                        json_data.append(item)
            else:
                json_data = self._dataclass_to_dict(data)
            
            with open(filename, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            logger.info(f"Exported data to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
    
    def _dataclass_to_dict(self, obj):
        """Convert dataclass to dictionary recursively"""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if hasattr(value, '__dict__'):
                    result[key] = self._dataclass_to_dict(value)
                elif isinstance(value, list):
                    result[key] = [self._dataclass_to_dict(item) if hasattr(item, '__dict__') else item for item in value]
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
            return result
        return obj

# Global mock data generator instance
mock_data_generator = MockDataGenerator()

# Convenience functions for easy data generation
async def generate_test_mission(scenario: str = None) -> MissionData:
    """Generate a test mission"""
    return mock_data_generator.generate_mission(scenario)

async def generate_test_telemetry(mission: MissionData, duration_minutes: int = 30) -> List[DroneTelemetry]:
    """Generate test telemetry data"""
    return mock_data_generator.generate_telemetry_stream(mission, duration_minutes=duration_minutes)

async def generate_test_discoveries(mission: MissionData, telemetry: List[DroneTelemetry]) -> List[Dict[str, Any]]:
    """Generate test discovery data"""
    return mock_data_generator.generate_discovery_data(mission, telemetry)
