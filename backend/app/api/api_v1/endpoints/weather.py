"""
Weather API endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
import logging

from app.services.weather_service import weather_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/current")
async def get_current_weather(latitude: float, longitude: float):
    """Get current weather conditions for a location."""
    try:
        weather = await weather_service.get_current_weather(latitude, longitude)
        if not weather:
            raise HTTPException(status_code=404, detail="Weather data not available")

        return {
            "temperature": weather.temperature,
            "humidity": weather.humidity,
            "wind_speed": weather.wind_speed,
            "wind_direction": weather.wind_direction,
            "visibility": weather.visibility,
            "pressure": weather.pressure,
            "conditions": weather.conditions,
            "timestamp": weather.timestamp.isoformat(),
            "location": weather.location
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current weather: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/forecast")
async def get_weather_forecast(latitude: float, longitude: float, hours: int = 24):
    """Get weather forecast for the next specified hours."""
    try:
        forecast = await weather_service.get_weather_forecast(latitude, longitude, hours)

        return {
            "forecast": [
                {
                    "temperature": item.temperature,
                    "humidity": item.humidity,
                    "wind_speed": item.wind_speed,
                    "wind_direction": item.wind_direction,
                    "visibility": item.visibility,
                    "pressure": item.pressure,
                    "conditions": item.conditions,
                    "timestamp": item.timestamp.isoformat(),
                    "location": item.location
                }
                for item in forecast
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suitability")
async def check_weather_suitability(latitude: float, longitude: float):
    """Check if weather conditions are suitable for drone operations."""
    try:
        weather = await weather_service.get_current_weather(latitude, longitude)
        if not weather:
            raise HTTPException(status_code=404, detail="Weather data not available")

        is_suitable, reason = weather_service.is_weather_suitable_for_mission(weather)

        return {
            "is_suitable": is_suitable,
            "reason": reason,
            "weather_conditions": {
                "temperature": weather.temperature,
                "wind_speed": weather.wind_speed,
                "visibility": weather.visibility,
                "conditions": weather.conditions
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking weather suitability: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alerts")
async def get_weather_alerts(latitude: float, longitude: float):
    """Get weather alerts for a location."""
    try:
        alerts = await weather_service.get_weather_alerts(latitude, longitude)

        return {
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error fetching weather alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")