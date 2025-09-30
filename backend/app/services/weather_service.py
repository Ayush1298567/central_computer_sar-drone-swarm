import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings

class WeatherService:
    """Weather monitoring and forecasting service."""

    def __init__(self):
        self.weather_data = {}

    async def get_current_weather(self, location: dict) -> dict:
        """Get current weather conditions."""
        return {
            "temperature": 22,
            "wind_speed": 5,
            "conditions": "clear",
            "safe_to_fly": True
        }

weather_service = WeatherService()