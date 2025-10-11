"""
Analytics API endpoints for SAR Mission Commander
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..services.analytics_engine import analytics_engine
from ..utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Pydantic models for API responses
class MissionMetricsResponse(BaseModel):
    mission_id: str
    total_time_minutes: float
    area_covered_km2: float
    discoveries_found: int
    drones_used: int
    efficiency_score: float
    success_rate: float
    avg_drone_utilization: float
    cost_estimate: float

class SystemMetricsResponse(BaseModel):
    total_missions: int
    active_missions: int
    completed_missions: int
    total_discoveries: int
    avg_mission_duration: float
    system_uptime: float
    drone_fleet_size: int
    active_drones: int
    total_flight_hours: float

class PerformanceReportResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    mission_metrics: List[MissionMetricsResponse]
    system_metrics: SystemMetricsResponse
    trends: Dict[str, Any]
    recommendations: List[str]

class DiscoveryAnalyticsResponse(BaseModel):
    total_discoveries: int
    discovery_types: Dict[str, int]
    average_confidence: float
    high_confidence_discoveries: int
    verified_discoveries: int
    period_days: int

class DronePerformanceResponse(BaseModel):
    drone_id: str
    total_missions: int
    successful_missions: int
    success_rate: float
    average_mission_time_minutes: float
    total_flight_hours: float

@router.get("/missions/{mission_id}", response_model=MissionMetricsResponse)
async def get_mission_analytics(mission_id: str):
    """Get detailed analytics for a specific mission"""
    try:
        metrics = await analytics_engine.get_mission_analytics(mission_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Mission not found or no analytics available")
        
        return MissionMetricsResponse(
            mission_id=metrics.mission_id,
            total_time_minutes=metrics.total_time_minutes,
            area_covered_km2=metrics.area_covered_km2,
            discoveries_found=metrics.discoveries_found,
            drones_used=metrics.drones_used,
            efficiency_score=metrics.efficiency_score,
            success_rate=metrics.success_rate,
            avg_drone_utilization=metrics.avg_drone_utilization,
            cost_estimate=metrics.cost_estimate
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get mission analytics for {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mission analytics")

@router.get("/system/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics():
    """Get overall system metrics"""
    try:
        metrics = await analytics_engine.get_system_metrics()
        
        return SystemMetricsResponse(
            total_missions=metrics.total_missions,
            active_missions=metrics.active_missions,
            completed_missions=metrics.completed_missions,
            total_discoveries=metrics.total_discoveries,
            avg_mission_duration=metrics.avg_mission_duration,
            system_uptime=metrics.system_uptime,
            drone_fleet_size=metrics.drone_fleet_size,
            active_drones=metrics.active_drones,
            total_flight_hours=metrics.total_flight_hours
        )
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")

@router.get("/performance/report", response_model=PerformanceReportResponse)
async def get_performance_report(
    days: int = Query(30, ge=1, le=365, description="Number of days for the report period")
):
    """Generate a performance report for the specified period"""
    try:
        report = await analytics_engine.get_performance_report(days)
        
        return PerformanceReportResponse(
            period_start=report.period_start,
            period_end=report.period_end,
            mission_metrics=[
                MissionMetricsResponse(
                    mission_id=m.mission_id,
                    total_time_minutes=m.total_time_minutes,
                    area_covered_km2=m.area_covered_km2,
                    discoveries_found=m.discoveries_found,
                    drones_used=m.drones_used,
                    efficiency_score=m.efficiency_score,
                    success_rate=m.success_rate,
                    avg_drone_utilization=m.avg_drone_utilization,
                    cost_estimate=m.cost_estimate
                )
                for m in report.mission_metrics
            ],
            system_metrics=SystemMetricsResponse(
                total_missions=report.system_metrics.total_missions,
                active_missions=report.system_metrics.active_missions,
                completed_missions=report.system_metrics.completed_missions,
                total_discoveries=report.system_metrics.total_discoveries,
                avg_mission_duration=report.system_metrics.avg_mission_duration,
                system_uptime=report.system_metrics.system_uptime,
                drone_fleet_size=report.system_metrics.drone_fleet_size,
                active_drones=report.system_metrics.active_drones,
                total_flight_hours=report.system_metrics.total_flight_hours
            ),
            trends=report.trends,
            recommendations=report.recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate performance report")

@router.get("/discoveries", response_model=DiscoveryAnalyticsResponse)
async def get_discovery_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days for the analysis period")
):
    """Get analytics about discoveries"""
    try:
        analytics = await analytics_engine.get_discovery_analytics(days)
        
        if "error" in analytics:
            raise HTTPException(status_code=500, detail=analytics["error"])
        
        return DiscoveryAnalyticsResponse(
            total_discoveries=analytics["total_discoveries"],
            discovery_types=analytics["discovery_types"],
            average_confidence=analytics["average_confidence"],
            high_confidence_discoveries=analytics["high_confidence_discoveries"],
            verified_discoveries=analytics["verified_discoveries"],
            period_days=analytics["period_days"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get discovery analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery analytics")

@router.get("/drones/{drone_id}", response_model=DronePerformanceResponse)
async def get_drone_performance(drone_id: str):
    """Get performance analytics for a specific drone"""
    try:
        performance = await analytics_engine.get_drone_performance(drone_id)
        
        if "error" in performance:
            raise HTTPException(status_code=500, detail=performance["error"])
        
        return DronePerformanceResponse(
            drone_id=performance["drone_id"],
            total_missions=performance["total_missions"],
            successful_missions=performance["successful_missions"],
            success_rate=performance["success_rate"],
            average_mission_time_minutes=performance["average_mission_time_minutes"],
            total_flight_hours=performance["total_flight_hours"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get drone performance for {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve drone performance")

@router.get("/drones", response_model=DronePerformanceResponse)
async def get_all_drones_performance():
    """Get performance analytics for all drones"""
    try:
        performance = await analytics_engine.get_drone_performance()
        
        if "error" in performance:
            raise HTTPException(status_code=500, detail=performance["error"])
        
        return DronePerformanceResponse(
            drone_id=performance["drone_id"],
            total_missions=performance["total_missions"],
            successful_missions=performance["successful_missions"],
            success_rate=performance["success_rate"],
            average_mission_time_minutes=performance["average_mission_time_minutes"],
            total_flight_hours=performance["total_flight_hours"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all drones performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve drones performance")

@router.get("/missions/success-rates")
async def get_mission_success_rates(
    days: int = Query(30, ge=1, le=365, description="Number of days for the analysis period")
):
    """Get mission success rates by type"""
    try:
        success_rates = await analytics_engine.get_mission_success_rates(days)
        
        return {
            "period_days": days,
            "success_rates_by_type": success_rates,
            "overall_success_rate": sum(success_rates.values()) / len(success_rates) if success_rates else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get mission success rates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mission success rates")

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get summary data for dashboard"""
    try:
        # Get system metrics
        system_metrics = await analytics_engine.get_system_metrics()
        
        # Get discovery analytics for last 7 days
        discovery_analytics = await analytics_engine.get_discovery_analytics(7)
        
        # Get mission success rates for last 30 days
        success_rates = await analytics_engine.get_mission_success_rates(30)
        
        return {
            "system_overview": {
                "total_missions": system_metrics.total_missions,
                "active_missions": system_metrics.active_missions,
                "completed_missions": system_metrics.completed_missions,
                "total_discoveries": system_metrics.total_discoveries,
                "drone_fleet_size": system_metrics.drone_fleet_size,
                "active_drones": system_metrics.active_drones
            },
            "recent_activity": {
                "discoveries_last_7_days": discovery_analytics.get("total_discoveries", 0),
                "discovery_types": discovery_analytics.get("discovery_types", {}),
                "high_confidence_discoveries": discovery_analytics.get("high_confidence_discoveries", 0)
            },
            "performance": {
                "success_rates_by_type": success_rates,
                "overall_success_rate": sum(success_rates.values()) / len(success_rates) if success_rates else 0,
                "average_mission_duration": system_metrics.avg_mission_duration,
                "total_flight_hours": system_metrics.total_flight_hours
            },
            "system_health": {
                "uptime_percentage": system_metrics.system_uptime,
                "fleet_utilization": (system_metrics.active_drones / system_metrics.drone_fleet_size * 100) if system_metrics.drone_fleet_size > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard summary")

@router.get("/trends/missions")
async def get_mission_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days for trend analysis")
):
    """Get mission trends over time"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get performance report for trend analysis
        report = await analytics_engine.get_performance_report(days)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "trends": report.trends,
            "summary": {
                "total_missions": len(report.mission_metrics),
                "average_efficiency": sum([m.efficiency_score for m in report.mission_metrics]) / len(report.mission_metrics) if report.mission_metrics else 0,
                "average_success_rate": sum([m.success_rate for m in report.mission_metrics]) / len(report.mission_metrics) if report.mission_metrics else 0,
                "total_cost": sum([m.cost_estimate for m in report.mission_metrics]),
                "total_discoveries": sum([m.discoveries_found for m in report.mission_metrics])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get mission trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mission trends")
