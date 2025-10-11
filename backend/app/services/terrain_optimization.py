"""
Advanced Terrain Optimization for SAR Mission Commander
Real-world terrain analysis and coverage optimization for search and rescue operations
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import math
try:
    from scipy import ndimage
    from scipy.spatial.distance import cdist
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Mock scipy functions
    def ndimage(*args, **kwargs): return None
    def cdist(*args, **kwargs): return None

from ..utils.logging import get_logger

logger = get_logger(__name__)

class TerrainType(Enum):
    FLAT = "flat"
    HILLY = "hilly"
    MOUNTAINOUS = "mountainous"
    FOREST = "forest"
    URBAN = "urban"
    WATER = "water"
    DESERT = "desert"
    SWAMP = "swamp"

class CoverageStrategy(Enum):
    UNIFORM = "uniform"
    PRIORITY_BASED = "priority_based"
    TERRAIN_ADAPTIVE = "terrain_adaptive"
    RISK_BASED = "risk_based"
    EFFICIENCY_OPTIMIZED = "efficiency_optimized"

@dataclass
class TerrainData:
    """Terrain elevation and characteristics data"""
    latitude: float
    longitude: float
    elevation_m: float
    slope_degrees: float
    aspect_degrees: float
    roughness: float
    vegetation_density: float
    visibility_factor: float
    accessibility_factor: float
    terrain_type: TerrainType

@dataclass
class CoverageCell:
    """Individual coverage cell with terrain characteristics"""
    cell_id: str
    center_lat: float
    center_lng: float
    elevation_m: float
    terrain_type: TerrainType
    visibility_score: float
    accessibility_score: float
    priority_score: float
    coverage_probability: float
    search_difficulty: float
    optimal_altitude_m: float
    coverage_radius_m: float

@dataclass
class TerrainOptimization:
    """Terrain optimization result"""
    optimization_id: str
    strategy: CoverageStrategy
    coverage_cells: List[CoverageCell]
    total_coverage_percentage: float
    efficiency_score: float
    terrain_adaptation_score: float
    recommended_altitude_m: float
    estimated_search_time_hours: float
    battery_consumption_estimate: float

@dataclass
class SearchZone:
    """Enhanced search zone with terrain data"""
    zone_id: str
    bounds: Dict[str, float]  # north, south, east, west
    center_lat: float
    center_lng: float
    area_km2: float
    terrain_data: List[TerrainData]
    priority_areas: List[Dict[str, Any]]
    obstacles: List[Dict[str, Any]]
    accessibility_constraints: List[Dict[str, Any]]

class TerrainOptimizationEngine:
    """Advanced terrain optimization engine for SAR operations"""
    
    def __init__(self):
        self.terrain_cache = {}
        self.elevation_data = {}
        self.terrain_analysis_cache = {}
        
        # Terrain-specific parameters
        self.terrain_parameters = {
            TerrainType.FLAT: {
                'visibility_factor': 1.0,
                'accessibility_factor': 1.0,
                'optimal_altitude_m': 100,
                'coverage_radius_m': 500
            },
            TerrainType.HILLY: {
                'visibility_factor': 0.8,
                'accessibility_factor': 0.7,
                'optimal_altitude_m': 150,
                'coverage_radius_m': 400
            },
            TerrainType.MOUNTAINOUS: {
                'visibility_factor': 0.6,
                'accessibility_factor': 0.4,
                'optimal_altitude_m': 200,
                'coverage_radius_m': 300
            },
            TerrainType.FOREST: {
                'visibility_factor': 0.4,
                'accessibility_factor': 0.3,
                'optimal_altitude_m': 120,
                'coverage_radius_m': 250
            },
            TerrainType.URBAN: {
                'visibility_factor': 0.5,
                'accessibility_factor': 0.6,
                'optimal_altitude_m': 80,
                'coverage_radius_m': 300
            },
            TerrainType.WATER: {
                'visibility_factor': 0.9,
                'accessibility_factor': 0.2,
                'optimal_altitude_m': 60,
                'coverage_radius_m': 600
            },
            TerrainType.DESERT: {
                'visibility_factor': 0.95,
                'accessibility_factor': 0.8,
                'optimal_altitude_m': 110,
                'coverage_radius_m': 550
            },
            TerrainType.SWAMP: {
                'visibility_factor': 0.3,
                'accessibility_factor': 0.1,
                'optimal_altitude_m': 90,
                'coverage_radius_m': 200
            }
        }
        
        # Coverage optimization weights
        self.optimization_weights = {
            'coverage_completeness': 0.4,
            'efficiency': 0.3,
            'terrain_adaptation': 0.2,
            'risk_minimization': 0.1
        }
    
    async def optimize_coverage(self, search_zone: SearchZone, 
                              drone_count: int = 1,
                              strategy: CoverageStrategy = CoverageStrategy.TERRAIN_ADAPTIVE) -> TerrainOptimization:
        """
        Optimize coverage for a search zone based on terrain characteristics
        """
        try:
            optimization_id = f"opt_{int(datetime.now().timestamp())}"
            
            # Analyze terrain characteristics
            terrain_analysis = await self._analyze_terrain_characteristics(search_zone)
            
            # Generate coverage cells based on strategy
            if strategy == CoverageStrategy.UNIFORM:
                coverage_cells = await self._generate_uniform_coverage(search_zone, drone_count)
            elif strategy == CoverageStrategy.PRIORITY_BASED:
                coverage_cells = await self._generate_priority_coverage(search_zone, drone_count)
            elif strategy == CoverageStrategy.TERRAIN_ADAPTIVE:
                coverage_cells = await self._generate_terrain_adaptive_coverage(search_zone, drone_count, terrain_analysis)
            elif strategy == CoverageStrategy.RISK_BASED:
                coverage_cells = await self._generate_risk_based_coverage(search_zone, drone_count)
            elif strategy == CoverageStrategy.EFFICIENCY_OPTIMIZED:
                coverage_cells = await self._generate_efficiency_optimized_coverage(search_zone, drone_count)
            else:
                coverage_cells = await self._generate_terrain_adaptive_coverage(search_zone, drone_count, terrain_analysis)
            
            # Optimize coverage parameters
            optimized_cells = await self._optimize_cell_parameters(coverage_cells, terrain_analysis)
            
            # Calculate optimization metrics
            total_coverage = await self._calculate_total_coverage(optimized_cells, search_zone)
            efficiency_score = await self._calculate_efficiency_score(optimized_cells, search_zone)
            terrain_adaptation_score = await self._calculate_terrain_adaptation_score(optimized_cells, terrain_analysis)
            
            # Determine recommended altitude
            recommended_altitude = await self._determine_optimal_altitude(optimized_cells)
            
            # Estimate search time and battery consumption
            search_time = await self._estimate_search_time(optimized_cells, drone_count)
            battery_consumption = await self._estimate_battery_consumption(optimized_cells, search_time)
            
            return TerrainOptimization(
                optimization_id=optimization_id,
                strategy=strategy,
                coverage_cells=optimized_cells,
                total_coverage_percentage=total_coverage,
                efficiency_score=efficiency_score,
                terrain_adaptation_score=terrain_adaptation_score,
                recommended_altitude_m=recommended_altitude,
                estimated_search_time_hours=search_time,
                battery_consumption_estimate=battery_consumption
            )
            
        except Exception as e:
            logger.error(f"Error optimizing coverage: {e}")
            raise
    
    async def _analyze_terrain_characteristics(self, search_zone: SearchZone) -> Dict[str, Any]:
        """Analyze terrain characteristics for optimization"""
        try:
            terrain_data = search_zone.terrain_data
            
            if not terrain_data:
                # Generate mock terrain data if none provided
                terrain_data = await self._generate_mock_terrain_data(search_zone)
            
            # Calculate terrain statistics
            elevations = [td.elevation_m for td in terrain_data]
            slopes = [td.slope_degrees for td in terrain_data]
            roughness_values = [td.roughness for td in terrain_data]
            
            # Terrain type distribution
            terrain_type_counts = {}
            for td in terrain_data:
                terrain_type_counts[td.terrain_type] = terrain_type_counts.get(td.terrain_type, 0) + 1
            
            # Calculate terrain complexity
            elevation_variance = np.var(elevations) if elevations else 0
            slope_variance = np.var(slopes) if slopes else 0
            roughness_variance = np.var(roughness_values) if roughness_values else 0
            
            terrain_complexity = (elevation_variance / 1000 + slope_variance / 100 + roughness_variance) / 3
            
            # Calculate average visibility and accessibility
            avg_visibility = np.mean([td.visibility_factor for td in terrain_data]) if terrain_data else 0.5
            avg_accessibility = np.mean([td.accessibility_factor for td in terrain_data]) if terrain_data else 0.5
            
            return {
                'terrain_complexity': terrain_complexity,
                'elevation_range': (min(elevations), max(elevations)) if elevations else (0, 0),
                'average_slope': np.mean(slopes) if slopes else 0,
                'terrain_type_distribution': terrain_type_counts,
                'average_visibility': avg_visibility,
                'average_accessibility': avg_accessibility,
                'dominant_terrain_type': max(terrain_type_counts.items(), key=lambda x: x[1])[0] if terrain_type_counts else TerrainType.FLAT
            }
            
        except Exception as e:
            logger.error(f"Error analyzing terrain characteristics: {e}")
            return {}
    
    async def _generate_terrain_adaptive_coverage(self, search_zone: SearchZone, 
                                                drone_count: int,
                                                terrain_analysis: Dict[str, Any]) -> List[CoverageCell]:
        """Generate terrain-adaptive coverage cells"""
        try:
            cells = []
            cell_size_km = 0.5  # 500m grid cells
            
            # Calculate number of cells needed
            zone_width_km = search_zone.bounds['east'] - search_zone.bounds['west']
            zone_height_km = search_zone.bounds['north'] - search_zone.bounds['south']
            
            # Convert to approximate km (rough conversion)
            zone_width_km *= 111 * math.cos(math.radians(search_zone.center_lat))
            zone_height_km *= 111
            
            num_cells_x = int(zone_width_km / cell_size_km)
            num_cells_y = int(zone_height_km / cell_size_km)
            
            # Generate cells based on terrain characteristics
            for i in range(num_cells_x):
                for j in range(num_cells_y):
                    # Calculate cell center coordinates
                    lat_offset = (i - num_cells_x / 2) * cell_size_km / 111
                    lng_offset = (j - num_cells_y / 2) * cell_size_km / (111 * math.cos(math.radians(search_zone.center_lat)))
                    
                    cell_lat = search_zone.center_lat + lat_offset
                    cell_lng = search_zone.center_lng + lng_offset
                    
                    # Get terrain data for this cell
                    cell_terrain = await self._get_terrain_for_cell(cell_lat, cell_lng, search_zone.terrain_data)
                    
                    # Calculate cell parameters based on terrain
                    visibility_score = cell_terrain.visibility_factor
                    accessibility_score = cell_terrain.accessibility_factor
                    
                    # Priority score based on terrain difficulty and potential for finding targets
                    priority_score = self._calculate_priority_score(cell_terrain, search_zone.priority_areas, cell_lat, cell_lng)
                    
                    # Coverage probability based on terrain visibility
                    coverage_probability = visibility_score * 0.8 + accessibility_score * 0.2
                    
                    # Search difficulty based on terrain complexity
                    search_difficulty = 1.0 - (visibility_score * 0.6 + accessibility_score * 0.4)
                    
                    # Optimal altitude and coverage radius based on terrain type
                    terrain_params = self.terrain_parameters[cell_terrain.terrain_type]
                    optimal_altitude = terrain_params['optimal_altitude_m']
                    coverage_radius = terrain_params['coverage_radius_m']
                    
                    # Adjust based on elevation
                    optimal_altitude = max(optimal_altitude, cell_terrain.elevation_m + 50)  # Minimum 50m above terrain
                    
                    cell = CoverageCell(
                        cell_id=f"cell_{i}_{j}",
                        center_lat=cell_lat,
                        center_lng=cell_lng,
                        elevation_m=cell_terrain.elevation_m,
                        terrain_type=cell_terrain.terrain_type,
                        visibility_score=visibility_score,
                        accessibility_score=accessibility_score,
                        priority_score=priority_score,
                        coverage_probability=coverage_probability,
                        search_difficulty=search_difficulty,
                        optimal_altitude_m=optimal_altitude,
                        coverage_radius_m=coverage_radius
                    )
                    
                    cells.append(cell)
            
            # Optimize cell distribution for drone count
            if drone_count > 1:
                cells = await self._optimize_cell_distribution(cells, drone_count)
            
            return cells
            
        except Exception as e:
            logger.error(f"Error generating terrain adaptive coverage: {e}")
            return []
    
    async def _get_terrain_for_cell(self, lat: float, lng: float, 
                                  terrain_data: List[TerrainData]) -> TerrainData:
        """Get terrain data for a specific cell location"""
        try:
            # Find closest terrain data point
            min_distance = float('inf')
            closest_terrain = None
            
            for td in terrain_data:
                distance = math.sqrt((td.latitude - lat)**2 + (td.longitude - lng)**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_terrain = td
            
            if closest_terrain:
                return closest_terrain
            else:
                # Return default terrain data if none found
                return TerrainData(
                    latitude=lat,
                    longitude=lng,
                    elevation_m=100.0,
                    slope_degrees=5.0,
                    aspect_degrees=0.0,
                    roughness=0.1,
                    vegetation_density=0.3,
                    visibility_factor=0.7,
                    accessibility_factor=0.6,
                    terrain_type=TerrainType.FLAT
                )
                
        except Exception as e:
            logger.error(f"Error getting terrain for cell: {e}")
            return TerrainData(
                latitude=lat, longitude=lng, elevation_m=100.0,
                slope_degrees=5.0, aspect_degrees=0.0, roughness=0.1,
                vegetation_density=0.3, visibility_factor=0.7,
                accessibility_factor=0.6, terrain_type=TerrainType.FLAT
            )
    
    def _calculate_priority_score(self, terrain: TerrainData, priority_areas: List[Dict[str, Any]], 
                                lat: float, lng: float) -> float:
        """Calculate priority score for a cell based on terrain and priority areas"""
        try:
            base_score = 0.5  # Default priority
            
            # Adjust based on terrain difficulty (higher difficulty = higher priority)
            terrain_difficulty = 1.0 - (terrain.visibility_factor * 0.6 + terrain.accessibility_factor * 0.4)
            base_score += terrain_difficulty * 0.3
            
            # Check if cell is in priority area
            for priority_area in priority_areas:
                if self._point_in_area(lat, lng, priority_area):
                    priority_multiplier = priority_area.get('priority_multiplier', 2.0)
                    base_score *= priority_multiplier
                    break
            
            return min(base_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating priority score: {e}")
            return 0.5
    
    def _point_in_area(self, lat: float, lng: float, area: Dict[str, Any]) -> bool:
        """Check if point is within a priority area"""
        try:
            bounds = area.get('bounds', {})
            if not bounds:
                return False
            
            return (bounds.get('south', -90) <= lat <= bounds.get('north', 90) and
                    bounds.get('west', -180) <= lng <= bounds.get('east', 180))
            
        except Exception as e:
            logger.error(f"Error checking point in area: {e}")
            return False
    
    async def _optimize_cell_distribution(self, cells: List[CoverageCell], drone_count: int) -> List[CoverageCell]:
        """Optimize cell distribution for multiple drones"""
        try:
            if drone_count <= 1:
                return cells
            
            # Sort cells by priority score
            sorted_cells = sorted(cells, key=lambda c: c.priority_score, reverse=True)
            
            # Distribute cells among drones
            cells_per_drone = len(sorted_cells) // drone_count
            optimized_cells = []
            
            for i, cell in enumerate(sorted_cells):
                # Assign drone based on priority and load balancing
                assigned_drone = i % drone_count
                
                # Create a copy of the cell with drone assignment
                optimized_cell = CoverageCell(
                    cell_id=cell.cell_id,
                    center_lat=cell.center_lat,
                    center_lng=cell.center_lng,
                    elevation_m=cell.elevation_m,
                    terrain_type=cell.terrain_type,
                    visibility_score=cell.visibility_score,
                    accessibility_score=cell.accessibility_score,
                    priority_score=cell.priority_score,
                    coverage_probability=cell.coverage_probability,
                    search_difficulty=cell.search_difficulty,
                    optimal_altitude_m=cell.optimal_altitude_m,
                    coverage_radius_m=cell.coverage_radius_m
                )
                
                # Add drone assignment metadata
                setattr(optimized_cell, 'assigned_drone', assigned_drone)
                
                optimized_cells.append(optimized_cell)
            
            return optimized_cells
            
        except Exception as e:
            logger.error(f"Error optimizing cell distribution: {e}")
            return cells
    
    async def _optimize_cell_parameters(self, cells: List[CoverageCell], 
                                      terrain_analysis: Dict[str, Any]) -> List[CoverageCell]:
        """Optimize individual cell parameters based on terrain analysis"""
        try:
            optimized_cells = []
            
            for cell in cells:
                # Adjust coverage radius based on terrain complexity
                terrain_complexity = terrain_analysis.get('terrain_complexity', 0.5)
                complexity_factor = 1.0 - (terrain_complexity * 0.3)  # Reduce radius for complex terrain
                
                optimized_radius = cell.coverage_radius_m * complexity_factor
                
                # Adjust optimal altitude based on elevation variance
                elevation_range = terrain_analysis.get('elevation_range', (0, 0))
                elevation_variance = elevation_range[1] - elevation_range[0]
                
                if elevation_variance > 200:  # High elevation variance
                    altitude_adjustment = elevation_variance * 0.1
                    optimized_altitude = max(cell.optimal_altitude_m + altitude_adjustment, cell.elevation_m + 50)
                else:
                    optimized_altitude = cell.optimal_altitude_m
                
                # Adjust coverage probability based on terrain analysis
                avg_visibility = terrain_analysis.get('average_visibility', 0.7)
                visibility_adjustment = (avg_visibility - 0.7) * 0.2  # Adjust based on average
                optimized_probability = max(0.1, min(1.0, cell.coverage_probability + visibility_adjustment))
                
                # Create optimized cell
                optimized_cell = CoverageCell(
                    cell_id=cell.cell_id,
                    center_lat=cell.center_lat,
                    center_lng=cell.center_lng,
                    elevation_m=cell.elevation_m,
                    terrain_type=cell.terrain_type,
                    visibility_score=cell.visibility_score,
                    accessibility_score=cell.accessibility_score,
                    priority_score=cell.priority_score,
                    coverage_probability=optimized_probability,
                    search_difficulty=cell.search_difficulty,
                    optimal_altitude_m=optimized_altitude,
                    coverage_radius_m=optimized_radius
                )
                
                # Copy any additional attributes
                if hasattr(cell, 'assigned_drone'):
                    setattr(optimized_cell, 'assigned_drone', cell.assigned_drone)
                
                optimized_cells.append(optimized_cell)
            
            return optimized_cells
            
        except Exception as e:
            logger.error(f"Error optimizing cell parameters: {e}")
            return cells
    
    async def _calculate_total_coverage(self, cells: List[CoverageCell], search_zone: SearchZone) -> float:
        """Calculate total coverage percentage"""
        try:
            if not cells:
                return 0.0
            
            # Calculate total area covered by all cells
            total_covered_area = 0.0
            
            for cell in cells:
                cell_area = math.pi * (cell.coverage_radius_m / 1000) ** 2  # Convert to km²
                weighted_area = cell_area * cell.coverage_probability
                total_covered_area += weighted_area
            
            # Calculate search zone area
            zone_area_km2 = search_zone.area_km2
            
            # Calculate coverage percentage
            coverage_percentage = min(100.0, (total_covered_area / zone_area_km2) * 100)
            
            return coverage_percentage
            
        except Exception as e:
            logger.error(f"Error calculating total coverage: {e}")
            return 0.0
    
    async def _calculate_efficiency_score(self, cells: List[CoverageCell], search_zone: SearchZone) -> float:
        """Calculate efficiency score (0-1, higher is better)"""
        try:
            if not cells:
                return 0.0
            
            # Calculate total distance traveled
            total_distance = 0.0
            
            for i in range(len(cells) - 1):
                cell1 = cells[i]
                cell2 = cells[i + 1]
                distance = self._calculate_distance(cell1.center_lat, cell1.center_lng, 
                                                  cell2.center_lat, cell2.center_lng)
                total_distance += distance
            
            # Calculate coverage per distance ratio
            total_coverage = await self._calculate_total_coverage(cells, search_zone)
            
            if total_distance > 0:
                efficiency = total_coverage / (total_distance / 1000)  # Coverage per km
            else:
                efficiency = total_coverage
            
            # Normalize to 0-1 scale
            normalized_efficiency = min(1.0, efficiency / 10.0)  # Assume 10% coverage per km is excellent
            
            return normalized_efficiency
            
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {e}")
            return 0.0
    
    async def _calculate_terrain_adaptation_score(self, cells: List[CoverageCell], 
                                                terrain_analysis: Dict[str, Any]) -> float:
        """Calculate terrain adaptation score"""
        try:
            if not cells:
                return 0.0
            
            total_adaptation_score = 0.0
            
            for cell in cells:
                # Score based on how well cell parameters adapt to terrain
                terrain_params = self.terrain_parameters[cell.terrain_type]
                
                # Check if altitude is appropriate for terrain
                altitude_score = 1.0 - abs(cell.optimal_altitude_m - terrain_params['optimal_altitude_m']) / 100.0
                altitude_score = max(0.0, min(1.0, altitude_score))
                
                # Check if coverage radius is appropriate for terrain
                radius_score = 1.0 - abs(cell.coverage_radius_m - terrain_params['coverage_radius_m']) / 200.0
                radius_score = max(0.0, min(1.0, radius_score))
                
                # Check if coverage probability accounts for terrain visibility
                visibility_score = abs(cell.coverage_probability - cell.visibility_score) / cell.visibility_score
                visibility_score = max(0.0, min(1.0, 1.0 - visibility_score))
                
                cell_adaptation_score = (altitude_score + radius_score + visibility_score) / 3.0
                total_adaptation_score += cell_adaptation_score
            
            average_adaptation_score = total_adaptation_score / len(cells)
            
            return average_adaptation_score
            
        except Exception as e:
            logger.error(f"Error calculating terrain adaptation score: {e}")
            return 0.0
    
    async def _determine_optimal_altitude(self, cells: List[CoverageCell]) -> float:
        """Determine optimal altitude for the mission"""
        try:
            if not cells:
                return 100.0  # Default altitude
            
            # Calculate weighted average altitude based on coverage probability and priority
            total_weight = 0.0
            weighted_altitude = 0.0
            
            for cell in cells:
                weight = cell.coverage_probability * cell.priority_score
                weighted_altitude += cell.optimal_altitude_m * weight
                total_weight += weight
            
            if total_weight > 0:
                optimal_altitude = weighted_altitude / total_weight
            else:
                optimal_altitude = np.mean([cell.optimal_altitude_m for cell in cells])
            
            # Ensure minimum altitude above highest terrain
            max_elevation = max([cell.elevation_m for cell in cells]) if cells else 0
            optimal_altitude = max(optimal_altitude, max_elevation + 50)
            
            return optimal_altitude
            
        except Exception as e:
            logger.error(f"Error determining optimal altitude: {e}")
            return 100.0
    
    async def _estimate_search_time(self, cells: List[CoverageCell], drone_count: int) -> float:
        """Estimate total search time in hours"""
        try:
            if not cells:
                return 0.0
            
            # Calculate time per cell based on search difficulty
            total_time_minutes = 0.0
            
            for cell in cells:
                base_time_per_cell = 5.0  # 5 minutes per cell
                difficulty_multiplier = 1.0 + cell.search_difficulty  # 1.0 to 2.0
                cell_time = base_time_per_cell * difficulty_multiplier
                total_time_minutes += cell_time
            
            # Divide by drone count for parallel search
            total_time_minutes /= drone_count
            
            # Convert to hours
            total_time_hours = total_time_minutes / 60.0
            
            return total_time_hours
            
        except Exception as e:
            logger.error(f"Error estimating search time: {e}")
            return 1.0
    
    async def _estimate_battery_consumption(self, cells: List[CoverageCell], search_time_hours: float) -> float:
        """Estimate battery consumption in Wh"""
        try:
            # Base power consumption
            hover_power = 200.0  # Watts
            flight_power = 250.0  # Watts
            
            # Calculate total energy consumption
            total_energy = search_time_hours * flight_power  # Wh
            
            # Add overhead for takeoff, landing, and maneuvering
            overhead_factor = 1.2
            total_energy *= overhead_factor
            
            return total_energy
            
        except Exception as e:
            logger.error(f"Error estimating battery consumption: {e}")
            return 500.0  # Default 500Wh
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters"""
        try:
            R = 6371000  # Earth radius in meters
            
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lng = math.radians(lng2 - lng1)
            
            a = (math.sin(delta_lat / 2) ** 2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * 
                 math.sin(delta_lng / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            return R * c
            
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return 0.0
    
    async def _generate_mock_terrain_data(self, search_zone: SearchZone) -> List[TerrainData]:
        """Generate mock terrain data for testing"""
        try:
            terrain_data = []
            
            # Generate a grid of terrain data points
            num_points = 50
            lat_range = search_zone.bounds['north'] - search_zone.bounds['south']
            lng_range = search_zone.bounds['east'] - search_zone.bounds['west']
            
            for i in range(num_points):
                lat = search_zone.bounds['south'] + (i / num_points) * lat_range
                lng = search_zone.bounds['west'] + (i / num_points) * lng_range
                
                # Generate mock terrain characteristics
                elevation = 100.0 + (i % 10) * 10.0  # Varying elevation
                slope = (i % 5) * 5.0  # Varying slope
                roughness = (i % 3) * 0.2  # Varying roughness
                
                # Determine terrain type based on elevation and slope
                if elevation > 150 and slope > 15:
                    terrain_type = TerrainType.MOUNTAINOUS
                    visibility = 0.6
                    accessibility = 0.4
                elif elevation > 120 or slope > 10:
                    terrain_type = TerrainType.HILLY
                    visibility = 0.8
                    accessibility = 0.7
                else:
                    terrain_type = TerrainType.FLAT
                    visibility = 1.0
                    accessibility = 1.0
                
                terrain_data.append(TerrainData(
                    latitude=lat,
                    longitude=lng,
                    elevation_m=elevation,
                    slope_degrees=slope,
                    aspect_degrees=0.0,
                    roughness=roughness,
                    vegetation_density=0.3,
                    visibility_factor=visibility,
                    accessibility_factor=accessibility,
                    terrain_type=terrain_type
                ))
            
            return terrain_data
            
        except Exception as e:
            logger.error(f"Error generating mock terrain data: {e}")
            return []
    
    # Additional coverage strategies (simplified implementations)
    async def _generate_uniform_coverage(self, search_zone: SearchZone, drone_count: int) -> List[CoverageCell]:
        """Generate uniform coverage cells"""
        # Simplified implementation - would generate regular grid
        return await self._generate_terrain_adaptive_coverage(search_zone, drone_count, {})
    
    async def _generate_priority_coverage(self, search_zone: SearchZone, drone_count: int) -> List[CoverageCell]:
        """Generate priority-based coverage cells"""
        # Simplified implementation - would focus on priority areas
        return await self._generate_terrain_adaptive_coverage(search_zone, drone_count, {})
    
    async def _generate_risk_based_coverage(self, search_zone: SearchZone, drone_count: int) -> List[CoverageCell]:
        """Generate risk-based coverage cells"""
        # Simplified implementation - would focus on high-risk areas
        return await self._generate_terrain_adaptive_coverage(search_zone, drone_count, {})
    
    async def _generate_efficiency_optimized_coverage(self, search_zone: SearchZone, drone_count: int) -> List[CoverageCell]:
        """Generate efficiency-optimized coverage cells"""
        # Simplified implementation - would optimize for maximum efficiency
        return await self._generate_terrain_adaptive_coverage(search_zone, drone_count, {})

# Global instance
terrain_optimization_engine = TerrainOptimizationEngine()
