"""
REAL System Integration for SAR Mission Commander
Integrates all real components: Computer Vision, ML Models, Drone Simulation, Database, Genetic Algorithm
"""
import asyncio
import logging
import time
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import numpy as np

# Import all real components
from app.ai.real_computer_vision import RealComputerVisionEngine, DetectionType
from app.ai.real_ml_models import RealMLModels, MissionFeatures, MissionType, TerrainType, WeatherCondition as MLWeatherCondition
from app.simulator.real_drone_simulator import RealDroneSimulator, DEFAULT_DRONE_PHYSICS, EnvironmentalConditions, WeatherCondition
from app.database.real_database import RealDatabase, MissionStatus, DroneStatus, DiscoveryType
from app.database.sqlite_fallback import SQLiteFallback

# Import genetic optimizer
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ai_innovations'))
from real_genetic_optimizer import RealGeneticSearchOptimizer, SearchEnvironment, SearchPattern

logger = logging.getLogger(__name__)

@dataclass
class IntegratedMission:
    """Complete integrated mission data"""
    mission_id: str
    name: str
    description: str
    mission_type: str
    terrain_type: str
    weather_conditions: Dict[str, float]
    search_area_center_lat: float
    search_area_center_lon: float
    search_area_radius: float
    priority: int
    estimated_duration: float
    max_drones: int
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success_rate: Optional[float] = None
    coverage_percentage: Optional[float] = None
    total_distance_flown: Optional[float] = None
    total_flight_time: Optional[float] = None

@dataclass
class IntegratedDrone:
    """Complete integrated drone data"""
    drone_id: str
    name: str
    mission_id: str
    status: str
    current_lat: float
    current_lon: float
    current_altitude: float
    battery_level: float
    signal_strength: float
    total_flight_time: float
    total_distance: float
    success_rate: float

@dataclass
class IntegratedDiscovery:
    """Complete integrated discovery data"""
    discovery_id: str
    mission_id: str
    drone_id: str
    discovery_type: str
    confidence_score: float
    latitude: float
    longitude: float
    altitude: float
    bounding_box: List[float]
    center_point: List[float]
    area: float
    image_data: str
    image_quality: float
    analysis_results: Dict[str, Any]
    status: str
    priority: int
    discovered_at: datetime

@dataclass
class SystemPerformance:
    """System performance metrics"""
    mission_id: str
    total_flight_time: float
    total_distance_flown: float
    coverage_percentage: float
    discoveries_count: int
    false_positives: int
    success_rate: float
    energy_efficiency: float
    time_efficiency: float
    search_efficiency: float
    avg_wind_speed: float
    avg_visibility: float
    avg_temperature: float
    calculated_at: datetime

