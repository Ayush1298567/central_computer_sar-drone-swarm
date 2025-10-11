"""
Adaptive Planning API endpoints for dynamic mission optimization.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.services.adaptive_planner import (
    adaptive_planner, 
    MissionContext, 
    OptimizationConstraints, 
    DroneCapabilities,
    OptimizationStrategy,
    OptimizationResult
)
from ....core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/optimize-mission")
async def optimize_mission(
    mission_data: Dict[str, Any] = Body(...),
    strategy: str = "adaptive",
    db: Session = Depends(get_db)
):
    """
    Optimize a mission plan using adaptive planning algorithms.
    
    Args:
        mission_data: Mission context and constraints
        strategy: Optimization strategy (time_efficient, coverage_optimal, battery_conservative, adaptive)
        
    Returns:
        OptimizationResult with optimized plan
    """
    try:
        # Validate strategy
        try:
            optimization_strategy = OptimizationStrategy(strategy)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid strategy. Must be one of: {[s.value for s in OptimizationStrategy]}"
            )
        
        # Parse mission context
        mission_context = await _parse_mission_context(mission_data)
        
        # Optimize mission
        result = await adaptive_planner.optimize_mission_plan(
            mission_context, 
            optimization_strategy
        )
        
        return {
            "success": result.success,
            "optimization_result": {
                "confidence_score": result.confidence_score,
                "estimated_duration": result.estimated_duration,
                "estimated_battery_usage": result.estimated_battery_usage,
                "coverage_percentage": result.coverage_percentage,
                "risk_assessment": result.risk_assessment,
                "recommendations": result.recommendations
            },
            "optimized_plan": result.optimized_plan,
            "strategy_used": strategy,
            "mission_id": mission_context.mission_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mission optimization failed: {e}")
        raise HTTPException(status_code=500, detail="Mission optimization failed")


@router.post("/analyze-mission-context")
async def analyze_mission_context(
    mission_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Analyze mission context for optimization decisions.
    
    Args:
        mission_data: Mission context data
        
    Returns:
        Context analysis results
    """
    try:
        # Parse mission context
        mission_context = await _parse_mission_context(mission_data)
        
        # Analyze context (this would normally be a private method, but we'll expose it for debugging)
        analysis = await adaptive_planner._analyze_mission_context(mission_context)
        
        return {
            "success": True,
            "context_analysis": analysis,
            "mission_id": mission_context.mission_id
        }
        
    except Exception as e:
        logger.error(f"Context analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Context analysis failed")


