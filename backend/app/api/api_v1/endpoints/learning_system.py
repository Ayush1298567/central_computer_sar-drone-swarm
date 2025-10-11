"""
Learning System API endpoints for performance improvement algorithms.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.services.learning_system import (
    learning_system,
    LearningAlgorithm,
    PerformanceMetric,
    LearningModel,
    PerformanceImprovement,
    LearningInsights
)
from ....core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/insights")
async def get_learning_insights(db: Session = Depends(get_db)):
    """
    Get comprehensive learning system insights.
    
    Returns:
        LearningInsights with system performance and recommendations
    """
    try:
        insights = await learning_system.get_learning_insights()
        
        return {
            "success": True,
            "insights": {
                "total_models": insights.total_models,
                "active_models": insights.active_models,
                "average_accuracy": insights.average_accuracy,
                "total_improvements": insights.total_improvements,
                "performance_trends": insights.performance_trends,
                "top_improvements": [
                    {
                        "improvement_id": imp.improvement_id,
                        "metric_type": imp.metric_type.value,
                        "current_value": imp.current_value,
                        "predicted_value": imp.predicted_value,
                        "improvement_percentage": imp.improvement_percentage,
                        "confidence": imp.confidence,
                        "recommendations": imp.recommendations,
                        "implementation_priority": imp.implementation_priority
                    }
                    for imp in insights.top_improvements
                ],
                "learning_recommendations": insights.learning_recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning insights")


@router.get("/models")
async def get_learning_models(db: Session = Depends(get_db)):
    """
    Get all learning models and their status.
    
    Returns:
        Dictionary of learning models with their details
    """
    try:
        models = await learning_system.get_learning_models()
        
        model_data = {}
        for model_id, model in models.items():
            model_data[model_id] = {
                "model_id": model.model_id,
                "algorithm": model.algorithm.value,
                "metric_type": model.metric_type.value,
                "accuracy": model.accuracy,
                "last_trained": model.last_trained.isoformat(),
                "training_data_count": model.training_data_count,
                "model_parameters": model.model_parameters
            }
        
        return {
            "success": True,
            "models": model_data,
            "total_models": len(models)
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning models")


@router.get("/improvements")
async def get_performance_improvements(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get performance improvement recommendations.
    
    Args:
        limit: Maximum number of improvements to return
        
    Returns:
        List of performance improvement recommendations
    """
    try:
        improvements = await learning_system.get_performance_improvements(limit)
        
        improvement_data = []
        for imp in improvements:
            improvement_data.append({
                "improvement_id": imp.improvement_id,
                "metric_type": imp.metric_type.value,
                "current_value": imp.current_value,
                "predicted_value": imp.predicted_value,
                "improvement_percentage": imp.improvement_percentage,
                "confidence": imp.confidence,
                "recommendations": imp.recommendations,
                "implementation_priority": imp.implementation_priority
            })
        
        return {
            "success": True,
            "improvements": improvement_data,
            "total_improvements": len(improvements)
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance improvements: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance improvements")


@router.post("/apply-improvement")
async def apply_improvement(
    improvement_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Apply a specific performance improvement.
    
    Args:
        improvement_id: ID of the improvement to apply
        
    Returns:
        Success status and details
    """
    try:
        success = await learning_system.apply_improvement(improvement_id)
        
        if success:
            return {
                "success": True,
                "message": f"Improvement {improvement_id} applied successfully",
                "improvement_id": improvement_id
            }
        else:
            raise HTTPException(status_code=404, detail="Improvement not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply improvement {improvement_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply improvement")


@router.get("/data-summary")
async def get_learning_data_summary(db: Session = Depends(get_db)):
    """
    Get summary of learning data.
    
    Returns:
        Learning data summary and quality metrics
    """
    try:
        summary = await learning_system.get_learning_data_summary()
        
        return {
            "success": True,
            "data_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning data summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning data summary")


@router.post("/disable-learning")
async def disable_learning(db: Session = Depends(get_db)):
    """
    Disable the learning system.
    
    Returns:
        Success status
    """
    try:
        await learning_system.disable_learning()
        
        return {
            "success": True,
            "message": "Learning system disabled successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to disable learning system: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable learning system")


@router.post("/enable-learning")
async def enable_learning(db: Session = Depends(get_db)):
    """
    Enable the learning system.
    
    Returns:
        Success status
    """
    try:
        await learning_system.enable_learning()
        
        return {
            "success": True,
            "message": "Learning system enabled successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to enable learning system: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable learning system")


@router.post("/reset-models")
async def reset_learning_models(db: Session = Depends(get_db)):
    """
    Reset all learning models.
    
    Returns:
        Success status
    """
    try:
        await learning_system.reset_learning_models()
        
        return {
            "success": True,
            "message": "Learning models reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset learning models: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset learning models")


@router.get("/algorithms")
async def get_learning_algorithms(db: Session = Depends(get_db)):
    """
    Get available learning algorithms.
    
    Returns:
        List of available learning algorithms
    """
    try:
        algorithms = [
            {
                "value": algorithm.value,
                "name": algorithm.value.replace('_', ' ').title(),
                "description": _get_algorithm_description(algorithm)
            }
            for algorithm in LearningAlgorithm
        ]
        
        return {
            "success": True,
            "algorithms": algorithms
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning algorithms: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning algorithms")


@router.get("/metrics")
async def get_performance_metrics(db: Session = Depends(get_db)):
    """
    Get available performance metrics.
    
    Returns:
        List of available performance metrics
    """
    try:
        metrics = [
            {
                "value": metric.value,
                "name": metric.value.replace('_', ' ').title(),
                "description": _get_metric_description(metric)
            }
            for metric in PerformanceMetric
        ]
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@router.post("/test-learning")
async def test_learning_system(
    test_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Test endpoint for learning system functionality.
    
    Args:
        test_data: Test parameters
        
    Returns:
        Comprehensive test results
    """
    try:
        test_results = {}
        
        # Test 1: Get learning insights
        try:
            insights = await learning_system.get_learning_insights()
            test_results['learning_insights'] = {
                'success': True,
                'total_models': insights.total_models,
                'active_models': insights.active_models,
                'average_accuracy': insights.average_accuracy
            }
        except Exception as e:
            test_results['learning_insights'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 2: Get learning models
        try:
            models = await learning_system.get_learning_models()
            test_results['learning_models'] = {
                'success': True,
                'model_count': len(models)
            }
        except Exception as e:
            test_results['learning_models'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 3: Get performance improvements
        try:
            improvements = await learning_system.get_performance_improvements(5)
            test_results['performance_improvements'] = {
                'success': True,
                'improvement_count': len(improvements)
            }
        except Exception as e:
            test_results['performance_improvements'] = {
                'success': False,
                'error': str(e)
            }
        
        # Test 4: Get data summary
        try:
            summary = await learning_system.get_learning_data_summary()
            test_results['data_summary'] = {
                'success': True,
                'total_data_points': summary['total_data_points'],
                'data_quality_score': summary['data_quality_score']
            }
        except Exception as e:
            test_results['data_summary'] = {
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
        logger.error(f"Learning system test failed: {e}")
        raise HTTPException(status_code=500, detail="Learning system test failed")


@router.get("/status")
async def get_learning_system_status(db: Session = Depends(get_db)):
    """
    Get learning system status and health.
    
    Returns:
        System status and health information
    """
    try:
        # Get basic system information
        insights = await learning_system.get_learning_insights()
        models = await learning_system.get_learning_models()
        data_summary = await learning_system.get_learning_data_summary()
        
        # Calculate system health score
        health_score = 0.0
        health_factors = []
        
        # Model health
        if insights.total_models > 0:
            model_health = insights.average_accuracy
            health_score += model_health * 0.3
            health_factors.append(f"Model accuracy: {model_health:.2f}")
        
        # Data health
        data_health = data_summary['data_quality_score']
        health_score += data_health * 0.2
        health_factors.append(f"Data quality: {data_health:.2f}")
        
        # Activity health
        if insights.total_models > 0:
            activity_health = insights.active_models / insights.total_models
            health_score += activity_health * 0.2
            health_factors.append(f"Model activity: {activity_health:.2f}")
        
        # Improvement health
        if insights.total_improvements > 0:
            improvement_health = min(1.0, insights.total_improvements / 10)
            health_score += improvement_health * 0.3
            health_factors.append(f"Improvement opportunities: {insights.total_improvements}")
        
        # Determine overall health status
        if health_score >= 0.8:
            health_status = "excellent"
        elif health_score >= 0.6:
            health_status = "good"
        elif health_score >= 0.4:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            "success": True,
            "status": {
                "health_score": health_score,
                "health_status": health_status,
                "health_factors": health_factors,
                "learning_enabled": learning_system.learning_enabled,
                "total_models": insights.total_models,
                "active_models": insights.active_models,
                "total_improvements": insights.total_improvements,
                "data_points": data_summary['total_data_points'],
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning system status")


def _get_algorithm_description(algorithm: LearningAlgorithm) -> str:
    """Get description for learning algorithm."""
    descriptions = {
        LearningAlgorithm.REINFORCEMENT_LEARNING: "Learn optimal actions through trial and error with rewards",
        LearningAlgorithm.SUPERVISED_LEARNING: "Learn from labeled training data to make predictions",
        LearningAlgorithm.UNSUPERVISED_LEARNING: "Find patterns in data without labeled examples",
        LearningAlgorithm.DEEP_LEARNING: "Use neural networks for complex pattern recognition",
        LearningAlgorithm.GENETIC_ALGORITHM: "Evolve solutions through genetic operations and selection"
    }
    return descriptions.get(algorithm, "Unknown algorithm")


def _get_metric_description(metric: PerformanceMetric) -> str:
    """Get description for performance metric."""
    descriptions = {
        PerformanceMetric.MISSION_EFFICIENCY: "Overall mission performance and resource utilization",
        PerformanceMetric.BATTERY_OPTIMIZATION: "Battery usage efficiency and power management",
        PerformanceMetric.DISCOVERY_ACCURACY: "Accuracy of object detection and discovery",
        PerformanceMetric.FLIGHT_PATH_OPTIMIZATION: "Efficiency of flight paths and navigation",
        PerformanceMetric.WEATHER_ADAPTATION: "Adaptation to weather conditions and environmental factors",
        PerformanceMetric.DRONE_COORDINATION: "Multi-drone coordination and collaboration effectiveness"
    }
    return descriptions.get(metric, "Unknown metric")
