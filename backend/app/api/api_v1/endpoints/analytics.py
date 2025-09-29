"""
Analytics API endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
import logging

from app.services.analytics_engine import analytics_engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/system-overview")
async def get_system_overview():
    """Get system-wide analytics overview."""
    try:
        overview = analytics_engine.get_system_overview_analytics()
        return overview
    except Exception as e:
        logger.error(f"Error fetching system overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/missions/{mission_id}")
async def get_mission_analytics(mission_id: str):
    """Get analytics for a specific mission."""
    try:
        analytics = analytics_engine.get_mission_analytics(mission_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Mission not found")

        return {
            "mission_id": analytics.mission_id,
            "total_duration": analytics.total_duration,
            "area_covered": analytics.area_covered,
            "discoveries_found": analytics.discoveries_found,
            "average_discovery_confidence": analytics.average_discovery_confidence,
            "drone_utilization_rate": analytics.drone_utilization_rate,
            "mission_efficiency_score": analytics.mission_efficiency_score,
            "weather_impact_score": analytics.weather_impact_score,
            "recommendations": analytics.recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching mission analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/drones/{drone_id}")
async def get_drone_analytics(drone_id: str, days: int = 30):
    """Get performance analytics for a specific drone."""
    try:
        analytics = analytics_engine.get_drone_performance_analytics(drone_id, days)
        if not analytics:
            raise HTTPException(status_code=404, detail="Drone not found")

        return {
            "drone_id": analytics.drone_id,
            "flight_time": analytics.flight_time,
            "distance_traveled": analytics.distance_traveled,
            "battery_efficiency": analytics.battery_efficiency,
            "discoveries_found": analytics.discoveries_found,
            "mission_participation_rate": analytics.mission_participation_rate,
            "maintenance_needed": analytics.maintenance_needed,
            "performance_score": analytics.performance_score
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching drone analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")