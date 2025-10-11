"""
Learning System for Performance Improvement Algorithms.

This module provides intelligent learning capabilities that analyze mission outcomes,
drone performance, and system behavior to continuously improve SAR operations.
"""

import asyncio
import logging
import math
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..core.database import SessionLocal
from ..models import Mission, Drone, Discovery, MissionDrone
from .analytics_engine import AnalyticsEngine, MissionMetrics
from .adaptive_planner import adaptive_planner
from ..core.config import settings

logger = logging.getLogger(__name__)


class LearningAlgorithm(Enum):
    """Types of learning algorithms."""
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    SUPERVISED_LEARNING = "supervised_learning"
    UNSUPERVISED_LEARNING = "unsupervised_learning"
    DEEP_LEARNING = "deep_learning"
    GENETIC_ALGORITHM = "genetic_algorithm"


class PerformanceMetric(Enum):
    """Performance metrics for learning."""
    MISSION_EFFICIENCY = "mission_efficiency"
    BATTERY_OPTIMIZATION = "battery_optimization"
    DISCOVERY_ACCURACY = "discovery_accuracy"
    FLIGHT_PATH_OPTIMIZATION = "flight_path_optimization"
    WEATHER_ADAPTATION = "weather_adaptation"
    DRONE_COORDINATION = "drone_coordination"


@dataclass
class LearningDataPoint:
    """Single data point for learning algorithms."""
    timestamp: datetime
    mission_id: str
    drone_id: Optional[str]
    metric_type: PerformanceMetric
    input_features: Dict[str, float]
    output_value: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningModel:
    """Learning model for performance improvement."""
    model_id: str
    algorithm: LearningAlgorithm
    metric_type: PerformanceMetric
    accuracy: float
    last_trained: datetime
    training_data_count: int
    model_parameters: Dict[str, Any]
    predictions: List[float] = field(default_factory=list)


@dataclass
class PerformanceImprovement:
    """Performance improvement recommendation."""
    improvement_id: str
    metric_type: PerformanceMetric
    current_value: float
    predicted_value: float
    improvement_percentage: float
    confidence: float
    recommendations: List[str]
    implementation_priority: str  # low, medium, high, critical


@dataclass
class LearningInsights:
    """Insights from learning system analysis."""
    total_models: int
    active_models: int
    average_accuracy: float
    total_improvements: int
    performance_trends: Dict[str, float]
    top_improvements: List[PerformanceImprovement]
    learning_recommendations: List[str]


