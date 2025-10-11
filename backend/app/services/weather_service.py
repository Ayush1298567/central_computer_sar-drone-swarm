"""
Weather Service for SAR Mission Commander
Real-time weather data integration for flight planning and safety
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import math

from ..utils.logging import get_logger
from ..core.config import settings

logger = get_logger(__name__)

class WeatherCondition(Enum):
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    FOG = "fog"
    SNOW = "snow"
    WINDY = "windy"
    SEVERE = "severe"

class FlightSafety(Enum):
    SAFE = "safe"
    CAUTION = "caution"
    UNSAFE = "unsafe"
    GROUNDED = "grounded"

@dataclass
class WeatherData:
    """Weather data for a specific location and time"""
    latitude: float
    longitude: float
    timestamp: datetime
    
    # Current conditions
    temperature_celsius: float
    humidity_percent: float
    pressure_hpa: float
    visibility_km: float
    cloud_cover_percent: float
    
    # Wind data
    wind_speed_ms: float
    wind_direction_degrees: float
    wind_gusts_ms: float
    
    # Precipitation
    precipitation_mm: float
    precipitation_probability: float
    
    # Weather condition
    condition: WeatherCondition
    description: str
    
    # Flight safety assessment
    flight_safety: FlightSafety
    safety_reasons: List[str]

@dataclass
class WeatherForecast:
    """Weather forecast for multiple time periods"""
    location: Tuple[float, float]  # lat, lng
    forecast_data: List[WeatherData]
    generated_at: datetime
    source: str

@dataclass
class FlightRestriction:
    """Flight restriction based on weather conditions"""
    restriction_type: str  # "altitude", "area", "time", "complete"
    severity: str  # "warning", "caution", "critical"
    reason: str
    affected_area: Optional[Dict[str, Any]] = None
    valid_until: Optional[datetime] = None
    recommended_action: str = ""

class WeatherService:
    """Weather service for SAR mission planning"""
    
    def __init__(self):
        self.api_keys = {
            'openweather': getattr(settings, 'OPENWEATHER_API_KEY', None),
            'weather_api': getattr(settings, 'WEATHER_API_KEY', None),
            'noaa': getattr(settings, 'NOAA_API_KEY', None)
        }
        
        # Weather thresholds for flight safety
        self.safety_thresholds = {
            'max_wind_speed_ms': 12.0,  # 12 m/s = ~27 mph
            'max_wind_gusts_ms': 15.0,  # 15 m/s = ~34 mph
            'min_visibility_km': 1.0,   # 1 km minimum visibility
            'max_cloud_cover_percent': 90.0,  # 90% cloud cover max
            'max_precipitation_mm': 2.0,  # 2mm/hour max
            'min_temperature_celsius': -20.0,  # -20°C minimum
            'max_temperature_celsius': 40.0   # 40°C maximum
        }
        
        # Cache for weather data
        self.weather_cache = {}
        self.cache_duration = 300  # 5 minutes
        
    async def get_current_weather(self, latitude: float, longitude: float) -> WeatherData:
        """Get current weather conditions for a specific location"""
        try:
            cache_key = f"{latitude:.4f}_{longitude:.4f}_current"
            
            # Check cache first
            if cache_key in self.weather_cache:
                cached_data, timestamp = self.weather_cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_duration:
                    return cached_data
            
            # Fetch from multiple sources for redundancy
            weather_data = None
            
            if self.api_keys['openweather']:
                weather_data = await self._fetch_openweather_data(latitude, longitude)
            
            if not weather_data and self.api_keys['weather_api']:
                weather_data = await self._fetch_weather_api_data(latitude, longitude)
            
            if not weather_data:
                # Fallback to mock data for development
                weather_data = self._generate_mock_weather_data(latitude, longitude)
            
            # Assess flight safety
            weather_data.flight_safety, weather_data.safety_reasons = self._assess_flight_safety(weather_data)
            
            # Cache the result
            self.weather_cache[cache_key] = (weather_data, datetime.now())
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Error getting current weather: {e}")
            # Return safe default weather data
            return self._generate_safe_weather_data(latitude, longitude)
    
    def _assess_flight_safety(self, weather_data: WeatherData) -> Tuple[FlightSafety, List[str]]:
        """Assess flight safety based on weather conditions"""
        safety_reasons = []
        
        # Check wind conditions
        if weather_data.wind_speed_ms > self.safety_thresholds['max_wind_speed_ms']:
            safety_reasons.append(f"High wind speed: {weather_data.wind_speed_ms:.1f} m/s")
        
        if weather_data.wind_gusts_ms > self.safety_thresholds['max_wind_gusts_ms']:
            safety_reasons.append(f"High wind gusts: {weather_data.wind_gusts_ms:.1f} m/s")
        
        # Check visibility
        if weather_data.visibility_km < self.safety_thresholds['min_visibility_km']:
            safety_reasons.append(f"Low visibility: {weather_data.visibility_km:.1f} km")
        
        # Check cloud cover
        if weather_data.cloud_cover_percent > self.safety_thresholds['max_cloud_cover_percent']:
            safety_reasons.append(f"High cloud cover: {weather_data.cloud_cover_percent:.1f}%")
        
        # Check precipitation
        if weather_data.precipitation_mm > self.safety_thresholds['max_precipitation_mm']:
            safety_reasons.append(f"Heavy precipitation: {weather_data.precipitation_mm:.1f} mm/h")
        
        # Check temperature
        if (weather_data.temperature_celsius < self.safety_thresholds['min_temperature_celsius'] or
            weather_data.temperature_celsius > self.safety_thresholds['max_temperature_celsius']):
            safety_reasons.append(f"Extreme temperature: {weather_data.temperature_celsius:.1f}°C")
        
        # Check weather condition
        if weather_data.condition in [WeatherCondition.STORM, WeatherCondition.SEVERE]:
            safety_reasons.append(f"Severe weather: {weather_data.condition.value}")
        
        # Determine safety level
        if len(safety_reasons) == 0:
            return FlightSafety.SAFE, []
        elif len(safety_reasons) <= 2 and weather_data.condition not in [WeatherCondition.STORM, WeatherCondition.SEVERE]:
            return FlightSafety.CAUTION, safety_reasons
        else:
            return FlightSafety.UNSAFE, safety_reasons
    
    def _generate_mock_weather_data(self, latitude: float, longitude: float) -> WeatherData:
        """Generate mock weather data for development/testing"""
        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(),
            temperature_celsius=22.0,
            humidity_percent=65.0,
            pressure_hpa=1013.25,
            visibility_km=10.0,
            cloud_cover_percent=25.0,
            wind_speed_ms=5.0,
            wind_direction_degrees=180.0,
            wind_gusts_ms=7.0,
            precipitation_mm=0.0,
            precipitation_probability=10.0,
            condition=WeatherCondition.CLEAR,
            description="Clear skies",
            flight_safety=FlightSafety.SAFE,
            safety_reasons=[]
        )
    
    def _generate_safe_weather_data(self, latitude: float, longitude: float) -> WeatherData:
        """Generate safe weather data as fallback"""
        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(),
            temperature_celsius=20.0,
            humidity_percent=50.0,
            pressure_hpa=1013.25,
            visibility_km=15.0,
            cloud_cover_percent=10.0,
            wind_speed_ms=3.0,
            wind_direction_degrees=0.0,
            wind_gusts_ms=5.0,
            precipitation_mm=0.0,
            precipitation_probability=0.0,
            condition=WeatherCondition.CLEAR,
            description="Safe flying conditions",
            flight_safety=FlightSafety.SAFE,
            safety_reasons=[]
        )
    
    async def _fetch_openweather_data(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """Fetch weather data from OpenWeather API"""
        try:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_keys['openweather'],
                'units': 'metric'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse OpenWeather data
                        weather_data = WeatherData(
                            latitude=latitude,
                            longitude=longitude,
                            timestamp=datetime.now(),
                            temperature_celsius=data['main']['temp'],
                            humidity_percent=data['main']['humidity'],
                            pressure_hpa=data['main']['pressure'],
                            visibility_km=data.get('visibility', 10000) / 1000,
                            cloud_cover_percent=data['clouds']['all'],
                            wind_speed_ms=data['wind']['speed'],
                            wind_direction_degrees=data['wind'].get('deg', 0),
                            wind_gusts_ms=data['wind'].get('gust', 0),
                            precipitation_mm=data.get('rain', {}).get('1h', 0),
                            precipitation_probability=0,  # Not provided in current weather
                            condition=self._map_weather_condition(data['weather'][0]['main']),
                            description=data['weather'][0]['description'],
                            flight_safety=FlightSafety.SAFE,  # Will be calculated later
                            safety_reasons=[]
                        )
                        
                        return weather_data
                    else:
                        logger.warning(f"OpenWeather API returned status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching OpenWeather data: {e}")
            return None
    
    async def _fetch_weather_api_data(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """Fetch weather data from WeatherAPI.com"""
        try:
            url = "http://api.weatherapi.com/v1/current.json"
            params = {
                'key': self.api_keys['weather_api'],
                'q': f"{latitude},{longitude}",
                'aqi': 'no'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse WeatherAPI data
                        weather_data = WeatherData(
                            latitude=latitude,
                            longitude=longitude,
                            timestamp=datetime.now(),
                            temperature_celsius=data['current']['temp_c'],
                            humidity_percent=data['current']['humidity'],
                            pressure_hpa=data['current']['pressure_mb'],
                            visibility_km=data['current']['vis_km'],
                            cloud_cover_percent=data['current']['cloud'],
                            wind_speed_ms=data['current']['wind_kph'] / 3.6,  # Convert km/h to m/s
                            wind_direction_degrees=data['current']['wind_degree'],
                            wind_gusts_ms=data['current'].get('gust_kph', 0) / 3.6,
                            precipitation_mm=data['current'].get('precip_mm', 0),
                            precipitation_probability=data['current'].get('chance_of_rain', 0),
                            condition=self._map_weather_condition(data['current']['condition']['text']),
                            description=data['current']['condition']['text'],
                            flight_safety=FlightSafety.SAFE,  # Will be calculated later
                            safety_reasons=[]
                        )
                        
                        return weather_data
                    else:
                        logger.warning(f"WeatherAPI returned status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching WeatherAPI data: {e}")
            return None
    
    def _map_weather_condition(self, condition_text: str) -> WeatherCondition:
        """Map weather condition text to enum"""
        condition_lower = condition_text.lower()
        
        if 'clear' in condition_lower or 'sunny' in condition_lower:
            return WeatherCondition.CLEAR
        elif 'partly' in condition_lower or 'few clouds' in condition_lower:
            return WeatherCondition.PARTLY_CLOUDY
        elif 'cloud' in condition_lower:
            return WeatherCondition.CLOUDY
        elif 'rain' in condition_lower or 'drizzle' in condition_lower:
            return WeatherCondition.RAIN
        elif 'storm' in condition_lower or 'thunder' in condition_lower:
            return WeatherCondition.STORM
        elif 'fog' in condition_lower or 'mist' in condition_lower:
            return WeatherCondition.FOG
        elif 'snow' in condition_lower:
            return WeatherCondition.SNOW
        elif 'wind' in condition_lower:
            return WeatherCondition.WINDY
        else:
            return WeatherCondition.CLEAR  # Default to clear
    
    def get_flight_restrictions(self, weather_data: WeatherData) -> List[FlightRestriction]:
        """Get flight restrictions based on weather conditions"""
        restrictions = []
        
        # Wind restrictions
        if weather_data.wind_speed_ms > self.safety_thresholds['max_wind_speed_ms']:
            restrictions.append(FlightRestriction(
                restriction_type="area",
                severity="warning",
                reason=f"High wind speed: {weather_data.wind_speed_ms:.1f} m/s",
                recommended_action="Reduce search area or postpone flight"
            ))
        
        # Visibility restrictions
        if weather_data.visibility_km < self.safety_thresholds['min_visibility_km']:
            restrictions.append(FlightRestriction(
                restriction_type="area",
                severity="critical",
                reason=f"Low visibility: {weather_data.visibility_km:.1f} km",
                recommended_action="Ground all flights until visibility improves"
            ))
        
        # Precipitation restrictions
        if weather_data.precipitation_mm > self.safety_thresholds['max_precipitation_mm']:
            restrictions.append(FlightRestriction(
                restriction_type="complete",
                severity="critical",
                reason=f"Heavy precipitation: {weather_data.precipitation_mm:.1f} mm/h",
                recommended_action="Ground all flights"
            ))
        
        # Storm restrictions
        if weather_data.condition in [WeatherCondition.STORM, WeatherCondition.SEVERE]:
            restrictions.append(FlightRestriction(
                restriction_type="complete",
                severity="critical",
                reason=f"Severe weather: {weather_data.condition.value}",
                recommended_action="Ground all flights until conditions improve"
            ))
        
        return restrictions

# Global instance
weather_service = WeatherService()