"""
REAL Genetic Algorithm for SAR Search Pattern Optimization
Connected to actual drone simulation with real fitness evaluation
"""
import numpy as np
import random
import math
import asyncio
import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our real components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.simulator.real_drone_simulator import RealDroneSimulator, DEFAULT_DRONE_PHYSICS, EnvironmentalConditions, WeatherCondition, DronePosition
from app.ai.real_ml_models import RealMLModels, MissionFeatures, MissionType, TerrainType, WeatherCondition as MLWeatherCondition
from app.database.real_database import RealDatabase
from app.database.sqlite_fallback import SQLiteFallback

logger = logging.getLogger(__name__)

@dataclass
class SearchPattern:
    """Represents a search pattern with genetic algorithm parameters"""
    pattern_type: str  # grid, spiral, sector, lawnmower, adaptive
    parameters: Dict[str, float]  # pattern-specific parameters
    fitness_score: float = 0.0
    coverage_efficiency: float = 0.0
    energy_efficiency: float = 0.0
    time_efficiency: float = 0.0
    success_rate: float = 0.0
    simulation_results: Dict[str, Any] = None

@dataclass
class SearchEnvironment:
    """Environmental conditions affecting search performance"""
    terrain_type: str  # mountain, forest, urban, water, desert
    weather_conditions: Dict[str, float]  # visibility, wind, temperature
    search_area_size: float  # square kilometers
    target_type: str  # person, vehicle, structure, debris
    urgency_level: int  # 1-5 scale
    num_drones: int
    mission_duration: float  # hours

@dataclass
class SimulationResult:
    """Results from a simulation run"""
    pattern: SearchPattern
    environment: SearchEnvironment
    coverage_percentage: float
    success_rate: float
    total_distance: float
    total_flight_time: float
    energy_consumed: float
    discoveries_found: int
    false_positives: int
    simulation_time: float

