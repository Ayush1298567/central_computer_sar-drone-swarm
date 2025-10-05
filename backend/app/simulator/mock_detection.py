"""
Mock detection system for simulating AI object detection.
"""

import logging
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MockDetectionSystem:
    """Simulates AI-powered object detection for testing."""

    def __init__(self):
        self.detection_models = {
            "person": {
                "accuracy": 0.85,
                "false_positive_rate": 0.05,
                "detection_zones": ["urban", "suburban", "rural"]
            },
            "vehicle": {
                "accuracy": 0.92,
                "false_positive_rate": 0.03,
                "detection_zones": ["urban", "roads", "parking"]
            },
            "building": {
                "accuracy": 0.78,
                "false_positive_rate": 0.08,
                "detection_zones": ["urban", "suburban"]
            },
            "debris": {
                "accuracy": 0.65,
                "false_positive_rate": 0.15,
                "detection_zones": ["disaster", "construction", "natural"]
            }
        }

    def detect_objects(self, image_data: Dict, detection_types: List[str] = None) -> List[Dict]:
        """Simulate object detection on image data."""
        detections = []

        # Determine environment type based on location
        environment = self._determine_environment(image_data.get("location", {}))

        # Filter detection types if specified
        available_types = detection_types or list(self.detection_models.keys())

        # Simulate detection for each type
        for detection_type in available_types:
            if detection_type in self.detection_models:
                detection = self._simulate_single_detection(
                    detection_type,
                    image_data,
                    environment
                )

                if detection:
                    detections.append(detection)

        return detections

    def _determine_environment(self, location: Dict) -> str:
        """Determine environment type based on GPS coordinates."""
        lat = location.get("lat", 0)
        lng = location.get("lng", 0)

        # Simple environment classification based on coordinates
        # In a real system, this would use mapping data
        if 37.7 < lat < 37.8 and -122.5 < lng < -122.3:
            return "urban"  # San Francisco area
        elif abs(lat) > 50 or abs(lng) > 125:
            return "rural"
        else:
            return "suburban"

    def _simulate_single_detection(
        self,
        detection_type: str,
        image_data: Dict,
        environment: str
    ) -> Optional[Dict]:
        """Simulate detection of a single object type."""

        model_config = self.detection_models[detection_type]

        # Check if detection is possible in this environment
        if environment not in model_config["detection_zones"]:
            return None

        # Calculate detection probability
        base_probability = model_config["accuracy"]

        # Adjust for image quality
        image_quality = image_data.get("quality", 1.0)
        detection_probability = base_probability * image_quality

        # Adjust for lighting conditions
        lighting = image_data.get("lighting", "good")
        lighting_factors = {
            "excellent": 1.2,
            "good": 1.0,
            "fair": 0.8,
            "poor": 0.6,
            "terrible": 0.3
        }
        detection_probability *= lighting_factors.get(lighting, 1.0)

        # Random detection decision
        if random.random() < detection_probability:
            # Generate detection result
            detection = {
                "type": detection_type,
                "confidence": round(random.uniform(0.6, 0.95), 2),
                "bounding_box": self._generate_bounding_box(),
                "attributes": self._generate_detection_attributes(detection_type),
                "timestamp": datetime.now().isoformat(),
                "model_used": f"mock_{detection_type}_detector",
                "environment": environment
            }

            logger.debug(f"Mock detection: {detection_type} with confidence {detection['confidence']}")
            return detection

        return None

    def _generate_bounding_box(self) -> Dict:
        """Generate a random bounding box for detected object."""
        # Random box somewhere in the image
        x1 = random.randint(50, 400)
        y1 = random.randint(50, 300)
        width = random.randint(20, 100)
        height = random.randint(20, 100)

        return {
            "x": x1,
            "y": y1,
            "width": width,
            "height": height,
            "confidence": round(random.uniform(0.8, 0.99), 2)
        }

    def _generate_detection_attributes(self, detection_type: str) -> Dict:
        """Generate attributes for the detected object."""
        attributes = {}

        if detection_type == "person":
            attributes = {
                "estimated_age": random.choice(["child", "adult", "elderly"]),
                "clothing_color": random.choice(["dark", "light", "bright", "camouflage"]),
                "movement": random.choice(["stationary", "slow", "fast"]),
                "posture": random.choice(["standing", "sitting", "lying", "crouching"])
            }
        elif detection_type == "vehicle":
            attributes = {
                "vehicle_type": random.choice(["car", "truck", "motorcycle", "bicycle"]),
                "color": random.choice(["white", "black", "red", "blue", "silver", "dark"]),
                "size": random.choice(["small", "medium", "large"]),
                "condition": random.choice(["intact", "damaged", "abandoned"])
            }
        elif detection_type == "building":
            attributes = {
                "structure_type": random.choice(["residential", "commercial", "industrial"]),
                "damage_level": random.choice(["none", "minor", "moderate", "severe", "collapsed"]),
                "occupancy": random.choice(["occupied", "vacant", "unknown"])
            }
        elif detection_type == "debris":
            attributes = {
                "debris_type": random.choice(["concrete", "wood", "metal", "mixed"]),
                "size": random.choice(["small", "medium", "large", "massive"]),
                "hazard_level": random.choice(["low", "medium", "high"])
            }

        return attributes

    def simulate_batch_detection(
        self,
        mission_area: Dict,
        flight_duration_minutes: int,
        detection_interval_seconds: int = 30
    ) -> List[Dict]:
        """Simulate a batch of detections over a mission period."""

        detections = []
        num_intervals = int((flight_duration_minutes * 60) / detection_interval_seconds)

        for i in range(num_intervals):
            # Generate random position within mission area
            position = {
                "lat": mission_area["center"]["lat"] + (random.random() - 0.5) * 0.01,
                "lng": mission_area["center"]["lng"] + (random.random() - 0.5) * 0.01,
                "altitude": 50.0
            }

            # Simulate image capture
            image_data = {
                "location": position,
                "quality": random.uniform(0.7, 1.0),
                "lighting": random.choice(["good", "fair", "excellent"])
            }

            # Detect objects
            interval_detections = self.detect_objects(image_data)
            detections.extend(interval_detections)

        return detections

    def get_detection_statistics(self) -> Dict:
        """Get statistics about the mock detection system."""
        stats = {}

        for detection_type, config in self.detection_models.items():
            stats[detection_type] = {
                "accuracy": config["accuracy"],
                "false_positive_rate": config["false_positive_rate"],
                "supported_environments": config["detection_zones"]
            }

        return stats


# Global instance
mock_detection_system = MockDetectionSystem()