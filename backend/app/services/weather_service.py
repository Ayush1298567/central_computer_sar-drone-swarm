import aiohttp
import asyncio
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import json
import math

logger = logging.getLogger(__name__)

class WeatherService:
    """
    Weather service for SAR mission planning and execution.

    Provides weather data integration, flight condition assessment,
    and mission timing optimization based on meteorological conditions.
    """

    def __init__(self):
        self.api_key = None  # Set via environment variable
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache = {}
        self.cache_duration = 300  # 5 minutes

        # Weather thresholds for drone operations
        self.weather_limits = {
            "max_wind_speed": 15.0,  # m/s
            "max_gust_speed": 20.0,  # m/s
            "min_visibility": 1000,   # meters
            "max_precipitation": 5.0, # mm/h
            "min_temperature": -10,   # Celsius
            "max_temperature": 45,    # Celsius
            "max_humidity": 90,       # percentage
        }

        # Impact factors for different weather conditions
        self.weather_impact_factors = {
            "wind": {
                "flight_time": 1.2,  # 20% increase in battery usage
                "stability": 0.8,    # 20% reduction in flight stability
                "range": 0.9         # 10% reduction in effective range
            },
            "precipitation": {
                "visibility": 0.6,   # 40% reduction in visibility
                "sensor_effectiveness": 0.7,  # 30% reduction in sensor effectiveness
                "safety_risk": 1.5   # 50% increase in safety risk
            },
            "temperature": {
                "battery_efficiency": 1.1,  # 10% reduction in battery efficiency
                "flight_time": 1.15   # 15% increase in power consumption
            }
        }

    async def get_weather_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Get current weather data for specified coordinates.

        Args:
            latitude: Target latitude
            longitude: Target longitude

        Returns:
            Weather data dictionary or None if request fails
        """
        cache_key = f"{latitude}_{longitude}"

        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_duration):
                return cached_data

        try:
            # Use free OpenWeatherMap API (no API key required for basic data)
            url = f"{self.base_url}/weather?lat={latitude}&lon={longitude}&units=metric&appid={self.api_key or 'demo'}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        processed_data = self._process_weather_data(data)

                        # Cache the result
                        self.cache[cache_key] = (processed_data, datetime.now())

                        return processed_data
                    else:
                        logger.error(f"Weather API request failed: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return None

    async def get_forecast(self, latitude: float, longitude: float, hours: int = 24) -> Optional[List[Dict]]:
        """
        Get weather forecast for specified duration.

        Args:
            latitude: Target latitude
            longitude: Target longitude
            hours: Forecast duration in hours

        Returns:
            List of forecast data or None if request fails
        """
        try:
            url = f"{self.base_url}/forecast?lat={latitude}&lon={longitude}&units=metric&appid={self.api_key or 'demo'}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        forecasts = []

                        for item in data.get("list", [])[:hours//3]:  # Every 3 hours
                            forecast_time = datetime.fromtimestamp(item["dt"])
                            processed_forecast = self._process_weather_data(item)
                            processed_forecast["timestamp"] = forecast_time.isoformat()
                            forecasts.append(processed_forecast)

                        return forecasts
                    else:
                        logger.error(f"Forecast API request failed: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return None

    def _process_weather_data(self, raw_data: Dict) -> Dict:
        """
        Process raw weather API data into standardized format.

        Args:
            raw_data: Raw weather data from API

        Returns:
            Processed weather data dictionary
        """
        main = raw_data.get("main", {})
        wind = raw_data.get("wind", {})
        clouds = raw_data.get("clouds", {})
        weather = raw_data.get("weather", [{}])[0]
        sys = raw_data.get("sys", {})

        processed = {
            "temperature": main.get("temp", 0),
            "feels_like": main.get("feels_like", 0),
            "humidity": main.get("humidity", 0),
            "pressure": main.get("pressure", 0),
            "wind_speed": wind.get("speed", 0),
            "wind_direction": wind.get("deg", 0),
            "wind_gust": wind.get("gust", 0),
            "visibility": raw_data.get("visibility", 10000),
            "cloud_coverage": clouds.get("all", 0),
            "condition": weather.get("main", "Unknown"),
            "description": weather.get("description", ""),
            "sunrise": datetime.fromtimestamp(sys.get("sunrise", 0)).isoformat() if sys.get("sunrise") else None,
            "sunset": datetime.fromtimestamp(sys.get("sunset", 0)).isoformat() if sys.get("sunset") else None,
            "location": {
                "latitude": raw_data.get("coord", {}).get("lat", 0),
                "longitude": raw_data.get("coord", {}).get("lon", 0),
                "name": raw_data.get("name", "Unknown")
            },
            "timestamp": datetime.now().isoformat()
        }

        return processed

    def assess_flight_conditions(self, weather_data: Dict) -> Dict:
        """
        Assess if current weather conditions are suitable for drone flight.

        Args:
            weather_data: Processed weather data

        Returns:
            Flight condition assessment
        """
        conditions = weather_data
        limits = self.weather_limits

        # Check each weather parameter against limits
        assessments = {
            "wind_speed_ok": conditions["wind_speed"] <= limits["max_wind_speed"],
            "wind_gust_ok": conditions.get("wind_gust", 0) <= limits["max_gust_speed"],
            "visibility_ok": conditions["visibility"] >= limits["min_visibility"],
            "temperature_ok": (limits["min_temperature"] <= conditions["temperature"] <= limits["max_temperature"]),
            "humidity_ok": conditions["humidity"] <= limits["max_humidity"],
        }

        # Calculate overall flight safety score (0-100)
        safety_score = 100
        issues = []

        if not assessments["wind_speed_ok"]:
            safety_score -= 25
            issues.append(f"Wind speed ({conditions['wind_speed']}m/s) exceeds limit ({limits['max_wind_speed']}m/s)")

        if not assessments["wind_gust_ok"]:
            safety_score -= 15
            issues.append(f"Wind gusts ({conditions.get('wind_gust', 0)}m/s) exceed limit ({limits['max_gust_speed']}m/s)")

        if not assessments["visibility_ok"]:
            safety_score -= 20
            issues.append(f"Visibility ({conditions['visibility']}m) below minimum ({limits['min_visibility']}m)")

        if not assessments["temperature_ok"]:
            safety_score -= 15
            issues.append(f"Temperature ({conditions['temperature']}°C) outside safe range")

        if not assessments["humidity_ok"]:
            safety_score -= 10
            issues.append(f"High humidity ({conditions['humidity']}%) may affect electronics")

        # Additional condition checks
        if conditions.get("condition") in ["Thunderstorm", "Snow", "Heavy Rain"]:
            safety_score -= 30
            issues.append(f"Severe weather condition: {conditions['condition']}")

        if conditions.get("wind_speed", 0) > 10:
            safety_score -= 10
            issues.append("High winds will increase battery consumption")

        # Determine flight recommendation
        if safety_score >= 80:
            recommendation = "optimal"
        elif safety_score >= 60:
            recommendation = "acceptable"
        elif safety_score >= 40:
            recommendation = "marginal"
        else:
            recommendation = "unsafe"

        return {
            "safety_score": max(0, safety_score),
            "recommendation": recommendation,
            "assessments": assessments,
            "issues": issues,
            "can_fly": recommendation in ["optimal", "acceptable"],
            "restrictions": self._get_flight_restrictions(recommendation, conditions)
        }

    def _get_flight_restrictions(self, recommendation: str, conditions: Dict) -> List[str]:
        """
        Get specific flight restrictions based on weather conditions.

        Args:
            recommendation: Flight condition recommendation
            conditions: Weather conditions

        Returns:
            List of flight restrictions
        """
        restrictions = []

        if recommendation == "unsafe":
            restrictions.append("Ground all drones immediately")
            restrictions.append("Wait for conditions to improve")

        elif recommendation == "marginal":
            restrictions.append("Reduce flight altitude to minimum safe height")
            restrictions.append("Limit mission duration to 50% of normal")
            restrictions.append("Increase monitoring frequency")
            restrictions.append("Prepare emergency return procedures")

        elif recommendation == "acceptable":
            restrictions.append("Monitor weather conditions continuously")
            restrictions.append("Be prepared to abort mission if conditions worsen")

        if conditions.get("wind_speed", 0) > 10:
            restrictions.append(f"Reduce maximum speed to {max(5, 15 - conditions['wind_speed'])} m/s")

        if conditions.get("visibility", 10000) < 2000:
            restrictions.append("Enable obstacle avoidance systems")
            restrictions.append("Reduce search altitude for better ground visibility")

        return restrictions

    def calculate_weather_impact(self, weather_data: Dict, mission_duration: int) -> Dict:
        """
        Calculate the impact of weather conditions on mission performance.

        Args:
            weather_data: Current weather conditions
            mission_duration: Planned mission duration in minutes

        Returns:
            Weather impact assessment
        """
        conditions = weather_data
        impact = {
            "battery_consumption_multiplier": 1.0,
            "flight_time_reduction": 0,
            "range_reduction": 0,
            "sensor_effectiveness": 1.0,
            "safety_risk_multiplier": 1.0
        }

        # Wind impact
        wind_speed = conditions.get("wind_speed", 0)
        if wind_speed > 5:
            wind_factor = min(0.5, wind_speed / 20)  # Max 50% impact
            impact["battery_consumption_multiplier"] *= (1 + wind_factor * self.weather_impact_factors["wind"]["flight_time"])
            impact["range_reduction"] += wind_factor * (1 - self.weather_impact_factors["wind"]["range"])

        # Precipitation impact
        condition = conditions.get("condition", "")
        if "rain" in condition.lower() or "snow" in condition.lower():
            precip_factor = 0.3  # 30% impact for precipitation
            impact["sensor_effectiveness"] *= (1 - precip_factor * (1 - self.weather_impact_factors["precipitation"]["sensor_effectiveness"]))
            impact["safety_risk_multiplier"] *= (1 + precip_factor * (self.weather_impact_factors["precipitation"]["safety_risk"] - 1))

        # Temperature impact
        temp = conditions.get("temperature", 20)
        if temp < 10 or temp > 30:
            temp_factor = min(0.3, abs(temp - 20) / 30)  # Max 30% impact
            impact["battery_consumption_multiplier"] *= (1 + temp_factor * (self.weather_impact_factors["temperature"]["battery_efficiency"] - 1))

        # Calculate adjusted mission parameters
        adjusted_duration = mission_duration * (1 - impact["flight_time_reduction"])
        adjusted_range = 5000 * (1 - impact["range_reduction"])  # Assuming 5km base range

        return {
            "impact_factors": impact,
            "adjusted_mission_duration": max(5, adjusted_duration),  # Minimum 5 minutes
            "adjusted_range": max(1000, adjusted_range),  # Minimum 1km
            "recommended_adjustments": self._get_mission_adjustments(impact, conditions)
        }

    def _get_mission_adjustments(self, impact: Dict, conditions: Dict) -> List[str]:
        """
        Get recommended mission adjustments based on weather impact.

        Args:
            impact: Calculated weather impact
            conditions: Weather conditions

        Returns:
            List of recommended adjustments
        """
        adjustments = []

        if impact["battery_consumption_multiplier"] > 1.1:
            adjustments.append("Consider shorter mission duration due to increased battery consumption")
            adjustments.append("Monitor battery levels more frequently")

        if impact["range_reduction"] > 0.1:
            adjustments.append("Reduce search area size or use more drones for coverage")
            adjustments.append("Plan for more frequent return-to-home cycles")

        if impact["sensor_effectiveness"] < 0.9:
            adjustments.append("Increase search altitude for better sensor coverage")
            adjustments.append("Consider thermal imaging for improved detection")

        if impact["safety_risk_multiplier"] > 1.2:
            adjustments.append("Implement stricter emergency protocols")
            adjustments.append("Reduce drone autonomy level")

        # Specific weather-based adjustments
        if conditions.get("wind_speed", 0) > 12:
            adjustments.append("Use wind-resistant search patterns")
            adjustments.append("Avoid downwind hovering positions")

        if conditions.get("condition", "") in ["Rain", "Snow"]:
            adjustments.append("Enable precipitation-resistant camera modes")
            adjustments.append("Increase image capture frequency for evidence")

        return adjustments

    async def get_optimal_mission_time(self, latitude: float, longitude: float, mission_duration: int) -> Dict:
        """
        Find optimal time window for mission execution based on weather forecast.

        Args:
            latitude: Mission latitude
            longitude: Mission longitude
            mission_duration: Mission duration in hours

        Returns:
            Optimal time window recommendations
        """
        forecast = await self.get_forecast(latitude, longitude, hours=48)

        if not forecast:
            return {"error": "Unable to retrieve weather forecast"}

        optimal_windows = []
        current_window = None

        for forecast_point in forecast:
            conditions = self.assess_flight_conditions(forecast_point)

            if conditions["recommendation"] in ["optimal", "acceptable"]:
                if current_window is None:
                    current_window = {
                        "start_time": forecast_point["timestamp"],
                        "conditions": [forecast_point],
                        "avg_safety_score": conditions["safety_score"]
                    }
                else:
                    current_window["conditions"].append(forecast_point)
                    current_window["avg_safety_score"] = (
                        current_window["avg_safety_score"] + conditions["safety_score"]
                    ) / 2
            else:
                if current_window is not None:
                    current_window["end_time"] = forecast_point["timestamp"]
                    current_window["duration"] = self._calculate_window_duration(current_window)
                    if current_window["duration"] >= mission_duration:
                        optimal_windows.append(current_window)
                    current_window = None

        # Close any open window at the end
        if current_window is not None:
            current_window["end_time"] = forecast[-1]["timestamp"]
            current_window["duration"] = self._calculate_window_duration(current_window)
            if current_window["duration"] >= mission_duration:
                optimal_windows.append(current_window)

        return {
            "optimal_windows": optimal_windows[:5],  # Return top 5 windows
            "immediate_conditions": self.assess_flight_conditions(forecast[0]) if forecast else None,
            "forecast_summary": self._summarize_forecast(forecast)
        }

    def _calculate_window_duration(self, window: Dict) -> int:
        """Calculate duration of a weather window in hours."""
        if "start_time" not in window or "end_time" not in window:
            return 0

        start = datetime.fromisoformat(window["start_time"].replace('Z', '+00:00'))
        end = datetime.fromisoformat(window["end_time"].replace('Z', '+00:00'))

        return int((end - start).total_seconds() / 3600)

    def _summarize_forecast(self, forecast: List[Dict]) -> Dict:
        """Create a summary of the weather forecast."""
        if not forecast:
            return {}

        temperatures = [f["temperature"] for f in forecast]
        wind_speeds = [f["wind_speed"] for f in forecast]
        conditions = [f["condition"] for f in forecast]

        return {
            "temperature_range": {"min": min(temperatures), "max": max(temperatures)},
            "wind_range": {"min": min(wind_speeds), "max": max(wind_speeds)},
            "common_conditions": max(set(conditions), key=conditions.count),
            "forecast_period": f"{forecast[0]['timestamp']} to {forecast[-1]['timestamp']}"
        }

    def get_weather_warnings(self, weather_data: Dict) -> List[str]:
        """
        Get specific weather warnings for drone operations.

        Args:
            weather_data: Current weather conditions

        Returns:
            List of weather warnings
        """
        warnings = []
        conditions = weather_data

        # Wind warnings
        if conditions.get("wind_speed", 0) > 10:
            warnings.append("Strong winds detected - monitor drone stability")
        if conditions.get("wind_gust", 0) > 15:
            warnings.append("Dangerous wind gusts - consider mission abort")

        # Precipitation warnings
        if "rain" in conditions.get("condition", "").lower():
            warnings.append("Precipitation detected - visibility and sensor effectiveness reduced")
        if "thunderstorm" in conditions.get("condition", "").lower():
            warnings.append("Thunderstorm activity - immediate return to base required")

        # Temperature warnings
        temp = conditions.get("temperature", 20)
        if temp > 35:
            warnings.append("High temperature - monitor battery temperature")
        if temp < 0:
            warnings.append("Freezing temperature - check for icing conditions")

        # Visibility warnings
        if conditions.get("visibility", 10000) < 2000:
            warnings.append("Reduced visibility - increase altitude and enable obstacle avoidance")

        return warnings

# Global weather service instance
weather_service = WeatherService()