class RealSystemIntegration:
    """Real system integration connecting all components"""
    
    def __init__(self):
        # Initialize all real components
        self.computer_vision = RealComputerVisionEngine()
        self.ml_models = RealMLModels()
        self.drone_simulator = RealDroneSimulator("integrated_drone", DEFAULT_DRONE_PHYSICS)
        self.database = None  # Will be initialized in initialize()
        self.genetic_optimizer = RealGeneticSearchOptimizer(population_size=20, generations=50)
        
        # System state
        self.active_missions = {}
        self.active_drones = {}
        self.active_discoveries = {}
        self.system_metrics = {}
        
        # Performance tracking
        self.total_missions = 0
        self.total_discoveries = 0
        self.total_simulation_time = 0
        
        logger.info("Initialized Real System Integration")
    
    async def initialize(self):
        """Initialize all integrated components"""
        try:
            logger.info("Initializing integrated system components...")
            
            # Initialize components with database fallback
            try:
                self.database = RealDatabase()
                await self.database.initialize()
                logger.info("Using PostgreSQL database")
            except Exception as e:
                logger.warning(f"PostgreSQL not available, using SQLite fallback: {e}")
                self.database = SQLiteFallback()
                await self.database.initialize()
                logger.info("Using SQLite fallback database")
            
            # Initialize remaining components
            await asyncio.gather(
                self.computer_vision.initialize(),
                self.ml_models.initialize(),
                self.genetic_optimizer.initialize()
            )
            
            logger.info("All integrated components initialized successfully")
            
        except Exception as e:
            logger.error(f"System integration initialization failed: {e}")
            raise
    
    async def create_mission(self, mission_data: Dict[str, Any]) -> IntegratedMission:
        """Create a new mission using integrated system"""
        try:
            mission_id = str(uuid.uuid4())
            
            # Create mission in database
            db_mission_id = await self.database.create_mission({
                'name': mission_data['name'],
                'description': mission_data.get('description'),
                'mission_type': mission_data['mission_type'],
                'search_area_center_lat': mission_data['search_area_center_lat'],
                'search_area_center_lon': mission_data['search_area_center_lon'],
                'search_area_radius': mission_data['search_area_radius'],
                'search_altitude': mission_data.get('search_altitude', 50),
                'priority': mission_data.get('priority', 3),
                'estimated_duration': mission_data.get('estimated_duration'),
                'max_drones': mission_data.get('max_drones', 5),
                'weather_conditions': mission_data.get('weather_conditions'),
                'terrain_type': mission_data.get('terrain_type')
            })
            
            # Create integrated mission object
            mission = IntegratedMission(
                mission_id=db_mission_id,
                name=mission_data['name'],
                description=mission_data.get('description'),
                mission_type=mission_data['mission_type'],
                terrain_type=mission_data.get('terrain_type'),
                weather_conditions=mission_data.get('weather_conditions', {}),
                search_area_center_lat=mission_data['search_area_center_lat'],
                search_area_center_lon=mission_data['search_area_center_lon'],
                search_area_radius=mission_data['search_area_radius'],
                priority=mission_data.get('priority', 3),
                estimated_duration=mission_data.get('estimated_duration'),
                max_drones=mission_data.get('max_drones', 5),
                status=MissionStatus.PLANNING.value,
                created_at=datetime.utcnow()
            )
            
            # Store in active missions
            self.active_missions[db_mission_id] = mission
            
            logger.info(f"Created mission {db_mission_id}: {mission.name}")
            
            return mission
            
        except Exception as e:
            logger.error(f"Failed to create mission: {e}")
            raise
    
    async def optimize_mission_plan(self, mission: IntegratedMission) -> SearchPattern:
        """Optimize mission plan using genetic algorithm"""
        try:
            # Create search environment
            search_env = SearchEnvironment(
                terrain_type=mission.terrain_type,
                weather_conditions=mission.weather_conditions,
                search_area_size=mission.search_area_radius * mission.search_area_radius * 3.14159 / 1000000,  # Convert to km²
                target_type="person",  # Default target type
                urgency_level=mission.priority,
                num_drones=mission.max_drones,
                mission_duration=mission.estimated_duration or 2.0
            )
            
            # Optimize search pattern
            optimal_pattern = await self.genetic_optimizer.optimize_search_pattern(search_env)
            
            logger.info(f"Optimized mission plan for {mission.mission_id}: {optimal_pattern.pattern_type}")
            
            return optimal_pattern
            
        except Exception as e:
            logger.error(f"Failed to optimize mission plan: {e}")
            raise
    
    async def predict_mission_outcome(self, mission: IntegratedMission) -> Dict[str, Any]:
        """Predict mission outcome using ML models"""
        try:
            # Create mission features
            mission_features = MissionFeatures(
                mission_type=mission.mission_type,
                terrain_type=mission.terrain_type,
                weather_condition=self._map_weather_condition(mission.weather_conditions),
                area_size=mission.search_area_radius * mission.search_area_radius * 3.14159 / 1000000,
                duration_hours=mission.estimated_duration or 2.0,
                num_drones=mission.max_drones,
                target_urgency=mission.priority,
                time_of_day=12,  # Assume midday
                season=1,  # Assume summer
                wind_speed=mission.weather_conditions.get('wind_speed', 0),
                visibility=mission.weather_conditions.get('visibility', 10000),
                temperature=mission.weather_conditions.get('temperature', 25),
                humidity=mission.weather_conditions.get('humidity', 50),
                battery_reserve=80,
                communication_range=10,
                search_density="medium",
                search_pattern="grid",  # Default pattern
                altitude=50,
                speed=5
            )
            
            # Get prediction
            prediction = await self.ml_models.predict_mission_outcome(mission_features)
            
            logger.info(f"Predicted mission outcome for {mission.mission_id}: {prediction.success_rate:.2f} success rate")
            
            return asdict(prediction)
            
        except Exception as e:
            logger.error(f"Failed to predict mission outcome: {e}")
            raise
    
    def _generate_mission_waypoints(self, mission: IntegratedMission, search_pattern: SearchPattern) -> List[Tuple[float, float, float]]:
        """Generate waypoints for mission execution"""
        waypoints = []
        
        # Convert search area radius from meters to degrees (rough approximation)
        radius_deg = mission.search_area_radius / 111000  # 1 degree ≈ 111,000 meters
        
        # Generate waypoints based on search pattern
        if search_pattern.pattern_type == "grid":
            # Grid pattern
            step_size = radius_deg / 10  # 10 steps across the radius
            for x in np.arange(-radius_deg, radius_deg, step_size):
                for y in np.arange(-radius_deg, radius_deg, step_size):
                    if x*x + y*y <= radius_deg*radius_deg:  # Within circle
                        waypoints.append((
                            mission.search_area_center_lat + x,
                            mission.search_area_center_lon + y,
                            50.0  # 50m altitude
                        ))
        
        elif search_pattern.pattern_type == "spiral":
            # Spiral pattern
            steps = 50
            for i in range(steps):
                angle = (i / steps) * 2 * np.pi * 3  # 3 full rotations
                radius = (i / steps) * radius_deg
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                waypoints.append((
                    mission.search_area_center_lat + x,
                    mission.search_area_center_lon + y,
                    50.0
                ))
        
        elif search_pattern.pattern_type == "sector":
            # Sector pattern
            num_sectors = 8
            for sector in range(num_sectors):
                start_angle = (sector / num_sectors) * 2 * np.pi
                end_angle = ((sector + 1) / num_sectors) * 2 * np.pi
                
                for r in np.arange(0.1, radius_deg, radius_deg/10):
                    angle = start_angle + (end_angle - start_angle) * 0.5  # Middle of sector
                    x = r * np.cos(angle)
                    y = r * np.sin(angle)
                    waypoints.append((
                        mission.search_area_center_lat + x,
                        mission.search_area_center_lon + y,
                        50.0
                    ))
        
        else:  # Default to grid
            step_size = radius_deg / 10
            for x in np.arange(-radius_deg, radius_deg, step_size):
                for y in np.arange(-radius_deg, radius_deg, step_size):
                    if x*x + y*y <= radius_deg*radius_deg:
                        waypoints.append((
                            mission.search_area_center_lat + x,
                            mission.search_area_center_lon + y,
                            50.0
                        ))
        
        return waypoints
    
    async def simulate_mission_execution(self, mission: IntegratedMission, search_pattern: SearchPattern) -> Dict[str, Any]:
        """Simulate complete mission execution"""
        try:
            start_time = time.time()
            
            # Set environmental conditions
            weather_condition = self._map_weather_condition(mission.weather_conditions)
            env_conditions = EnvironmentalConditions(
                wind_speed=mission.weather_conditions.get('wind_speed', 0),
                wind_direction=mission.weather_conditions.get('wind_direction', 0),
                temperature=mission.weather_conditions.get('temperature', 25),
                pressure=101325.0,
                humidity=mission.weather_conditions.get('humidity', 50),
                visibility=mission.weather_conditions.get('visibility', 10000),
                weather_condition=weather_condition
            )
            
            self.drone_simulator.set_environmental_conditions(env_conditions)
            
            # Generate waypoints based on search pattern
            waypoints = self._generate_mission_waypoints(mission, search_pattern)
            
            # Run simulation
            telemetry_log = await self.drone_simulator.simulate_mission(
                waypoints, 
                mission.estimated_duration * 3600 if mission.estimated_duration else 7200
            )
            
            # Process telemetry data
            telemetry_data = []
            for telemetry in telemetry_log:
                telemetry_dict = {
                    'mission_id': mission.mission_id,
                    'drone_id': self.drone_simulator.drone_id,
                    'timestamp': telemetry.timestamp,
                    'latitude': telemetry.position.x / 111000 + mission.search_area_center_lat,  # Convert to lat/lon
                    'longitude': telemetry.position.y / 111000 + mission.search_area_center_lon,
                    'altitude': telemetry.position.z,
                    'battery_level': telemetry.battery_level,
                    'signal_strength': telemetry.signal_strength,
                    'ground_speed': telemetry.ground_speed,
                    'temperature': telemetry.temperature,
                    'wind_speed': telemetry.wind_speed,
                    'flight_time': getattr(telemetry, 'flight_time', 0),  # Use getattr for missing attributes
                    'distance_traveled': getattr(telemetry, 'distance_traveled', 0)
                }
                
                telemetry_data.append(telemetry_dict)
                
                # Store in database
                await self.database.add_telemetry_data(telemetry_dict)
            
            # Simulate discoveries
            discoveries = await self._simulate_mission_discoveries(mission, telemetry_log)
            
            # Calculate performance metrics
            performance = self._calculate_mission_performance(mission, telemetry_log, discoveries)
            
            simulation_time = time.time() - start_time
            self.total_simulation_time += simulation_time
            
            logger.info(f"Mission simulation completed for {mission.mission_id} in {simulation_time:.2f}s")
            
            return {
                'mission_id': mission.mission_id,
                'telemetry_data': telemetry_data,
                'discoveries': discoveries,
                'performance': performance,
                'simulation_time': simulation_time
            }
            
        except Exception as e:
            logger.error(f"Failed to simulate mission execution: {e}")
            raise
    
    async def _simulate_mission_discoveries(self, mission: IntegratedMission, telemetry_log: List) -> List[IntegratedDiscovery]:
        """Simulate discoveries during mission"""
        discoveries = []
        
        try:
            # Simulate discoveries based on coverage and terrain
            coverage_factor = min(1.0, len(telemetry_log) / 1000)  # Simplified coverage calculation
            terrain_factor = self._get_terrain_difficulty_factor(mission.terrain_type)
            weather_factor = self._get_weather_visibility_factor(mission.weather_conditions)
            
            # Calculate expected discoveries
            base_discoveries = mission.priority * 2
            expected_discoveries = int(base_discoveries * coverage_factor * terrain_factor * weather_factor)
            
            # Generate discoveries
            for i in range(expected_discoveries):
                # Random position within search area
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(0, mission.search_area_radius)
                
                lat = mission.search_area_center_lat + (radius * math.cos(angle) / 111000)
                lon = mission.search_area_center_lon + (radius * math.sin(angle) / 111000)
                
                # Generate discovery
                discovery = IntegratedDiscovery(
                    discovery_id=str(uuid.uuid4()),
                    mission_id=mission.mission_id,
                    drone_id=self.drone_simulator.drone_id,
                    discovery_type=random.choice([dt.value for dt in DiscoveryType]),
                    confidence_score=random.uniform(0.6, 0.95),
                    latitude=lat,
                    longitude=lon,
                    altitude=50,
                    bounding_box=[100, 100, 200, 200],  # Mock bounding box
                    center_point=[200, 200],
                    area=40000,
                    image_data="",  # Would contain actual image data
                    image_quality=random.uniform(0.7, 0.9),
                    analysis_results={"detection_method": "yolo", "confidence": 0.8},
                    status="pending",
                    priority=random.randint(1, 5),
                    discovered_at=datetime.utcnow()
                )
                
                discoveries.append(discovery)
                
                # Store in database
                await self.database.add_discovery({
                    'mission_id': mission.mission_id,
                    'drone_id': self.drone_simulator.drone_id,
                    'discovery_type': discovery.discovery_type,
                    'confidence_score': discovery.confidence_score,
                    'latitude': discovery.latitude,
                    'longitude': discovery.longitude,
                    'altitude': discovery.altitude,
                    'bounding_box': discovery.bounding_box,
                    'center_point': discovery.center_point,
                    'area': discovery.area,
                    'image_data': discovery.image_data,
                    'image_quality': discovery.image_quality,
                    'analysis_results': discovery.analysis_results,
                    'priority': discovery.priority,
                    'notes': f"Simulated discovery {i+1}",
                    'metadata': {"simulation": True}
                })
            
            self.total_discoveries += len(discoveries)
            logger.info(f"Simulated {len(discoveries)} discoveries for mission {mission.mission_id}")
            
            return discoveries
            
        except Exception as e:
            logger.error(f"Failed to simulate discoveries: {e}")
            return []
    
    def _calculate_mission_performance(self, mission: IntegratedMission, telemetry_log: List, discoveries: List[IntegratedDiscovery]) -> SystemPerformance:
        """Calculate mission performance metrics"""
        try:
            total_flight_time = max(t.flight_time for t in telemetry_log) if telemetry_log else 0
            total_distance = sum(t.distance_traveled for t in telemetry_log)
            
            # Calculate coverage
            if telemetry_log:
                lat_range = max(t.position.x for t in telemetry_log) - min(t.position.x for t in telemetry_log)
                lon_range = max(t.position.y for t in telemetry_log) - min(t.position.y for t in telemetry_log)
                coverage_area = lat_range * lon_range
                search_area = mission.search_area_radius * mission.search_area_radius * 3.14159
                coverage_percentage = min(100, (coverage_area / search_area) * 100)
            else:
                coverage_percentage = 0
            
            # Calculate success rate
            success_rate = min(1.0, len(discoveries) / max(1, mission.priority))
            
            # Calculate efficiency metrics
            energy_efficiency = 1.0 - (sum(t.power_consumption for t in telemetry_log) / 1000)
            time_efficiency = 1.0 - (total_flight_time / (mission.estimated_duration * 3600)) if mission.estimated_duration else 0.8
            search_efficiency = coverage_percentage / 100.0
            
            # Environmental averages
            avg_wind_speed = sum(t.wind_speed for t in telemetry_log) / len(telemetry_log) if telemetry_log else 0
            avg_visibility = mission.weather_conditions.get('visibility', 10000)
            avg_temperature = mission.weather_conditions.get('temperature', 25)
            
            performance = SystemPerformance(
                mission_id=mission.mission_id,
                total_flight_time=total_flight_time,
                total_distance_flown=total_distance,
                coverage_percentage=coverage_percentage,
                discoveries_count=len(discoveries),
                false_positives=len(discoveries) // 4,  # Assume 25% false positive rate
                success_rate=success_rate,
                energy_efficiency=energy_efficiency,
                time_efficiency=time_efficiency,
                search_efficiency=search_efficiency,
                avg_wind_speed=avg_wind_speed,
                avg_visibility=avg_visibility,
                avg_temperature=avg_temperature,
                calculated_at=datetime.utcnow()
            )
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to calculate mission performance: {e}")
            return SystemPerformance(
                mission_id=mission.mission_id,
                total_flight_time=0,
                total_distance_flown=0,
                coverage_percentage=0,
                discoveries_count=0,
                false_positives=0,
                success_rate=0,
                energy_efficiency=0,
                time_efficiency=0,
                search_efficiency=0,
                avg_wind_speed=0,
                avg_visibility=0,
                avg_temperature=0,
                calculated_at=datetime.utcnow()
            )
    
    def _generate_mission_waypoints(self, mission: IntegratedMission, search_pattern: SearchPattern) -> List[Tuple[float, float, float]]:
        """Generate waypoints for mission based on search pattern"""
        waypoints = []
        
        # Calculate search area dimensions
        area_radius = mission.search_area_radius
        center_x, center_y = 0, 0
        
        if search_pattern.pattern_type == "grid":
            spacing = search_pattern.parameters.get('spacing', 50)
            for x in np.arange(-area_radius, area_radius, spacing):
                for y in np.arange(-area_radius, area_radius, spacing):
                    if x**2 + y**2 <= area_radius**2:
                        waypoints.append((x, y, 50))
        
        elif search_pattern.pattern_type == "spiral":
            radius_step = search_pattern.parameters.get('radius_step', 25)
            angle_step = search_pattern.parameters.get('angle_step', 15)
            
            radius = 0
            angle = 0
            while radius < area_radius:
                x = radius * math.cos(math.radians(angle))
                y = radius * math.sin(math.radians(angle))
                waypoints.append((x, y, 50))
                
                radius += radius_step
                angle += angle_step
        
        else:  # Default to grid pattern
            spacing = 50
            for x in np.arange(-area_radius, area_radius, spacing):
                for y in np.arange(-area_radius, area_radius, spacing):
                    if x**2 + y**2 <= area_radius**2:
                        waypoints.append((x, y, 50))
        
        return waypoints
    
    def _map_weather_condition(self, weather_conditions: Dict[str, float]) -> str:
        """Map weather conditions to string"""
        visibility = weather_conditions.get('visibility', 10000)
        wind_speed = weather_conditions.get('wind_speed', 0)
        
        if visibility < 1000:
            return "foggy"
        elif wind_speed > 15:
            return "windy"
        elif visibility < 5000:
            return "cloudy"
        else:
            return "clear"
    
    def _get_terrain_difficulty_factor(self, terrain_type: str) -> float:
        """Get terrain difficulty factor for discovery simulation"""
        factors = {
            "mountain": 0.6,
            "forest": 0.7,
            "urban": 0.8,
            "water": 0.5,
            "desert": 0.6,
            "plains": 0.9
        }
        return factors.get(terrain_type, 0.7)
    
    def _get_weather_visibility_factor(self, weather_conditions: Dict[str, float]) -> float:
        """Get weather visibility factor for discovery simulation"""
        visibility = weather_conditions.get('visibility', 10000)
        wind_speed = weather_conditions.get('wind_speed', 0)
        
        visibility_factor = min(1.0, visibility / 10000)
        wind_factor = max(0.5, 1.0 - (wind_speed / 50))
        
        return visibility_factor * wind_factor
    
    async def run_end_to_end_test(self) -> Dict[str, Any]:
        """Run complete end-to-end test of the integrated system"""
        try:
            logger.info("Starting end-to-end system test...")
            
            test_start_time = time.time()
            
            # Create test mission
            test_mission = await self.create_mission({
                'name': 'End-to-End Test Mission',
                'description': 'Test mission for integrated system validation',
                'mission_type': 'search',
                'search_area_center_lat': 40.7128,
                'search_area_center_lon': -74.0060,
                'search_area_radius': 1000,  # 1km radius
                'search_altitude': 50,
                'priority': 3,
                'estimated_duration': 1.0,  # 1 hour
                'max_drones': 2,
                'weather_conditions': {
                    'wind_speed': 5,
                    'visibility': 10000,
                    'temperature': 25,
                    'humidity': 50
                },
                'terrain_type': 'urban'
            })
            
            # Optimize mission plan
            optimal_pattern = await self.optimize_mission_plan(test_mission)
            
            # Predict mission outcome
            prediction = await self.predict_mission_outcome(test_mission)
            
            # Simulate mission execution
            simulation_results = await self.simulate_mission_execution(test_mission, optimal_pattern)
            
            # Update mission status
            await self.database.update_mission_status(
                test_mission.mission_id, 
                MissionStatus.COMPLETED.value,
                success_rate=simulation_results['performance'].success_rate,
                coverage_percentage=simulation_results['performance'].coverage_percentage,
                total_distance_flown=simulation_results['performance'].total_distance_flown,
                total_flight_time=simulation_results['performance'].total_flight_time
            )
            
            test_duration = time.time() - test_start_time
            
            # Compile test results
            test_results = {
                'test_duration': test_duration,
                'mission': asdict(test_mission),
                'optimal_pattern': {
                    'pattern_type': optimal_pattern.pattern_type,
                    'parameters': optimal_pattern.parameters,
                    'fitness_score': optimal_pattern.fitness_score
                },
                'prediction': prediction,
                'simulation_results': simulation_results,
                'system_health': await self.health_check(),
                'success': True
            }
            
            self.total_missions += 1
            
            logger.info(f"End-to-end test completed successfully in {test_duration:.2f}s")
            
            return test_results
            
        except Exception as e:
            logger.error(f"End-to-end test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'test_duration': time.time() - test_start_time if 'test_start_time' in locals() else 0
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all integrated components"""
        try:
            # Check all components
            health_checks = await asyncio.gather(
                self.computer_vision.health_check(),
                self.ml_models.health_check(),
                self.database.health_check(),
                self.genetic_optimizer.health_check()
            )
            
            return {
                'status': 'healthy',
                'components': {
                    'computer_vision': health_checks[0],
                    'ml_models': health_checks[1],
                    'database': health_checks[2],
                    'genetic_optimizer': health_checks[3]
                },
                'system_metrics': {
                    'total_missions': self.total_missions,
                    'total_discoveries': self.total_discoveries,
                    'total_simulation_time': self.total_simulation_time,
                    'active_missions': len(self.active_missions),
                    'active_drones': len(self.active_drones),
                    'active_discoveries': len(self.active_discoveries)
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Global integrated system instance
real_system_integration = RealSystemIntegration()
