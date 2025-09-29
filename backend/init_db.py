"""
Database initialization script.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import create_tables, SessionLocal
from app.models import Mission, Drone, Discovery, ChatMessage
from datetime import datetime


def init_database():
    """Initialize database with sample data."""
    print("Initializing SAR Mission Commander database...")

    # Create tables
    create_tables()
    print("✓ Database tables created")

    # Create sample data
    create_sample_data()
    print("✓ Sample data created")

    print("Database initialization complete!")


def create_sample_data():
    """Create sample missions, drones, and discoveries."""
    db = SessionLocal()

    try:
        # Create sample drones
        drones_data = [
            {
                "name": "Alpha-1",
                "model": "DJI Matrice 300",
                "serial_number": "M300-001",
                "status": "available",
                "max_speed": 20.0,
                "max_altitude": 120.0,
                "camera_resolution": "4K",
                "has_thermal": True,
                "has_night_vision": True,
                "flight_hours": 45.5,
                "notes": "Primary search drone with thermal imaging"
            },
            {
                "name": "Bravo-2",
                "model": "DJI Mavic 2 Enterprise",
                "serial_number": "M2E-002",
                "status": "available",
                "max_speed": 18.0,
                "max_altitude": 100.0,
                "camera_resolution": "1080p",
                "has_thermal": False,
                "has_night_vision": True,
                "flight_hours": 23.8,
                "notes": "Secondary drone for detailed inspection"
            },
            {
                "name": "Charlie-3",
                "model": "Custom SAR Drone",
                "serial_number": "SAR-003",
                "status": "maintenance",
                "max_speed": 25.0,
                "max_altitude": 150.0,
                "camera_resolution": "4K",
                "has_thermal": True,
                "has_night_vision": True,
                "flight_hours": 67.2,
                "notes": "High-altitude long-range drone"
            }
        ]

        drones = []
        for drone_data in drones_data:
            drone = Drone(**drone_data)
            drone.last_seen = datetime.now()
            db.add(drone)
            drones.append(drone)

        db.commit()

        # Create sample mission
        mission = Mission(
            name="Urban Search - Downtown District",
            description="Search for missing person in downtown area following building collapse",
            status="planning",
            center_lat=37.7749,
            center_lng=-122.4194,
            area_size_km2=2.5,
            search_altitude=50.0,
            priority="high",
            weather_conditions={
                "temperature": 22,
                "wind_speed": 12,
                "visibility": 8,
                "conditions": "Partly cloudy"
            },
            estimated_duration=90
        )

        db.add(mission)
        db.commit()
        db.refresh(mission)

        # Create sample discoveries
        discoveries_data = [
            {
                "mission_id": mission.id,
                "drone_id": drones[0].id,
                "lat": 37.7750,
                "lng": -122.4200,
                "discovery_type": "person",
                "confidence": 0.85,
                "description": "Possible person spotted in rubble",
                "category": "human",
                "status": "investigating",
                "priority": "high",
                "response_required": True,
                "response_type": "medical"
            },
            {
                "mission_id": mission.id,
                "drone_id": drones[1].id,
                "lat": 37.7745,
                "lng": -122.4185,
                "discovery_type": "vehicle",
                "confidence": 0.92,
                "description": "Abandoned vehicle near collapse site",
                "category": "vehicle",
                "status": "confirmed",
                "priority": "normal"
            }
        ]

        for discovery_data in discoveries_data:
            discovery = Discovery(**discovery_data)
            discovery.discovered_at = datetime.now()
            db.add(discovery)

        # Create sample chat messages
        chat_messages_data = [
            {
                "mission_id": mission.id,
                "sender": "ai",
                "message": "Hello! I'm your AI mission planner. I'll help you create a comprehensive search and rescue mission. What type of area would you like to search and where is it located?",
                "message_type": "text",
                "ai_context": {"stage": "greeting", "next_question": "location"}
            },
            {
                "mission_id": mission.id,
                "sender": "user",
                "message": "I need to search a collapsed building in downtown San Francisco. The coordinates are approximately 37.7749, -122.4194.",
                "message_type": "text"
            },
            {
                "mission_id": mission.id,
                "sender": "ai",
                "message": "Great! I've set the mission center to coordinates 37.7749, -122.4194. Now, what size area would you like to search? (e.g., '5 square kilometers' or '2 hectares')",
                "message_type": "text",
                "ai_context": {"stage": "area", "parameters": {"center_lat": 37.7749, "center_lng": -122.4194}}
            },
            {
                "mission_id": mission.id,
                "sender": "user",
                "message": "Let's search about 2.5 square kilometers around the building.",
                "message_type": "text"
            },
            {
                "mission_id": mission.id,
                "sender": "ai",
                "message": "Perfect! I've set the search area to 2.5 square kilometers. Now, at what altitude should the drones fly? (e.g., '50 meters' or '100 feet')",
                "message_type": "text",
                "ai_context": {"stage": "altitude", "parameters": {"area_size_km2": 2.5}}
            }
        ]

        for chat_data in chat_messages_data:
            chat_message = ChatMessage(**chat_data)
            db.add(chat_message)

        db.commit()

        print(f"Created sample mission: {mission.name}")
        print(f"Created {len(drones)} sample drones")
        print(f"Created {len(discoveries_data)} sample discoveries")
        print(f"Created {len(chat_messages_data)} sample chat messages")

    except Exception as e:
        db.rollback()
        print(f"Error creating sample data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()