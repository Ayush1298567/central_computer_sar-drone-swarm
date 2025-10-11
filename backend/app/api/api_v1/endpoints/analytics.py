import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.core.database import get_db
from app.services.analytics_engine import analytics_engine
from app.services.analytics_engine import MissionMetrics, SystemMetrics
from enum import Enum

class MetricType(Enum):
    MISSION_EFFICIENCY = "mission_efficiency"
    DRONE_UTILIZATION = "drone_utilization"
    DISCOVERY_RATE = "discovery_rate"
    BATTERY_CONSUMPTION = "battery_consumption"
    WEATHER_IMPACT = "weather_impact"

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/missions/{mission_id}/analytics", response_model=Dict[str, Any])
async def get_mission_analytics_endpoint(
    mission_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for a specific mission.
    """
    try:
        metrics = analytics_engine.get_mission_analytics(mission_id)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found or no analytics available")
        
        return JSONResponse(content={
            "success": True,
            "mission_id": mission_id,
            "analytics": {
                "total_duration": metrics.total_duration,
                "area_covered": metrics.area_covered,
                "discoveries_found": metrics.discoveries_found,
                "average_discovery_confidence": metrics.average_discovery_confidence,
                "mission_efficiency_score": metrics.mission_efficiency_score,
                "battery_consumption": metrics.battery_consumption,
                "drone_utilization": metrics.drone_utilization,
                "weather_impact": metrics.weather_impact,
                "completion_rate": metrics.completion_rate
            }
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting mission analytics for {mission_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get mission analytics: {e}")

@router.get("/drones/{drone_id}/analytics", response_model=Dict[str, Any])
async def get_drone_analytics_endpoint(
    drone_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for a specific drone over a given period.
    """
    try:
        metrics = analytics_engine.get_drone_analytics(drone_id, days)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found or no analytics available")
        
        return JSONResponse(content={
            "success": True,
            "drone_id": drone_id,
            "period_days": days,
            "analytics": {
                "total_flight_time": metrics.total_flight_time,
                "average_battery_efficiency": metrics.average_battery_efficiency,
                "discovery_contribution": metrics.discovery_contribution,
                "reliability_score": metrics.reliability_score,
                "maintenance_frequency": metrics.maintenance_frequency,
                "average_speed": metrics.average_speed,
                "altitude_efficiency": metrics.altitude_efficiency
            }
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting drone analytics for {drone_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get drone analytics: {e}")

@router.get("/system/analytics", response_model=Dict[str, Any])
async def get_system_analytics_endpoint(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for the entire system over a given period.
    """
    try:
        analytics = analytics_engine.get_system_analytics(days)
        
        return JSONResponse(content={
            "success": True,
            "period_days": days,
            "analytics": {
                "total_missions": analytics.total_missions,
                "successful_missions": analytics.successful_missions,
                "average_mission_duration": analytics.average_mission_duration,
                "total_discoveries": analytics.total_discoveries,
                "system_uptime": analytics.system_uptime,
                "average_drone_utilization": analytics.average_drone_utilization,
                "peak_performance_period": analytics.peak_performance_period,
                "improvement_areas": analytics.improvement_areas
            }
        })
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get system analytics: {e}")

@router.get("/trends/{metric_type}", response_model=Dict[str, Any])
async def get_performance_trends_endpoint(
    metric_type: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get performance trends for a specific metric type over time.
    
    Available metric types:
    - mission_efficiency
    - drone_performance
    - discovery_rate
    - battery_usage
    - coverage_area
    - response_time
    """
    try:
        # Validate metric type
        try:
            metric_enum = MetricType(metric_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid metric type. Available types: {[m.value for m in MetricType]}"
            )
        
        trends = analytics_engine.get_performance_trends(metric_enum, days)
        
        return JSONResponse(content={
            "success": True,
            "metric_type": metric_type,
            "period_days": days,
            "trends": trends
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting performance trends for {metric_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get performance trends: {e}")

@router.get("/missions/{mission_id}/summary", response_model=Dict[str, Any])
async def get_mission_summary_endpoint(
    mission_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a summary of mission performance with key metrics and insights.
    """
    try:
        metrics = analytics_engine.get_mission_analytics(mission_id)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found or no analytics available")
        
        # Generate summary insights
        insights = []
        
        if metrics.mission_efficiency_score > 0.8:
            insights.append("Excellent mission efficiency")
        elif metrics.mission_efficiency_score > 0.6:
            insights.append("Good mission efficiency")
        else:
            insights.append("Mission efficiency needs improvement")
        
        if metrics.discoveries_found > 0:
            insights.append(f"Found {metrics.discoveries_found} discoveries")
        else:
            insights.append("No discoveries found")
        
        if metrics.battery_consumption > 80:
            insights.append("High battery consumption")
        elif metrics.battery_consumption < 30:
            insights.append("Efficient battery usage")
        
        if metrics.weather_impact > 0.5:
            insights.append("Weather conditions affected mission")
        
        # Calculate performance grade
        if metrics.mission_efficiency_score > 0.8 and metrics.discoveries_found > 0:
            grade = "A"
        elif metrics.mission_efficiency_score > 0.6:
            grade = "B"
        elif metrics.mission_efficiency_score > 0.4:
            grade = "C"
        else:
            grade = "D"
        
        return JSONResponse(content={
            "success": True,
            "mission_id": mission_id,
            "summary": {
                "performance_grade": grade,
                "key_metrics": {
                    "efficiency_score": metrics.mission_efficiency_score,
                    "discoveries_found": metrics.discoveries_found,
                    "duration_minutes": metrics.total_duration,
                    "area_covered_sqm": metrics.area_covered,
                    "battery_consumption_percent": metrics.battery_consumption
                },
                "insights": insights,
                "recommendations": [
                    "Consider optimizing search patterns for better coverage",
                    "Monitor battery usage to improve efficiency",
                    "Review weather conditions for future missions"
                ]
            }
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting mission summary for {mission_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get mission summary: {e}")

@router.get("/drones/{drone_id}/performance", response_model=Dict[str, Any])
async def get_drone_performance_endpoint(
    drone_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get detailed performance analysis for a specific drone.
    """
    try:
        metrics = analytics_engine.get_drone_analytics(drone_id, days)
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found or no analytics available")
        
        # Generate performance insights
        insights = []
        
        if metrics.reliability_score > 0.9:
            insights.append("Excellent reliability")
        elif metrics.reliability_score > 0.7:
            insights.append("Good reliability")
        else:
            insights.append("Reliability needs improvement")
        
        if metrics.average_battery_efficiency > 0.8:
            insights.append("Efficient battery usage")
        elif metrics.average_battery_efficiency < 0.5:
            insights.append("Battery efficiency needs improvement")
        
        if metrics.discovery_contribution > 5:
            insights.append("High discovery contribution")
        elif metrics.discovery_contribution == 0:
            insights.append("No discoveries made")
        
        if metrics.maintenance_frequency > 2:
            insights.append("High maintenance frequency")
        elif metrics.maintenance_frequency < 0.5:
            insights.append("Low maintenance requirements")
        
        # Calculate performance score
        performance_score = (
            metrics.reliability_score * 0.3 +
            metrics.average_battery_efficiency * 0.25 +
            min(1.0, metrics.discovery_contribution / 10.0) * 0.25 +
            max(0.0, 1.0 - metrics.maintenance_frequency / 5.0) * 0.2
        )
        
        return JSONResponse(content={
            "success": True,
            "drone_id": drone_id,
            "period_days": days,
            "performance": {
                "performance_score": performance_score,
                "key_metrics": {
                    "reliability_score": metrics.reliability_score,
                    "battery_efficiency": metrics.average_battery_efficiency,
                    "discovery_contribution": metrics.discovery_contribution,
                    "maintenance_frequency": metrics.maintenance_frequency,
                    "average_speed": metrics.average_speed,
                    "altitude_efficiency": metrics.altitude_efficiency,
                    "total_flight_time": metrics.total_flight_time
                },
                "insights": insights,
                "recommendations": [
                    "Monitor battery usage patterns",
                    "Schedule regular maintenance checks",
                    "Optimize flight parameters for better efficiency"
                ]
            }
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting drone performance for {drone_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get drone performance: {e}")

@router.get("/system/health", response_model=Dict[str, Any])
async def get_system_health_endpoint(
    db: Session = Depends(get_db)
):
    """
    Get overall system health assessment.
    """
    try:
        analytics = analytics_engine.get_system_analytics(30)  # Last 30 days
        
        # Calculate health score
        health_factors = []
        health_score = 0.0
        
        # Mission success rate
        if analytics.total_missions > 0:
            success_rate = analytics.successful_missions / analytics.total_missions
            health_score += success_rate * 0.3
            if success_rate > 0.8:
                health_factors.append("High mission success rate")
            elif success_rate < 0.5:
                health_factors.append("Low mission success rate")
        
        # System uptime
        health_score += analytics.system_uptime * 0.25
        if analytics.system_uptime > 0.9:
            health_factors.append("Excellent system uptime")
        elif analytics.system_uptime < 0.7:
            health_factors.append("System uptime needs improvement")
        
        # Drone utilization
        health_score += analytics.average_drone_utilization * 0.2
        if analytics.average_drone_utilization > 0.8:
            health_factors.append("Good drone utilization")
        elif analytics.average_drone_utilization < 0.5:
            health_factors.append("Low drone utilization")
        
        # Discovery rate
        if analytics.total_missions > 0:
            discovery_rate = analytics.total_discoveries / analytics.total_missions
            health_score += min(1.0, discovery_rate / 2.0) * 0.15
            if discovery_rate > 1.0:
                health_factors.append("Good discovery rate")
            elif discovery_rate < 0.5:
                health_factors.append("Low discovery rate")
        
        # Mission duration efficiency
        if analytics.average_mission_duration > 0:
            duration_efficiency = max(0.0, 1.0 - (analytics.average_mission_duration - 60) / 120.0)
            health_score += duration_efficiency * 0.1
            if analytics.average_mission_duration < 90:
                health_factors.append("Efficient mission durations")
            elif analytics.average_mission_duration > 150:
                health_factors.append("Long mission durations")
        
        # Determine health status
        if health_score > 0.8:
            health_status = "excellent"
        elif health_score > 0.6:
            health_status = "good"
        elif health_score > 0.4:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return JSONResponse(content={
            "success": True,
            "health": {
                "health_score": health_score,
                "health_status": health_status,
                "health_factors": health_factors,
                "system_metrics": {
                    "total_missions": analytics.total_missions,
                    "successful_missions": analytics.successful_missions,
                    "system_uptime": analytics.system_uptime,
                    "average_drone_utilization": analytics.average_drone_utilization,
                    "total_discoveries": analytics.total_discoveries,
                    "average_mission_duration": analytics.average_mission_duration
                },
                "improvement_areas": analytics.improvement_areas,
                "recommendations": [
                    "Monitor system performance metrics regularly",
                    "Address identified improvement areas",
                    "Optimize mission planning and execution",
                    "Maintain optimal drone utilization levels"
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error getting system health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {e}")

@router.get("/discoveries/trends", response_model=Dict[str, Any])
async def get_discovery_trends_endpoint(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    type: Optional[str] = Query(None, description="Filter by discovery type"),
    db: Session = Depends(get_db)
):
    """
    Get discovery trends and patterns over time.
    """
    try:
        # This would typically use the analytics engine, but for now we'll return mock data
        # In a real implementation, this would analyze discovery patterns
        
        trends = [
            {
                "date": "2024-01-01",
                "discoveries": 5,
                "types": {"person": 2, "vehicle": 2, "debris": 1},
                "confidence_avg": 0.85
            },
            {
                "date": "2024-01-02",
                "discoveries": 3,
                "types": {"person": 1, "vehicle": 1, "debris": 1},
                "confidence_avg": 0.78
            }
        ]
        
        return JSONResponse(content={
            "success": True,
            "trends": trends,
            "summary": {
                "total_discoveries": 8,
                "average_confidence": 0.82,
                "most_common_type": "person",
                "trend_direction": "stable"
            }
        })
    except Exception as e:
        logger.error(f"Error getting discovery trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get discovery trends: {e}")

@router.get("/battery/report", response_model=Dict[str, Any])
async def get_battery_usage_report_endpoint(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    drone_id: Optional[str] = Query(None, description="Filter by specific drone"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive battery usage report.
    """
    try:
        # This would typically use the analytics engine, but for now we'll return mock data
        # In a real implementation, this would analyze battery usage patterns
        
        report = {
            "summary": {
                "total_flight_time": 120.5,
                "average_battery_consumption": 65.2,
                "most_efficient_drone": "drone-001",
                "least_efficient_drone": "drone-003"
            },
            "drone_breakdown": [
                {
                    "drone_id": "drone-001",
                    "flight_time": 45.2,
                    "battery_consumption": 58.1,
                    "efficiency_score": 0.92
                },
                {
                    "drone_id": "drone-002",
                    "flight_time": 38.7,
                    "battery_consumption": 62.3,
                    "efficiency_score": 0.88
                },
                {
                    "drone_id": "drone-003",
                    "flight_time": 36.6,
                    "battery_consumption": 75.2,
                    "efficiency_score": 0.76
                }
            ],
            "recommendations": [
                "Optimize flight patterns for drone-003",
                "Schedule charging breaks for better battery health",
                "Monitor battery degradation over time"
            ]
        }
        
        return JSONResponse(content={
            "success": True,
            "report": report
        })
    except Exception as e:
        logger.error(f"Error getting battery usage report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get battery usage report: {e}")