class RealGeneticSearchOptimizer:
    """
    REAL genetic algorithm for optimizing SAR search patterns
    Connected to actual drone simulation and ML models
    """
    
    def __init__(self, population_size: int = 50, generations: int = 100):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = 0.1
        self.crossover_rate = 0.8
        self.elite_size = 5
        
        # Pattern parameter ranges
        self.pattern_parameters = {
            'grid': {
                'spacing': (10, 100),  # meters
                'angle': (0, 90),  # degrees
                'overlap': (0, 0.5)  # percentage
            },
            'spiral': {
                'radius_step': (5, 50),  # meters
                'angle_step': (5, 45),  # degrees
                'max_radius': (100, 1000)  # meters
            },
            'sector': {
                'sector_count': (4, 16),  # number of sectors
                'sector_angle': (10, 90),  # degrees
                'search_radius': (50, 500)  # meters
            },
            'lawnmower': {
                'strip_width': (10, 100),  # meters
                'turn_radius': (5, 50),  # meters
                'overlap': (0, 0.3)  # percentage
            },
            'adaptive': {
                'exploration_rate': (0.1, 0.9),  # balance between exploration and exploitation
                'adaptation_threshold': (0.1, 0.5),  # when to adapt
                'learning_rate': (0.01, 0.1)  # how fast to adapt
            }
        }
        
        # Initialize real components
        self.ml_models = RealMLModels()
        self.database = None  # Will be initialized in initialize()
        self.simulator_pool = []
        
        # Performance tracking
        self.best_patterns = []
        self.fitness_history = []
        self.simulation_count = 0
        
        logger.info(f"Initialized Real Genetic Search Optimizer with population {population_size}, generations {generations}")
    
    async def initialize(self):
        """Initialize all real components"""
        try:
            # Initialize ML models
            await self.ml_models.initialize()
            
            # Initialize database with fallback
            try:
                self.database = RealDatabase()
                await self.database.initialize()
                logger.info("Using PostgreSQL database")
            except Exception as e:
                logger.warning(f"PostgreSQL not available, using SQLite fallback: {e}")
                self.database = SQLiteFallback()
                await self.database.initialize()
                logger.info("Using SQLite fallback database")
            
            # Create simulator pool
            for i in range(self.population_size):
                simulator = RealDroneSimulator(f"drone_{i:03d}", DEFAULT_DRONE_PHYSICS)
                self.simulator_pool.append(simulator)
            
            logger.info("Real Genetic Search Optimizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Real Genetic Search Optimizer initialization failed: {e}")
            raise
    
    def generate_random_pattern(self) -> SearchPattern:
        """Generate a random search pattern"""
        pattern_type = random.choice(list(self.pattern_parameters.keys()))
        parameters = {}
        
        for param, (min_val, max_val) in self.pattern_parameters[pattern_type].items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                parameters[param] = random.randint(min_val, max_val)
            else:
                parameters[param] = random.uniform(min_val, max_val)
        
        return SearchPattern(
            pattern_type=pattern_type,
            parameters=parameters
        )
    
    def generate_initial_population(self) -> List[SearchPattern]:
        """Generate initial population of search patterns"""
        population = []
        
        # Generate diverse patterns
        for _ in range(self.population_size):
            pattern = self.generate_random_pattern()
            population.append(pattern)
        
        logger.info(f"Generated initial population of {len(population)} patterns")
        return population
    
    async def evaluate_fitness(self, pattern: SearchPattern, environment: SearchEnvironment) -> float:
        """
        Evaluate fitness using REAL simulation and ML models
        
        Args:
            pattern: Search pattern to evaluate
            environment: Environmental conditions
        
        Returns:
            Fitness score (0-1)
        """
        try:
            # Run real simulation
            simulation_result = await self.run_simulation(pattern, environment)
            
            # Calculate fitness components
            coverage_score = simulation_result.coverage_percentage / 100.0
            success_score = simulation_result.success_rate
            energy_score = 1.0 - (simulation_result.energy_consumed / (environment.num_drones * 100))  # Normalize
            time_score = 1.0 - (simulation_result.total_flight_time / (environment.mission_duration * 3600))
            
            # Weighted fitness function
            fitness = (
                coverage_score * 0.3 +
                success_score * 0.4 +
                energy_score * 0.2 +
                time_score * 0.1
            )
            
            # Store results
            pattern.fitness_score = fitness
            pattern.coverage_efficiency = coverage_score
            pattern.energy_efficiency = energy_score
            pattern.time_efficiency = time_score
            pattern.success_rate = success_score
            pattern.simulation_results = asdict(simulation_result)
            
            self.simulation_count += 1
            
            logger.debug(f"Pattern {pattern.pattern_type} fitness: {fitness:.3f}")
            
            return fitness
            
        except Exception as e:
            logger.error(f"Fitness evaluation failed: {e}")
            return 0.0
    
    async def run_simulation(self, pattern: SearchPattern, environment: SearchEnvironment) -> SimulationResult:
        """
        Run REAL simulation using drone simulator and ML models
        
        Args:
            pattern: Search pattern to simulate
            environment: Environmental conditions
        
        Returns:
            Simulation results
        """
        start_time = time.time()
        
        try:
            # Get a simulator from the pool
            simulator = self.simulator_pool[self.simulation_count % len(self.simulator_pool)]
            
            # Set environmental conditions
            weather_condition = self._map_weather_condition(environment.weather_conditions)
            env_conditions = EnvironmentalConditions(
                wind_speed=environment.weather_conditions.get('wind_speed', 0),
                wind_direction=environment.weather_conditions.get('wind_direction', 0),
                temperature=environment.weather_conditions.get('temperature', 25),
                pressure=101325.0,
                humidity=environment.weather_conditions.get('humidity', 50),
                visibility=environment.weather_conditions.get('visibility', 10000),
                weather_condition=weather_condition
            )
            
            simulator.set_environmental_conditions(env_conditions)
            
            # Generate waypoints based on pattern
            waypoints = self._generate_pattern_waypoints(pattern, environment)
            
            # Run simulation
            telemetry_log = await simulator.simulate_mission(waypoints, environment.mission_duration * 3600)
            
            # Calculate results
            total_distance = sum(t.distance_traveled for t in telemetry_log)
            total_flight_time = max(t.flight_time for t in telemetry_log) if telemetry_log else 0
            energy_consumed = sum(t.power_consumption for t in telemetry_log) / 3600  # Wh
            
            # Calculate coverage (simplified)
            if telemetry_log:
                x_range = max(t.position.x for t in telemetry_log) - min(t.position.x for t in telemetry_log)
                y_range = max(t.position.y for t in telemetry_log) - min(t.position.y for t in telemetry_log)
                coverage_area = x_range * y_range  # Already in meters
                search_area = environment.search_area_size * 1000000  # Convert km² to m²
                coverage_percentage = min(100, (coverage_area / search_area) * 100)
            else:
                coverage_percentage = 0
            
            # Simulate discoveries (using ML model)
            discoveries_found = await self._simulate_discoveries(pattern, environment, coverage_percentage)
            
            # Calculate success rate
            success_rate = min(1.0, discoveries_found / max(1, environment.urgency_level))
            
            simulation_time = time.time() - start_time
            
            return SimulationResult(
                pattern=pattern,
                environment=environment,
                coverage_percentage=coverage_percentage,
                success_rate=success_rate,
                total_distance=total_distance,
                total_flight_time=total_flight_time,
                energy_consumed=energy_consumed,
                discoveries_found=discoveries_found,
                false_positives=discoveries_found // 4,  # Assume 25% false positive rate
                simulation_time=simulation_time
            )
            
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            return SimulationResult(
                pattern=pattern,
                environment=environment,
                coverage_percentage=0,
                success_rate=0,
                total_distance=0,
                total_flight_time=0,
                energy_consumed=0,
                discoveries_found=0,
                false_positives=0,
                simulation_time=time.time() - start_time
            )
    
    def _map_weather_condition(self, weather_conditions: Dict[str, float]) -> WeatherCondition:
        """Map weather conditions to WeatherCondition enum"""
        visibility = weather_conditions.get('visibility', 10000)
        wind_speed = weather_conditions.get('wind_speed', 0)
        
        if visibility < 1000:
            return WeatherCondition.FOGGY
        elif wind_speed > 15:
            return WeatherCondition.WINDY
        elif visibility < 5000:
            return WeatherCondition.CLOUDY
        else:
            return WeatherCondition.CLEAR
    
    def _generate_pattern_waypoints(self, pattern: SearchPattern, environment: SearchEnvironment) -> List[Tuple[float, float, float]]:
        """Generate waypoints based on search pattern"""
        waypoints = []
        
        # Calculate search area dimensions
        area_radius = math.sqrt(environment.search_area_size / math.pi) * 1000  # meters
        center_x, center_y = 0, 0  # Assume center at origin
        
        if pattern.pattern_type == "grid":
            spacing = pattern.parameters.get('spacing', 50)
            angle = pattern.parameters.get('angle', 0)
            
            # Generate grid waypoints
            for x in np.arange(-area_radius, area_radius, spacing):
                for y in np.arange(-area_radius, area_radius, spacing):
                    # Rotate coordinates
                    rotated_x = x * math.cos(math.radians(angle)) - y * math.sin(math.radians(angle))
                    rotated_y = x * math.sin(math.radians(angle)) + y * math.cos(math.radians(angle))
                    
                    if rotated_x**2 + rotated_y**2 <= area_radius**2:
                        waypoints.append((rotated_x, rotated_y, 50))  # 50m altitude
        
        elif pattern.pattern_type == "spiral":
            radius_step = pattern.parameters.get('radius_step', 25)
            angle_step = pattern.parameters.get('angle_step', 15)
            max_radius = min(pattern.parameters.get('max_radius', 500), area_radius)
            
            # Generate spiral waypoints
            radius = 0
            angle = 0
            while radius < max_radius:
                x = radius * math.cos(math.radians(angle))
                y = radius * math.sin(math.radians(angle))
                waypoints.append((x, y, 50))
                
                radius += radius_step
                angle += angle_step
        
        elif pattern.pattern_type == "sector":
            sector_count = int(pattern.parameters.get('sector_count', 8))
            sector_angle = pattern.parameters.get('sector_angle', 45)
            search_radius = min(pattern.parameters.get('search_radius', 300), area_radius)
            
            # Generate sector waypoints
            for sector in range(sector_count):
                start_angle = sector * (360 / sector_count)
                end_angle = start_angle + sector_angle
                
                for angle in np.arange(start_angle, end_angle, 10):
                    for radius in np.arange(50, search_radius, 50):
                        x = radius * math.cos(math.radians(angle))
                        y = radius * math.sin(math.radians(angle))
                        waypoints.append((x, y, 50))
        
        elif pattern.pattern_type == "lawnmower":
            strip_width = pattern.parameters.get('strip_width', 50)
            overlap = pattern.parameters.get('overlap', 0.1)
            
            # Generate lawnmower waypoints
            y = -area_radius
            direction = 1
            while y < area_radius:
                if direction == 1:
                    x_values = np.arange(-area_radius, area_radius, strip_width)
                else:
                    x_values = np.arange(area_radius, -area_radius, -strip_width)
                
                for x in x_values:
                    if x**2 + y**2 <= area_radius**2:
                        waypoints.append((x, y, 50))
                
                y += strip_width
                direction *= -1
        
        elif pattern.pattern_type == "adaptive":
            # Map adaptive to spiral pattern for ML model compatibility
            radius_step = pattern.parameters.get('radius_step', 25)
            angle_step = pattern.parameters.get('angle_step', 15)
            max_radius = min(pattern.parameters.get('max_radius', 500), area_radius)
            
            # Generate spiral waypoints (adaptive uses spiral as base)
            radius = 0
            angle = 0
            while radius < max_radius:
                x = radius * math.cos(math.radians(angle))
                y = radius * math.sin(math.radians(angle))
                waypoints.append((x, y, 50))
                
                radius += radius_step
                angle += angle_step
        
        else:  # default fallback
            # Generate grid pattern as fallback
            spacing = 50
            for x in np.arange(-area_radius, area_radius, spacing):
                for y in np.arange(-area_radius, area_radius, spacing):
                    if x**2 + y**2 <= area_radius**2:
                        waypoints.append((x, y, 50))
        
        return waypoints
    
    async def _simulate_discoveries(self, pattern: SearchPattern, environment: SearchEnvironment, coverage_percentage: float) -> int:
        """Simulate discoveries using ML models"""
        try:
            # Create mission features for ML prediction
            mission_features = MissionFeatures(
                mission_type=MissionType.SEARCH.value,
                terrain_type=environment.terrain_type,
                weather_condition=self._map_weather_condition(environment.weather_conditions).value,
                area_size=environment.search_area_size,
                duration_hours=environment.mission_duration,
                num_drones=environment.num_drones,
                target_urgency=environment.urgency_level,
                time_of_day=12,  # Assume midday
                season=1,  # Assume summer
                wind_speed=environment.weather_conditions.get('wind_speed', 0),
                visibility=environment.weather_conditions.get('visibility', 10000),
                temperature=environment.weather_conditions.get('temperature', 25),
                humidity=environment.weather_conditions.get('humidity', 50),
                battery_reserve=80,
                communication_range=10,
                search_density="medium",
                search_pattern=pattern.pattern_type,
                altitude=50,
                speed=5
            )
            
            # Get ML prediction
            prediction = await self.ml_models.predict_mission_outcome(mission_features)
            
            # Calculate expected discoveries based on coverage and success rate
            base_discoveries = environment.urgency_level * 2  # Base discoveries per urgency level
            coverage_factor = coverage_percentage / 100.0
            success_factor = prediction.success_rate
            
            expected_discoveries = int(base_discoveries * coverage_factor * success_factor)
            
            # Add some randomness
            actual_discoveries = max(0, int(expected_discoveries + random.uniform(-2, 2)))
            
            return actual_discoveries
            
        except Exception as e:
            logger.error(f"Discovery simulation failed: {e}")
            return 0
    
    def crossover(self, parent1: SearchPattern, parent2: SearchPattern) -> Tuple[SearchPattern, SearchPattern]:
        """Perform crossover between two parent patterns"""
        if random.random() > self.crossover_rate:
            return parent1, parent2
        
        # Create offspring
        child1 = SearchPattern(
            pattern_type=parent1.pattern_type,
            parameters=parent1.parameters.copy()
        )
        child2 = SearchPattern(
            pattern_type=parent2.pattern_type,
            parameters=parent2.parameters.copy()
        )
        
        # Crossover parameters (only if both parents have the same pattern type)
        if parent1.pattern_type == parent2.pattern_type:
            for param in parent1.parameters:
                if random.random() < 0.5:
                    child1.parameters[param] = parent2.parameters[param]
                    child2.parameters[param] = parent1.parameters[param]
        
        return child1, child2
    
    def mutate(self, pattern: SearchPattern) -> SearchPattern:
        """Mutate a search pattern"""
        mutated = SearchPattern(
            pattern_type=pattern.pattern_type,
            parameters=pattern.parameters.copy()
        )
        
        if random.random() < self.mutation_rate:
            # Mutate parameters
            for param, (min_val, max_val) in self.pattern_parameters[pattern.pattern_type].items():
                if random.random() < 0.3:  # 30% chance to mutate each parameter
                    if isinstance(min_val, int) and isinstance(max_val, int):
                        mutated.parameters[param] = random.randint(min_val, max_val)
                    else:
                        mutated.parameters[param] = random.uniform(min_val, max_val)
            
            # Small chance to change pattern type
            if random.random() < 0.1:
                mutated.pattern_type = random.choice(list(self.pattern_parameters.keys()))
                # Regenerate parameters for new pattern type
                for param, (min_val, max_val) in self.pattern_parameters[mutated.pattern_type].items():
                    if isinstance(min_val, int) and isinstance(max_val, int):
                        mutated.parameters[param] = random.randint(min_val, max_val)
                    else:
                        mutated.parameters[param] = random.uniform(min_val, max_val)
        
        return mutated
    
    def select_parents(self, population: List[SearchPattern]) -> Tuple[SearchPattern, SearchPattern]:
        """Select parents using tournament selection"""
        tournament_size = 3
        
        # Tournament selection for parent 1
        tournament1 = random.sample(population, tournament_size)
        parent1 = max(tournament1, key=lambda p: p.fitness_score)
        
        # Tournament selection for parent 2
        tournament2 = random.sample(population, tournament_size)
        parent2 = max(tournament2, key=lambda p: p.fitness_score)
        
        return parent1, parent2
    
    async def evolve_population(self, population: List[SearchPattern], environment: SearchEnvironment) -> List[SearchPattern]:
        """Evolve population for one generation"""
        # Sort by fitness
        population.sort(key=lambda p: p.fitness_score, reverse=True)
        
        # Keep elite
        new_population = population[:self.elite_size]
        
        # Generate offspring
        while len(new_population) < self.population_size:
            parent1, parent2 = self.select_parents(population)
            child1, child2 = self.crossover(parent1, parent2)
            
            child1 = self.mutate(child1)
            child2 = self.mutate(child2)
            
            new_population.extend([child1, child2])
        
        # Trim to population size
        new_population = new_population[:self.population_size]
        
        return new_population
    
    async def optimize_search_pattern(self, environment: SearchEnvironment) -> SearchPattern:
        """
        Main optimization function
        
        Args:
            environment: Environmental conditions for optimization
        
        Returns:
            Best search pattern found
        """
        try:
            logger.info(f"Starting optimization for {self.generations} generations")
            
            # Generate initial population
            population = self.generate_initial_population()
            
            # Evaluate initial population
            logger.info("Evaluating initial population...")
            for pattern in population:
                await self.evaluate_fitness(pattern, environment)
            
            # Evolution loop
            for generation in range(self.generations):
                logger.info(f"Generation {generation + 1}/{self.generations}")
                
                # Evolve population
                population = await self.evolve_population(population, environment)
                
                # Evaluate new population
                for pattern in population:
                    if pattern.fitness_score == 0.0:  # Only evaluate unevaluated patterns
                        await self.evaluate_fitness(pattern, environment)
                
                # Track best patterns
                best_pattern = max(population, key=lambda p: p.fitness_score)
                self.best_patterns.append(best_pattern)
                self.fitness_history.append(best_pattern.fitness_score)
                
                logger.info(f"Best fitness: {best_pattern.fitness_score:.3f} ({best_pattern.pattern_type})")
            
            # Return best pattern
            best_pattern = max(population, key=lambda p: p.fitness_score)
            logger.info(f"Optimization complete. Best pattern: {best_pattern.pattern_type} with fitness {best_pattern.fitness_score:.3f}")
            
            return best_pattern
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of genetic optimizer"""
        return {
            "status": "healthy",
            "population_size": self.population_size,
            "generations": self.generations,
            "simulation_count": self.simulation_count,
            "best_patterns_count": len(self.best_patterns),
            "fitness_history": self.fitness_history[-10:] if self.fitness_history else [],
            "components": {
                "ml_models": await self.ml_models.health_check(),
                "database": await self.database.health_check(),
                "simulators": len(self.simulator_pool)
            }
        }

# Global genetic optimizer instance
real_genetic_optimizer = RealGeneticSearchOptimizer()
