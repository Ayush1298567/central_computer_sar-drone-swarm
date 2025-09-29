"""
Weather service for SAR missions.
"""

import asyncio
import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import httpx
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WeatherConditions:
    """Weather conditions data structure."""
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: float
    visibility: float
    pressure: float
    conditions: str
    timestamp: datetime
    location: Tuple[float, float]


class WeatherService:
    """
    Weather service for retrieving current and forecasted weather conditions.
    """

    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = settings.WEATHER_API_URL
        self.cache: Dict[Tuple[float, float], Tuple[WeatherConditions, datetime]] = {}
        self.cache_duration = timedelta(minutes=15)  # Cache weather data for 15 minutes

    async def get_current_weather(self, latitude: float, longitude: float) -> Optional[WeatherConditions]:
        """
        Get current weather conditions for a location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location

        Returns:
            WeatherConditions object or None if failed
        """
        try:
            # Check cache first
            cache_key = (latitude, longitude)
            if cache_key in self.cache:
                weather_data, timestamp = self.cache[cache_key]
                if datetime.utcnow() - timestamp < self.cache_duration:
                    logger.info(f"Returning cached weather data for ({latitude}, {longitude})")
                    return weather_data

            # Fetch from API
            if not self.api_key:
                logger.warning("Weather API key not configured, returning mock data")
                return self._get_mock_weather(latitude, longitude)

            url = f"{self.base_url}/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            # Parse weather data
            weather_conditions = self._parse_weather_data(data, latitude, longitude)

            # Cache the result
            self.cache[cache_key] = (weather_conditions, datetime.utcnow())

            logger.info(f"Retrieved weather data for ({latitude}, {longitude})")
            return weather_conditions

        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return self._get_mock_weather(latitude, longitude)

    async def get_weather_forecast(self, latitude: float, longitude: float, hours: int = 24) -> list:
        """
        Get weather forecast for the next specified hours.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            hours: Number of hours to forecast (max 48)

        Returns:
            List of WeatherConditions objects
        """
        try:
            if not self.api_key:
                logger.warning("Weather API key not configured, returning mock forecast")
                return self._get_mock_forecast(latitude, longitude, hours)

            url = f"{self.base_url}/forecast"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            forecast = []
            for item in data.get("list", [])[:hours//3]:  # API returns 3-hour intervals
                weather_data = self._parse_weather_data(item, latitude, longitude, is_forecast=True)
                forecast.append(weather_data)

            return forecast

        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return self._get_mock_forecast(latitude, longitude, hours)

    def is_weather_suitable_for_mission(self, weather: WeatherConditions) -> Tuple[bool, str]:
        """
        Check if weather conditions are suitable for drone operations.

        Args:
            weather: WeatherConditions object

        Returns:
            Tuple of (is_suitable, reason)
        """
        # Define weather thresholds for safe drone operations
        max_wind_speed = 15.0  # m/s (about 33 mph)
        min_visibility = 1000.0  # meters
        max_precipitation = 2.0  # mm/h

        if weather.wind_speed > max_wind_speed:
            return False, f"Wind speed {weather.wind_speed} m/s exceeds maximum safe limit of {max_wind_speed} m/s"

        if weather.visibility < min_visibility:
            return False, f"Visibility {weather.visibility} m is below minimum safe limit of {min_visibility} m"

        # Check for severe weather conditions
        severe_conditions = ["thunderstorm", "heavy rain", "snow", "fog"]
        if any(condition in weather.conditions.lower() for condition in severe_conditions):
            return False, f"Severe weather conditions detected: {weather.conditions}"

        return True, "Weather conditions are suitable for drone operations"

    def _parse_weather_data(self, data: Dict, latitude: float, longitude: float, is_forecast: bool = False) -> WeatherConditions:
        """Parse weather API response into WeatherConditions object."""
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = data.get("weather", [{}])[0]
        visibility = data.get("visibility", 10000) / 1000  # Convert meters to km

        return WeatherConditions(
            temperature=main.get("temp", 20.0),
            humidity=main.get("humidity", 50.0),
            wind_speed=wind.get("speed", 0.0),
            wind_direction=wind.get("deg", 0.0),
            visibility=visibility,
            pressure=main.get("pressure", 1013.0),
            conditions=weather.get("main", "Clear"),
            timestamp=datetime.fromtimestamp(data.get("dt", datetime.utcnow().timestamp())),
            location=(latitude, longitude)
        )

    def _get_mock_weather(self, latitude: float, longitude: float) -> WeatherConditions:
        """Return mock weather data for testing when API is unavailable."""
        return WeatherConditions(
            temperature=22.0,
            humidity=65.0,
            wind_speed=5.0,
            wind_direction=180.0,
            visibility=10.0,
            pressure=1013.0,
            conditions="Clear",
            timestamp=datetime.utcnow(),
            location=(latitude, longitude)
        )

    def _get_mock_forecast(self, latitude: float, longitude: float, hours: int) -> list:
        """Return mock weather forecast for testing."""
        forecast = []
        base_weather = self._get_mock_weather(latitude, longitude)

        for i in range(0, hours, 3):
            weather = WeatherConditions(
                temperature=base_weather.temperature + (i * 0.1),  # Slight temperature variation
                humidity=base_weather.humidity,
                wind_speed=base_weather.wind_speed,
                wind_direction=base_weather.wind_direction,
                visibility=base_weather.visibility,
                pressure=base_weather.pressure,
                conditions=base_weather.conditions,
                timestamp=datetime.utcnow() + timedelta(hours=i),
                location=(latitude, longitude)
            )
            forecast.append(weather)

        return forecast

    async def get_weather_alerts(self, latitude: float, longitude: float) -> list:
        """
        Get weather alerts for a location.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location

        Returns:
            List of weather alert dictionaries
        """
        try:
            if not self.api_key:
                return []

            url = f"{self.base_url}/onecall"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "exclude": "current,minutely,hourly,daily"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            alerts = data.get("alerts", [])
            return [
                {
                    "title": alert.get("title", ""),
                    "description": alert.get("description", ""),
                    "severity": alert.get("tags", [""])[0],
                    "start": datetime.fromtimestamp(alert.get("start", 0)),
                    "end": datetime.fromtimestamp(alert.get("end", 0))
                }
                for alert in alerts
            ]

        except Exception as e:
            logger.error(f"Error fetching weather alerts: {e}")
            return []


# Global weather service instance
weather_service = WeatherService()