@router.post("/generate-search-pattern")
async def generate_search_pattern(
    pattern_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Generate search pattern waypoints for a mission area.
    
    Args:
        pattern_data: Pattern generation parameters
        
    Returns:
        Generated waypoints and pattern information
    """
    try:
        # Extract parameters
        center_lat = pattern_data.get('center_lat', 37.7749)
        center_lng = pattern_data.get('center_lng', -122.4194)
        area_size_km2 = pattern_data.get('area_size_km2', 1.0)
        pattern_type = pattern_data.get('pattern_type', 'grid')
        altitude = pattern_data.get('altitude', 50.0)
        
        # Create minimal mission context for pattern generation
        mission_context = MissionContext(
            mission_id="pattern_generation",
            search_target="pattern_test",
            area_size_km2=area_size_km2,
            terrain_type=pattern_data.get('terrain_type', 'rural'),
            time_of_day=pattern_data.get('time_of_day', 'day'),
            weather_conditions=pattern_data.get('weather_conditions', {}),
            urgency_level=pattern_data.get('urgency_level', 'medium'),
            available_drones=[],
            constraints=OptimizationConstraints()
        )
        
        # Generate waypoints based on pattern type
        if pattern_type == 'grid':
            waypoints = adaptive_planner._generate_grid_waypoints(mission_context, altitude)
        elif pattern_type == 'spiral':
            waypoints = adaptive_planner._generate_spiral_waypoints(mission_context, altitude)
        elif pattern_type == 'concentric':
            waypoints = adaptive_planner._generate_concentric_waypoints(mission_context, altitude)
        elif pattern_type == 'lawnmower':
            waypoints = adaptive_planner._generate_lawnmower_waypoints(mission_context, altitude)
        else:
            waypoints = adaptive_planner._generate_adaptive_waypoints(mission_context, altitude)
        
        # Update waypoints with actual center coordinates
        for waypoint in waypoints:
            waypoint['lat'] = center_lat + (waypoint['lat'] - 37.7749)
            waypoint['lng'] = center_lng + (waypoint['lng'] - (-122.4194))
        
        return {
            "success": True,
            "pattern_type": pattern_type,
            "waypoints": waypoints,
            "waypoint_count": len(waypoints),
            "area_size_km2": area_size_km2,
            "altitude": altitude
        }
        
    except Exception as e:
        logger.error(f"Pattern generation failed: {e}")
        raise HTTPException(status_code=500, detail="Pattern generation failed")


@router.post("/optimize-drone-assignment")
async def optimize_drone_assignment(
    assignment_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Optimize drone assignment for a mission.
    
    Args:
        assignment_data: Drone assignment parameters
        
    Returns:
        Optimized drone assignments
    """
    try:
        # Extract parameters
        available_drones = assignment_data.get('available_drones', [])
        waypoints = assignment_data.get('waypoints', [])
        mission_area_km2 = assignment_data.get('mission_area_km2', 1.0)
        
        # Convert drone data to DroneCapabilities
        drone_capabilities = []
        for drone_data in available_drones:
            capabilities = DroneCapabilities(
                drone_id=drone_data.get('drone_id', 'unknown'),
                max_flight_time=drone_data.get('max_flight_time', 30),
                max_altitude=drone_data.get('max_altitude', 120.0),
                max_speed=drone_data.get('max_speed', 15.0),
                cruise_speed=drone_data.get('cruise_speed', 10.0),
                battery_capacity=drone_data.get('battery_capacity', 100.0),
                camera_resolution=(drone_data.get('camera_width', 1920), drone_data.get('camera_height', 1080)),
                gimbal_stabilization=drone_data.get('gimbal_stabilization', False),
                obstacle_avoidance=drone_data.get('obstacle_avoidance', False),
                weather_resistance=drone_data.get('weather_resistance', 'light')
            )
            drone_capabilities.append(capabilities)
        
        # Create minimal mission context
        mission_context = MissionContext(
            mission_id="assignment_optimization",
            search_target="assignment_test",
            area_size_km2=mission_area_km2,
            terrain_type=assignment_data.get('terrain_type', 'rural'),
            time_of_day=assignment_data.get('time_of_day', 'day'),
            weather_conditions=assignment_data.get('weather_conditions', {}),
            urgency_level=assignment_data.get('urgency_level', 'medium'),
            available_drones=drone_capabilities,
            constraints=OptimizationConstraints()
        )
        
        # Optimize drone assignment
        assignments = await adaptive_planner._assign_drones_to_areas(
            drone_capabilities, waypoints, mission_context
        )
        
        return {
            "success": True,
            "drone_assignments": assignments,
            "total_drones": len(drone_capabilities),
            "total_waypoints": len(waypoints)
        }
        
    except Exception as e:
        logger.error(f"Drone assignment optimization failed: {e}")
        raise HTTPException(status_code=500, detail="Drone assignment optimization failed")


@router.get("/optimization-history")
async def get_optimization_history(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get optimization history for analysis.
    
    Args:
        limit: Maximum number of history entries to return
        
    Returns:
        Optimization history
    """
    try:
        history = await adaptive_planner.get_optimization_history(limit)
        
        return {
            "success": True,
            "optimization_history": history,
            "total_entries": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get optimization history")


@router.get("/performance-insights")
async def get_performance_insights(db: Session = Depends(get_db)):
    """
    Get performance insights from optimization history.
    
    Returns:
        Performance insights and metrics
    """
    try:
        insights = await adaptive_planner.get_performance_insights()
        
        return {
            "success": True,
            "performance_insights": insights
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance insights")


@router.post("/update-optimization-weights")
async def update_optimization_weights(
    weights: Dict[str, float] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update optimization weights based on performance.
    
    Args:
        weights: New optimization weights
        
    Returns:
        Updated weights confirmation
    """
    try:
        # Validate weights
        valid_keys = ['time_efficiency', 'coverage_quality', 'battery_conservation', 'safety_margin', 'weather_adaptation']
        for key in weights:
            if key not in valid_keys:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid weight key: {key}. Must be one of: {valid_keys}"
                )
        
        # Update weights
        await adaptive_planner.update_optimization_weights(weights)
        
        return {
            "success": True,
            "updated_weights": adaptive_planner.optimization_weights,
            "message": "Optimization weights updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update optimization weights: {e}")
        raise HTTPException(status_code=500, detail="Failed to update optimization weights")


@router.get("/optimization-strategies")
async def get_optimization_strategies(db: Session = Depends(get_db)):
    """
    Get available optimization strategies.
    
    Returns:
        List of available optimization strategies
    """
    try:
        strategies = [
            {
                "value": strategy.value,
                "name": strategy.value.replace('_', ' ').title(),
                "description": _get_strategy_description(strategy)
            }
            for strategy in OptimizationStrategy
        ]
        
        return {
            "success": True,
            "optimization_strategies": strategies
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization strategies: {e}")
        raise HTTPException(status_code=500, detail="Failed to get optimization strategies")


@router.get("/search-patterns")
async def get_search_patterns(db: Session = Depends(get_db)):
    """
    Get available search patterns.
    
    Returns:
        List of available search patterns
    """
    try:
        patterns = [
            {
                "value": "grid",
                "name": "Grid Pattern",
                "description": "Systematic grid search for maximum coverage"
            },
            {
                "value": "spiral",
                "name": "Spiral Pattern",
                "description": "Spiral from center outward for complex terrain"
            },
            {
                "value": "concentric",
                "name": "Concentric Pattern",
                "description": "Concentric circles for circular search areas"
            },
            {
                "value": "lawnmower",
                "name": "Lawnmower Pattern",
                "description": "Back-and-forth pattern for rectangular areas"
            },
            {
                "value": "adaptive",
                "name": "Adaptive Pattern",
                "description": "Dynamic pattern based on conditions"
            }
        ]
        
        return {
            "success": True,
            "search_patterns": patterns
        }
        
    except Exception as e:
        logger.error(f"Failed to get search patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search patterns")


@router.post("/test-optimization")
async def test_optimization(
    test_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Test endpoint for adaptive planning functionality.
    
    Args:
        test_data: Test parameters
        
    Returns:
        Comprehensive test results
    """
    try:
        test_results = {}
        
        # Test 1: Mission context analysis
        try:
            mission_context = await _parse_mission_context(test_data)
            analysis = await adaptive_planner._analyze_mission_context(mission_context)
            test_results['context_analysis'] = {
                'success': True,
                'analysis': analysis
            }
        except Exception as e:
            test_results['context_analysis'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 2: Search pattern generation
        try:
            pattern_type = test_data.get('pattern_type', 'grid')
            waypoints = adaptive_planner._generate_grid_waypoints(mission_context, 50.0)
            test_results['pattern_generation'] = {
                'success': True,
                'waypoint_count': len(waypoints),
                'pattern_type': pattern_type
            }
        except Exception as e:
            test_results['pattern_generation'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 3: Mission optimization
        try:
            result = await adaptive_planner.optimize_mission_plan(
                mission_context, 
                OptimizationStrategy.ADAPTIVE
            )
            test_results['mission_optimization'] = {
                'success': result.success,
                'confidence_score': result.confidence_score,
                'estimated_duration': result.estimated_duration
            }
        except Exception as e:
            test_results['mission_optimization'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 4: Performance insights
        try:
            insights = await adaptive_planner.get_performance_insights()
            test_results['performance_insights'] = {
                'success': True,
                'insights': insights
            }
        except Exception as e:
            test_results['performance_insights'] = {
                'success': False,
                'error': str(e)
            }
        
        return {
            "success": True,
            "test_results": test_results,
            "summary": {
                "total_tests": len(test_results),
                "passed_tests": sum(1 for test in test_results.values() if test['success']),
                "failed_tests": sum(1 for test in test_results.values() if not test['success'])
            }
        }
        
    except Exception as e:
        logger.error(f"Optimization test failed: {e}")
        raise HTTPException(status_code=500, detail="Optimization test failed")


async def _parse_mission_context(mission_data: Dict[str, Any]) -> MissionContext:
    """Parse mission data into MissionContext object."""
    # Extract basic mission information
    mission_id = mission_data.get('mission_id', 'unknown')
    search_target = mission_data.get('search_target', 'unknown')
    area_size_km2 = mission_data.get('area_size_km2', 1.0)
    terrain_type = mission_data.get('terrain_type', 'rural')
    time_of_day = mission_data.get('time_of_day', 'day')
    weather_conditions = mission_data.get('weather_conditions', {})
    urgency_level = mission_data.get('urgency_level', 'medium')
    
    # Parse constraints
    constraints_data = mission_data.get('constraints', {})
    constraints = OptimizationConstraints(
        max_duration_minutes=constraints_data.get('max_duration_minutes', 120),
        min_battery_reserve=constraints_data.get('min_battery_reserve', 20.0),
        max_altitude=constraints_data.get('max_altitude', 150.0),
        min_altitude=constraints_data.get('min_altitude', 30.0),
        weather_tolerance=constraints_data.get('weather_tolerance', 'moderate'),
        priority_areas=constraints_data.get('priority_areas', []),
        no_fly_zones=constraints_data.get('no_fly_zones', [])
    )
    
    # Parse drone capabilities
    available_drones = []
    drones_data = mission_data.get('available_drones', [])
    for drone_data in drones_data:
        capabilities = DroneCapabilities(
            drone_id=drone_data.get('drone_id', 'unknown'),
            max_flight_time=drone_data.get('max_flight_time', 30),
            max_altitude=drone_data.get('max_altitude', 120.0),
            max_speed=drone_data.get('max_speed', 15.0),
            cruise_speed=drone_data.get('cruise_speed', 10.0),
            battery_capacity=drone_data.get('battery_capacity', 100.0),
            camera_resolution=(drone_data.get('camera_width', 1920), drone_data.get('camera_height', 1080)),
            gimbal_stabilization=drone_data.get('gimbal_stabilization', False),
            obstacle_avoidance=drone_data.get('obstacle_avoidance', False),
            weather_resistance=drone_data.get('weather_resistance', 'light')
        )
        available_drones.append(capabilities)
    
    return MissionContext(
        mission_id=mission_id,
        search_target=search_target,
        area_size_km2=area_size_km2,
        terrain_type=terrain_type,
        time_of_day=time_of_day,
        weather_conditions=weather_conditions,
        urgency_level=urgency_level,
        available_drones=available_drones,
        constraints=constraints
    )


def _get_strategy_description(strategy: OptimizationStrategy) -> str:
    """Get description for optimization strategy."""
    descriptions = {
        OptimizationStrategy.TIME_EFFICIENT: "Minimize mission duration for urgent operations",
        OptimizationStrategy.COVERAGE_OPTIMAL: "Maximize area coverage for thorough searches",
        OptimizationStrategy.BATTERY_CONSERVATIVE: "Minimize battery usage for extended operations",
        OptimizationStrategy.ADAPTIVE: "Dynamic optimization based on real-time conditions"
    }
    return descriptions.get(strategy, "Unknown strategy")