class LearningSystem:
    """
    Advanced learning system for continuous performance improvement.
    
    Analyzes mission outcomes, drone performance, and system behavior to:
    - Optimize mission planning algorithms
    - Improve drone coordination strategies
    - Enhance discovery accuracy
    - Optimize battery usage patterns
    - Adapt to weather conditions
    - Learn from mission outcomes
    """

    def __init__(self):
        self.analytics_engine = AnalyticsEngine()
        self.learning_models: Dict[str, LearningModel] = {}
        self.learning_data: List[LearningDataPoint] = []
        self.performance_improvements: List[PerformanceImprovement] = []
        self.learning_enabled = True
        
        # Learning parameters
        self.min_training_data = 50
        self.model_update_interval = timedelta(hours=24)
        self.learning_rate = 0.01
        self.exploration_rate = 0.1
        
        # Performance tracking
        self.performance_history: Dict[str, List[float]] = {}
        self.improvement_history: List[Dict] = []

    async def initialize(self):
        """Initialize the learning system."""
        logger.info("Initializing learning system...")
        
        # Load existing models
        await self._load_existing_models()
        
        # Initialize performance tracking
        await self._initialize_performance_tracking()
        
        # Start background learning tasks
        asyncio.create_task(self._background_learning_loop())
        
        logger.info("Learning system initialized successfully")

    async def _load_existing_models(self):
        """Load existing learning models from storage."""
        try:
            # In a real implementation, this would load from a database or file
            # For now, we'll initialize with default models
            default_models = [
                LearningModel(
                    model_id="mission_efficiency_rl",
                    algorithm=LearningAlgorithm.REINFORCEMENT_LEARNING,
                    metric_type=PerformanceMetric.MISSION_EFFICIENCY,
                    accuracy=0.75,
                    last_trained=datetime.utcnow(),
                    training_data_count=0,
                    model_parameters={"learning_rate": 0.01, "exploration_rate": 0.1}
                ),
                LearningModel(
                    model_id="battery_optimization_sl",
                    algorithm=LearningAlgorithm.SUPERVISED_LEARNING,
                    metric_type=PerformanceMetric.BATTERY_OPTIMIZATION,
                    accuracy=0.82,
                    last_trained=datetime.utcnow(),
                    training_data_count=0,
                    model_parameters={"learning_rate": 0.005, "regularization": 0.01}
                ),
                LearningModel(
                    model_id="discovery_accuracy_dl",
                    algorithm=LearningAlgorithm.DEEP_LEARNING,
                    metric_type=PerformanceMetric.DISCOVERY_ACCURACY,
                    accuracy=0.88,
                    last_trained=datetime.utcnow(),
                    training_data_count=0,
                    model_parameters={"layers": 3, "neurons": 128, "dropout": 0.2}
                )
            ]
            
            for model in default_models:
                self.learning_models[model.model_id] = model
                
        except Exception as e:
            logger.error(f"Failed to load existing models: {e}")

    async def _initialize_performance_tracking(self):
        """Initialize performance tracking for all metrics."""
        for metric in PerformanceMetric:
            self.performance_history[metric.value] = []

    async def _background_learning_loop(self):
        """Background task for continuous learning."""
        while self.learning_enabled:
            try:
                # Collect new data
                await self._collect_learning_data()
                
                # Update models
                await self._update_learning_models()
                
                # Generate improvements
                await self._generate_performance_improvements()
                
                # Wait before next iteration
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Background learning loop error: {e}")
                await asyncio.sleep(300)  # 5 minutes on error

    async def _collect_learning_data(self):
        """Collect new learning data from recent missions."""
        try:
            with SessionLocal() as db:
                # Get recent missions (last 24 hours)
                recent_missions = db.query(Mission).filter(
                    Mission.created_at >= datetime.utcnow() - timedelta(hours=24)
                ).all()
                
                for mission in recent_missions:
                    # Collect mission efficiency data
                    await self._collect_mission_efficiency_data(mission, db)
                    
                    # Collect battery optimization data
                    await self._collect_battery_optimization_data(mission, db)
                    
                    # Collect discovery accuracy data
                    await self._collect_discovery_accuracy_data(mission, db)
                    
                    # Collect flight path optimization data
                    await self._collect_flight_path_data(mission, db)
                    
        except Exception as e:
            logger.error(f"Failed to collect learning data: {e}")

    async def _collect_mission_efficiency_data(self, mission: Mission, db: Session):
        """Collect mission efficiency learning data."""
        try:
            # Calculate mission efficiency metrics
            duration = (mission.updated_at - mission.created_at).total_seconds() / 3600  # hours
            area_covered = mission.area_covered or 0
            discoveries = len(mission.discoveries) if mission.discoveries else 0
            
            # Input features
            input_features = {
                "area_size": mission.area_size or 0,
                "drone_count": len(mission.drones) if mission.drones else 1,
                "weather_wind": 0,  # Would come from weather service
                "weather_visibility": 10000,  # Default
                "terrain_complexity": self._calculate_terrain_complexity(mission),
                "urgency_level": self._calculate_urgency_level(mission)
            }
            
            # Output value (efficiency score)
            efficiency_score = self._calculate_efficiency_score(duration, area_covered, discoveries)
            
            # Create data point
            data_point = LearningDataPoint(
                timestamp=datetime.utcnow(),
                mission_id=mission.mission_id,
                drone_id=None,
                metric_type=PerformanceMetric.MISSION_EFFICIENCY,
                input_features=input_features,
                output_value=efficiency_score,
                context={"mission_type": mission.mission_type, "status": mission.status}
            )
            
            self.learning_data.append(data_point)
            
        except Exception as e:
            logger.error(f"Failed to collect mission efficiency data: {e}")

    async def _collect_battery_optimization_data(self, mission: Mission, db: Session):
        """Collect battery optimization learning data."""
        try:
            if not mission.drones:
                return
                
            for mission_drone in mission.drones:
                drone = mission_drone.drone
                if not drone:
                    continue
                
                # Input features
                input_features = {
                    "flight_duration": (mission.updated_at - mission.created_at).total_seconds() / 3600,
                    "distance_traveled": self._estimate_distance_traveled(mission),
                    "altitude": mission.altitude or 50,
                    "weather_wind": 0,  # Would come from weather service
                    "payload_weight": 0,  # Would come from drone specs
                    "battery_capacity": drone.battery_capacity or 100
                }
                
                # Output value (battery efficiency)
                battery_efficiency = self._calculate_battery_efficiency(drone, mission)
                
                # Create data point
                data_point = LearningDataPoint(
                    timestamp=datetime.utcnow(),
                    mission_id=mission.mission_id,
                    drone_id=drone.drone_id,
                    metric_type=PerformanceMetric.BATTERY_OPTIMIZATION,
                    input_features=input_features,
                    output_value=battery_efficiency,
                    context={"drone_model": drone.model, "mission_type": mission.mission_type}
                )
                
                self.learning_data.append(data_point)
                
        except Exception as e:
            logger.error(f"Failed to collect battery optimization data: {e}")

    async def _collect_discovery_accuracy_data(self, mission: Mission, db: Session):
        """Collect discovery accuracy learning data."""
        try:
            discoveries = db.query(Discovery).filter(Discovery.mission_id == mission.id).all()
            
            for discovery in discoveries:
                # Input features
                input_features = {
                    "drone_altitude": mission.altitude or 50,
                    "weather_visibility": 10000,  # Default
                    "time_of_day": self._calculate_time_of_day(mission.created_at),
                    "terrain_type": self._get_terrain_type(mission),
                    "camera_resolution": 1920,  # Default
                    "gimbal_stabilization": 1,  # Boolean as int
                    "discovery_type": self._encode_discovery_type(discovery.discovery_type)
                }
                
                # Output value (confidence score)
                confidence_score = discovery.confidence or 0.0
                
                # Create data point
                data_point = LearningDataPoint(
                    timestamp=datetime.utcnow(),
                    mission_id=mission.mission_id,
                    drone_id=discovery.drone_id,
                    metric_type=PerformanceMetric.DISCOVERY_ACCURACY,
                    input_features=input_features,
                    output_value=confidence_score,
                    context={"discovery_type": discovery.discovery_type, "status": discovery.status}
                )
                
                self.learning_data.append(data_point)
                
        except Exception as e:
            logger.error(f"Failed to collect discovery accuracy data: {e}")

    async def _collect_flight_path_data(self, mission: Mission, db: Session):
        """Collect flight path optimization learning data."""
        try:
            if not mission.drones:
                return
                
            for mission_drone in mission.drones:
                drone = mission_drone.drone
                if not drone:
                    continue
                
                # Input features
                input_features = {
                    "area_size": mission.area_size or 0,
                    "terrain_complexity": self._calculate_terrain_complexity(mission),
                    "weather_wind": 0,  # Would come from weather service
                    "drone_speed": drone.cruise_speed or 10,
                    "search_pattern": self._encode_search_pattern(mission),
                    "obstacle_density": self._estimate_obstacle_density(mission)
                }
                
                # Output value (path efficiency)
                path_efficiency = self._calculate_path_efficiency(mission, drone)
                
                # Create data point
                data_point = LearningDataPoint(
                    timestamp=datetime.utcnow(),
                    mission_id=mission.mission_id,
                    drone_id=drone.drone_id,
                    metric_type=PerformanceMetric.FLIGHT_PATH_OPTIMIZATION,
                    input_features=input_features,
                    output_value=path_efficiency,
                    context={"search_pattern": mission.search_pattern, "drone_model": drone.model}
                )
                
                self.learning_data.append(data_point)
                
        except Exception as e:
            logger.error(f"Failed to collect flight path data: {e}")

    def _calculate_terrain_complexity(self, mission: Mission) -> float:
        """Calculate terrain complexity score."""
        # Simple implementation - would be more sophisticated in reality
        if mission.terrain_type == "urban":
            return 0.8
        elif mission.terrain_type == "mountainous":
            return 0.9
        elif mission.terrain_type == "forest":
            return 0.7
        elif mission.terrain_type == "coastal":
            return 0.6
        else:
            return 0.3

    def _calculate_urgency_level(self, mission: Mission) -> float:
        """Calculate urgency level score."""
        if mission.priority == "critical":
            return 1.0
        elif mission.priority == "high":
            return 0.7
        elif mission.priority == "medium":
            return 0.4
        else:
            return 0.1

    def _calculate_efficiency_score(self, duration: float, area_covered: float, discoveries: int) -> float:
        """Calculate mission efficiency score."""
        if duration <= 0 or area_covered <= 0:
            return 0.0
        
        # Efficiency = (discoveries * area_covered) / duration
        efficiency = (discoveries * area_covered) / duration
        
        # Normalize to 0-1 range
        return min(1.0, efficiency / 1000)

    def _estimate_distance_traveled(self, mission: Mission) -> float:
        """Estimate distance traveled during mission."""
        # Simple estimation based on area size
        area_size = mission.area_size or 1.0
        return math.sqrt(area_size) * 1000  # Rough estimate in meters

    def _calculate_battery_efficiency(self, drone: Drone, mission: Mission) -> float:
        """Calculate battery efficiency for a drone."""
        # Simple calculation - would be more sophisticated in reality
        flight_time = (mission.updated_at - mission.created_at).total_seconds() / 3600
        battery_used = 100 - (drone.battery_level or 100)
        
        if flight_time <= 0:
            return 0.0
        
        efficiency = battery_used / flight_time
        return min(1.0, efficiency / 50)  # Normalize

    def _calculate_time_of_day(self, timestamp: datetime) -> float:
        """Calculate time of day as a normalized value."""
        hour = timestamp.hour
        # Normalize to 0-1 range (0 = midnight, 0.5 = noon, 1 = midnight)
        return (hour % 24) / 24.0

    def _get_terrain_type(self, mission: Mission) -> float:
        """Get terrain type as encoded value."""
        terrain_map = {
            "urban": 0.8,
            "mountainous": 0.9,
            "forest": 0.7,
            "coastal": 0.6,
            "rural": 0.3,
            "desert": 0.4
        }
        return terrain_map.get(mission.terrain_type, 0.5)

    def _encode_discovery_type(self, discovery_type: str) -> float:
        """Encode discovery type as numerical value."""
        type_map = {
            "person": 1.0,
            "vehicle": 0.8,
            "structure": 0.6,
            "signal": 0.9,
            "animal": 0.4,
            "debris": 0.3,
            "other": 0.5
        }
        return type_map.get(discovery_type, 0.5)

    def _encode_search_pattern(self, mission: Mission) -> float:
        """Encode search pattern as numerical value."""
        pattern_map = {
            "grid": 0.8,
            "spiral": 0.6,
            "concentric": 0.7,
            "lawnmower": 0.9,
            "adaptive": 1.0
        }
        return pattern_map.get(mission.search_pattern, 0.5)

    def _estimate_obstacle_density(self, mission: Mission) -> float:
        """Estimate obstacle density in mission area."""
        # Simple estimation based on terrain type
        if mission.terrain_type == "urban":
            return 0.9
        elif mission.terrain_type == "forest":
            return 0.7
        elif mission.terrain_type == "mountainous":
            return 0.8
        else:
            return 0.2

    def _calculate_path_efficiency(self, mission: Mission, drone: Drone) -> float:
        """Calculate flight path efficiency."""
        # Simple calculation - would be more sophisticated in reality
        area_size = mission.area_size or 1.0
        flight_time = (mission.updated_at - mission.created_at).total_seconds() / 3600
        
        if flight_time <= 0:
            return 0.0
        
        # Efficiency = area_covered / (flight_time * drone_speed)
        drone_speed = drone.cruise_speed or 10
        efficiency = area_size / (flight_time * drone_speed)
        
        return min(1.0, efficiency / 10)  # Normalize

    async def _update_learning_models(self):
        """Update learning models with new data."""
        try:
            for model_id, model in self.learning_models.items():
                # Check if model needs updating
                if datetime.utcnow() - model.last_trained < self.model_update_interval:
                    continue
                
                # Get relevant training data
                training_data = [
                    dp for dp in self.learning_data
                    if dp.metric_type == model.metric_type
                ]
                
                if len(training_data) < self.min_training_data:
                    continue
                
                # Update model based on algorithm
                if model.algorithm == LearningAlgorithm.REINFORCEMENT_LEARNING:
                    await self._update_reinforcement_learning_model(model, training_data)
                elif model.algorithm == LearningAlgorithm.SUPERVISED_LEARNING:
                    await self._update_supervised_learning_model(model, training_data)
                elif model.algorithm == LearningAlgorithm.DEEP_LEARNING:
                    await self._update_deep_learning_model(model, training_data)
                
                # Update model metadata
                model.last_trained = datetime.utcnow()
                model.training_data_count = len(training_data)
                
                logger.info(f"Updated model {model_id} with {len(training_data)} data points")
                
        except Exception as e:
            logger.error(f"Failed to update learning models: {e}")

    async def _update_reinforcement_learning_model(self, model: LearningModel, training_data: List[LearningDataPoint]):
        """Update reinforcement learning model."""
        try:
            # Simple Q-learning update
            learning_rate = model.model_parameters.get("learning_rate", 0.01)
            exploration_rate = model.model_parameters.get("exploration_rate", 0.1)
            
            # Calculate average performance improvement
            if len(training_data) >= 10:
                recent_data = training_data[-10:]
                avg_performance = np.mean([dp.output_value for dp in recent_data])
                
                # Update model parameters based on performance
                if avg_performance > 0.7:
                    # Good performance - reduce exploration
                    model.model_parameters["exploration_rate"] = max(0.05, exploration_rate * 0.9)
                else:
                    # Poor performance - increase exploration
                    model.model_parameters["exploration_rate"] = min(0.3, exploration_rate * 1.1)
                
                # Update accuracy based on recent performance
                model.accuracy = min(0.95, model.accuracy + (avg_performance - 0.5) * learning_rate)
                
        except Exception as e:
            logger.error(f"Failed to update reinforcement learning model: {e}")

    async def _update_supervised_learning_model(self, model: LearningModel, training_data: List[LearningDataPoint]):
        """Update supervised learning model."""
        try:
            # Simple linear regression update
            learning_rate = model.model_parameters.get("learning_rate", 0.005)
            regularization = model.model_parameters.get("regularization", 0.01)
            
            if len(training_data) >= 20:
                # Calculate feature weights using simple linear regression
                X = np.array([[dp.input_features.get(f"feature_{i}", 0) for i in range(6)] for dp in training_data[-20:]])
                y = np.array([dp.output_value for dp in training_data[-20:]])
                
                # Simple gradient descent update
                if X.shape[0] > 0 and X.shape[1] > 0:
                    # Calculate predictions
                    weights = model.model_parameters.get("weights", np.zeros(X.shape[1]))
                    predictions = np.dot(X, weights)
                    
                    # Calculate error
                    error = y - predictions
                    
                    # Update weights
                    gradient = np.dot(X.T, error) / len(y)
                    weights = weights + learning_rate * gradient - regularization * weights
                    
                    model.model_parameters["weights"] = weights.tolist()
                    
                    # Update accuracy
                    mse = np.mean(error ** 2)
                    model.accuracy = max(0.0, min(0.95, 1.0 - mse))
                
        except Exception as e:
            logger.error(f"Failed to update supervised learning model: {e}")

    async def _update_deep_learning_model(self, model: LearningModel, training_data: List[LearningDataPoint]):
        """Update deep learning model."""
        try:
            # Simple neural network update simulation
            layers = model.model_parameters.get("layers", 3)
            neurons = model.model_parameters.get("neurons", 128)
            dropout = model.model_parameters.get("dropout", 0.2)
            
            if len(training_data) >= 50:
                # Simulate neural network training
                recent_data = training_data[-50:]
                avg_performance = np.mean([dp.output_value for dp in recent_data])
                
                # Update model complexity based on performance
                if avg_performance > 0.8:
                    # Good performance - maintain current complexity
                    pass
                elif avg_performance > 0.6:
                    # Moderate performance - slightly increase complexity
                    model.model_parameters["neurons"] = min(256, neurons + 16)
                else:
                    # Poor performance - increase complexity significantly
                    model.model_parameters["neurons"] = min(512, neurons + 32)
                    model.model_parameters["layers"] = min(5, layers + 1)
                
                # Update accuracy
                model.accuracy = min(0.95, model.accuracy + (avg_performance - 0.5) * 0.01)
                
        except Exception as e:
            logger.error(f"Failed to update deep learning model: {e}")

    async def _generate_performance_improvements(self):
        """Generate performance improvement recommendations."""
        try:
            self.performance_improvements.clear()
            
            for metric in PerformanceMetric:
                # Get recent data for this metric
                recent_data = [
                    dp for dp in self.learning_data[-100:]  # Last 100 data points
                    if dp.metric_type == metric
                ]
                
                if len(recent_data) < 10:
                    continue
                
                # Calculate current performance
                current_performance = np.mean([dp.output_value for dp in recent_data[-10:]])
                
                # Get model prediction
                model = self._get_model_for_metric(metric)
                if model:
                    predicted_performance = await self._predict_performance(model, recent_data[-1])
                    
                    # Calculate improvement potential
                    improvement = predicted_performance - current_performance
                    improvement_percentage = (improvement / current_performance) * 100 if current_performance > 0 else 0
                    
                    if improvement_percentage > 5:  # Only suggest improvements > 5%
                        recommendations = await self._generate_improvement_recommendations(metric, improvement_percentage)
                        
                        improvement = PerformanceImprovement(
                            improvement_id=f"{metric.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                            metric_type=metric,
                            current_value=current_performance,
                            predicted_value=predicted_performance,
                            improvement_percentage=improvement_percentage,
                            confidence=model.accuracy,
                            recommendations=recommendations,
                            implementation_priority=self._calculate_priority(improvement_percentage, model.accuracy)
                        )
                        
                        self.performance_improvements.append(improvement)
            
            # Store improvement history
            for improvement in self.performance_improvements:
                self.improvement_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "improvement_id": improvement.improvement_id,
                    "metric_type": improvement.metric_type.value,
                    "improvement_percentage": improvement.improvement_percentage,
                    "confidence": improvement.confidence,
                    "priority": improvement.implementation_priority
                })
            
            # Keep only last 1000 improvements
            if len(self.improvement_history) > 1000:
                self.improvement_history = self.improvement_history[-1000:]
                
        except Exception as e:
            logger.error(f"Failed to generate performance improvements: {e}")

    def _get_model_for_metric(self, metric: PerformanceMetric) -> Optional[LearningModel]:
        """Get the learning model for a specific metric."""
        for model in self.learning_models.values():
            if model.metric_type == metric:
                return model
        return None

    async def _predict_performance(self, model: LearningModel, data_point: LearningDataPoint) -> float:
        """Predict performance using a learning model."""
        try:
            if model.algorithm == LearningAlgorithm.REINFORCEMENT_LEARNING:
                # Simple Q-value prediction
                base_performance = 0.5
                exploration_bonus = model.model_parameters.get("exploration_rate", 0.1) * 0.1
                return min(1.0, base_performance + exploration_bonus)
                
            elif model.algorithm == LearningAlgorithm.SUPERVISED_LEARNING:
                # Linear regression prediction
                weights = model.model_parameters.get("weights", [0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
                features = [data_point.input_features.get(f"feature_{i}", 0) for i in range(len(weights))]
                prediction = sum(w * f for w, f in zip(weights, features))
                return max(0.0, min(1.0, prediction))
                
            elif model.algorithm == LearningAlgorithm.DEEP_LEARNING:
                # Neural network prediction simulation
                base_performance = 0.6
                complexity_bonus = model.model_parameters.get("neurons", 128) / 1000
                return min(1.0, base_performance + complexity_bonus)
                
            else:
                return 0.5  # Default prediction
                
        except Exception as e:
            logger.error(f"Failed to predict performance: {e}")
            return 0.5

    async def _generate_improvement_recommendations(self, metric: PerformanceMetric, improvement_percentage: float) -> List[str]:
        """Generate improvement recommendations for a metric."""
        recommendations = []
        
        if metric == PerformanceMetric.MISSION_EFFICIENCY:
            if improvement_percentage > 20:
                recommendations.append("Consider using adaptive search patterns for better area coverage")
                recommendations.append("Optimize drone assignment based on individual capabilities")
            elif improvement_percentage > 10:
                recommendations.append("Adjust mission duration based on area complexity")
                recommendations.append("Implement dynamic waypoint optimization")
            else:
                recommendations.append("Fine-tune search pattern parameters")
                
        elif metric == PerformanceMetric.BATTERY_OPTIMIZATION:
            if improvement_percentage > 15:
                recommendations.append("Implement intelligent battery management algorithms")
                recommendations.append("Optimize flight paths to reduce energy consumption")
            elif improvement_percentage > 8:
                recommendations.append("Adjust cruise speeds based on mission requirements")
                recommendations.append("Implement predictive battery usage models")
            else:
                recommendations.append("Monitor battery usage patterns more closely")
                
        elif metric == PerformanceMetric.DISCOVERY_ACCURACY:
            if improvement_percentage > 25:
                recommendations.append("Upgrade computer vision models for better object detection")
                recommendations.append("Implement multi-sensor fusion for improved accuracy")
            elif improvement_percentage > 12:
                recommendations.append("Optimize camera settings based on environmental conditions")
                recommendations.append("Implement confidence-based filtering")
            else:
                recommendations.append("Fine-tune detection thresholds")
                
        elif metric == PerformanceMetric.FLIGHT_PATH_OPTIMIZATION:
            if improvement_percentage > 18:
                recommendations.append("Implement dynamic path planning based on real-time conditions")
                recommendations.append("Use machine learning for optimal waypoint selection")
            elif improvement_percentage > 9:
                recommendations.append("Optimize search patterns for specific terrain types")
                recommendations.append("Implement obstacle avoidance algorithms")
            else:
                recommendations.append("Adjust flight altitude for better efficiency")
                
        return recommendations

    def _calculate_priority(self, improvement_percentage: float, confidence: float) -> str:
        """Calculate implementation priority based on improvement and confidence."""
        score = improvement_percentage * confidence
        
        if score > 20:
            return "critical"
        elif score > 12:
            return "high"
        elif score > 6:
            return "medium"
        else:
            return "low"

    async def get_learning_insights(self) -> LearningInsights:
        """Get comprehensive learning system insights."""
        try:
            total_models = len(self.learning_models)
            active_models = sum(1 for model in self.learning_models.values() 
                              if datetime.utcnow() - model.last_trained < timedelta(days=7))
            
            average_accuracy = np.mean([model.accuracy for model in self.learning_models.values()]) if self.learning_models else 0.0
            
            total_improvements = len(self.performance_improvements)
            
            # Calculate performance trends
            performance_trends = {}
            for metric in PerformanceMetric:
                recent_data = [dp for dp in self.learning_data[-50:] if dp.metric_type == metric]
                if len(recent_data) >= 10:
                    old_avg = np.mean([dp.output_value for dp in recent_data[:10]])
                    new_avg = np.mean([dp.output_value for dp in recent_data[-10:]])
                    trend = ((new_avg - old_avg) / old_avg) * 100 if old_avg > 0 else 0
                    performance_trends[metric.value] = trend
            
            # Get top improvements
            top_improvements = sorted(
                self.performance_improvements,
                key=lambda x: x.improvement_percentage * x.confidence,
                reverse=True
            )[:5]
            
            # Generate learning recommendations
            learning_recommendations = await self._generate_learning_recommendations()
            
            return LearningInsights(
                total_models=total_models,
                active_models=active_models,
                average_accuracy=average_accuracy,
                total_improvements=total_improvements,
                performance_trends=performance_trends,
                top_improvements=top_improvements,
                learning_recommendations=learning_recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to get learning insights: {e}")
            return LearningInsights(
                total_models=0,
                active_models=0,
                average_accuracy=0.0,
                total_improvements=0,
                performance_trends={},
                top_improvements=[],
                learning_recommendations=["Learning system initialization in progress"]
            )

    async def _generate_learning_recommendations(self) -> List[str]:
        """Generate learning system recommendations."""
        recommendations = []
        
        # Check model performance
        for model in self.learning_models.values():
            if model.accuracy < 0.6:
                recommendations.append(f"Model {model.model_id} has low accuracy ({model.accuracy:.2f}). Consider retraining with more data.")
            
            if datetime.utcnow() - model.last_trained > timedelta(days=7):
                recommendations.append(f"Model {model.model_id} hasn't been updated recently. Consider updating with new data.")
        
        # Check data quality
        if len(self.learning_data) < 100:
            recommendations.append("Limited training data available. Consider running more missions to improve learning.")
        
        # Check improvement opportunities
        if len(self.performance_improvements) == 0:
            recommendations.append("No significant improvement opportunities identified. System is performing well.")
        elif len(self.performance_improvements) > 10:
            recommendations.append("Multiple improvement opportunities available. Consider implementing high-priority improvements.")
        
        # Check learning system health
        if not self.learning_enabled:
            recommendations.append("Learning system is disabled. Enable learning for continuous improvement.")
        
        return recommendations

    async def apply_improvement(self, improvement_id: str) -> bool:
        """Apply a specific performance improvement."""
        try:
            improvement = next(
                (imp for imp in self.performance_improvements if imp.improvement_id == improvement_id),
                None
            )
            
            if not improvement:
                return False
            
            # Apply improvement based on metric type
            if improvement.metric_type == PerformanceMetric.MISSION_EFFICIENCY:
                await self._apply_mission_efficiency_improvement(improvement)
            elif improvement.metric_type == PerformanceMetric.BATTERY_OPTIMIZATION:
                await self._apply_battery_optimization_improvement(improvement)
            elif improvement.metric_type == PerformanceMetric.DISCOVERY_ACCURACY:
                await self._apply_discovery_accuracy_improvement(improvement)
            elif improvement.metric_type == PerformanceMetric.FLIGHT_PATH_OPTIMIZATION:
                await self._apply_flight_path_improvement(improvement)
            
            # Update adaptive planner with new parameters
            await self._update_adaptive_planner_parameters(improvement)
            
            logger.info(f"Applied improvement {improvement_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply improvement {improvement_id}: {e}")
            return False

    async def _apply_mission_efficiency_improvement(self, improvement: PerformanceImprovement):
        """Apply mission efficiency improvement."""
        # Update optimization weights in adaptive planner
        new_weights = {
            'time_efficiency': 0.35,  # Increase time efficiency weight
            'coverage_quality': 0.3,  # Increase coverage weight
            'battery_conservation': 0.2,
            'safety_margin': 0.1,
            'weather_adaptation': 0.05
        }
        await adaptive_planner.update_optimization_weights(new_weights)

    async def _apply_battery_optimization_improvement(self, improvement: PerformanceImprovement):
        """Apply battery optimization improvement."""
        # Update battery-related parameters
        new_weights = {
            'time_efficiency': 0.2,
            'coverage_quality': 0.25,
            'battery_conservation': 0.35,  # Increase battery conservation weight
            'safety_margin': 0.15,
            'weather_adaptation': 0.05
        }
        await adaptive_planner.update_optimization_weights(new_weights)

    async def _apply_discovery_accuracy_improvement(self, improvement: PerformanceImprovement):
        """Apply discovery accuracy improvement."""
        # Update discovery-related parameters
        new_weights = {
            'time_efficiency': 0.25,
            'coverage_quality': 0.4,  # Increase coverage quality for better discovery
            'battery_conservation': 0.2,
            'safety_margin': 0.1,
            'weather_adaptation': 0.05
        }
        await adaptive_planner.update_optimization_weights(new_weights)

    async def _apply_flight_path_improvement(self, improvement: PerformanceImprovement):
        """Apply flight path optimization improvement."""
        # Update path-related parameters
        new_weights = {
            'time_efficiency': 0.3,
            'coverage_quality': 0.3,
            'battery_conservation': 0.25,
            'safety_margin': 0.1,
            'weather_adaptation': 0.05
        }
        await adaptive_planner.update_optimization_weights(new_weights)

    async def _update_adaptive_planner_parameters(self, improvement: PerformanceImprovement):
        """Update adaptive planner parameters based on improvement."""
        # This would update the adaptive planner with new parameters
        # based on the learning system's recommendations
        pass

    async def get_performance_improvements(self, limit: int = 20) -> List[PerformanceImprovement]:
        """Get performance improvement recommendations."""
        return sorted(
            self.performance_improvements,
            key=lambda x: x.improvement_percentage * x.confidence,
            reverse=True
        )[:limit]

    async def get_learning_models(self) -> Dict[str, LearningModel]:
        """Get all learning models."""
        return self.learning_models

    async def get_learning_data_summary(self) -> Dict[str, Any]:
        """Get summary of learning data."""
        return {
            "total_data_points": len(self.learning_data),
            "data_by_metric": {
                metric.value: len([dp for dp in self.learning_data if dp.metric_type == metric])
                for metric in PerformanceMetric
            },
            "recent_data_points": len([dp for dp in self.learning_data if dp.timestamp >= datetime.utcnow() - timedelta(hours=24)]),
            "data_quality_score": self._calculate_data_quality_score()
        }

    def _calculate_data_quality_score(self) -> float:
        """Calculate data quality score."""
        if not self.learning_data:
            return 0.0
        
        # Simple data quality assessment
        recent_data = [dp for dp in self.learning_data if dp.timestamp >= datetime.utcnow() - timedelta(hours=24)]
        
        if len(recent_data) < 10:
            return 0.3
        elif len(recent_data) < 50:
            return 0.6
        else:
            return 0.9

    async def disable_learning(self):
        """Disable the learning system."""
        self.learning_enabled = False
        logger.info("Learning system disabled")

    async def enable_learning(self):
        """Enable the learning system."""
        self.learning_enabled = True
        logger.info("Learning system enabled")

    async def reset_learning_models(self):
        """Reset all learning models."""
        self.learning_models.clear()
        self.learning_data.clear()
        self.performance_improvements.clear()
        self.improvement_history.clear()
        
        # Reinitialize with default models
        await self._load_existing_models()
        
        logger.info("Learning models reset")


# Global instance
learning_system = LearningSystem()
