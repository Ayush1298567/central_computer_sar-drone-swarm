"""
Database initialization script.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db, SessionLocal, Base, engine
from app.models.mission import Mission, MissionDrone
from app.models.drone import Drone, TelemetryData
from app.models.discovery import Discovery
from app.models.chat import ChatMessageDB, ChatSession
from datetime import datetime


def init_database():
    """Initialize database with sample data."""
    print("Initializing SAR Mission Commander database...")

    # Drop all tables first to ensure clean slate
    from app.core.database import engine
    Base.metadata.drop_all(bind=engine)
    print("Existing tables dropped")

    # Create tables
    import asyncio
    asyncio.run(init_db())
    print("Database tables created")

    # Create sample data
    create_sample_data()
    print("Sample data created")

    print("Database initialization complete!")


def create_sample_data():
    """Create sample missions, drones, and discoveries."""
    db = SessionLocal()

    try:
        # Create sample drones
        drones_data = [
            {
                "drone_id": "drone_alpha_1",
                "name": "Alpha-1",
                "model": "DJI Matrice 300",
                "status": "available",
                "position_lat": 37.7749,
                "position_lng": -122.4194,
                "altitude": 0.0,
                "battery_level": 85.0,
                "max_flight_time": 25,
                "max_altitude": 120.0,
                "max_speed": 20.0,
                "speed": 0.0,
                "is_active": True
            },
            {
                "drone_id": "drone_bravo_2",
                "name": "Bravo-2",
                "model": "DJI Mavic 2 Enterprise",
                "status": "available",
                "position_lat": 37.7750,
                "position_lng": -122.4200,
                "altitude": 0.0,
                "battery_level": 92.0,
                "max_flight_time": 30,
                "max_altitude": 100.0,
                "max_speed": 18.0,
                "speed": 0.0,
                "is_active": True
            },
            {
                "drone_id": "drone_charlie_3",
                "name": "Charlie-3",
                "model": "Custom SAR Drone",
                "status": "maintenance",
                "position_lat": 37.7745,
                "position_lng": -122.4185,
                "altitude": 0.0,
                "battery_level": 45.0,
                "max_flight_time": 20,
                "max_altitude": 150.0,
                "max_speed": 25.0,
                "speed": 0.0,
                "is_active": False
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
            mission_id="mission_001",
            name="Urban Search - Downtown District",
            description="Search for missing person in downtown area following building collapse",
            status="planning",
            priority=5,
            mission_type="search",
            center_lat=37.7749,
            center_lng=-122.4194,
            search_area={
                "type": "Polygon",
                "coordinates": [[
                    [-122.4194, 37.7749],
                    [-122.4200, 37.7749],
                    [-122.4200, 37.7755],
                    [-122.4194, 37.7755],
                    [-122.4194, 37.7749]
                ]]
            },
            search_altitude=50.0,
            estimated_duration=90,
            max_drones=2,
            search_pattern="lawnmower",
            overlap_percentage=10.0
        )

        db.add(mission)
        db.commit()
        db.refresh(mission)

        # Create sample discoveries
        discoveries_data = [
            {
                "mission_id": mission.id,
                "drone_id": drones[0].id,
                "discovery_type": "person",
                "confidence": 0.85,
                "latitude": 37.7750,
                "longitude": -122.4200,
                "altitude": 10.0,
                "description": "Person detected in search area",
                "priority": 3
            },
            {
                "mission_id": mission.id,
                "drone_id": drones[1].id,
                "discovery_type": "vehicle",
                "confidence": 0.92,
                "latitude": 37.7745,
                "longitude": -122.4185,
                "altitude": 15.0,
                "description": "Vehicle detected in search area",
                "priority": 2
            }
        ]

        for discovery_data in discoveries_data:
            discovery = Discovery(**discovery_data)
            discovery.discovered_at = datetime.now()
            db.add(discovery)

        # Create sample chat messages
        chat_messages_data = [
            {
                "session_id": "session_001",
                "content": "Hello! I'm your AI mission planner. I'll help you create a comprehensive search and rescue mission. What type of area would you like to search and where is it located?",
                "message_type": "text",
                "user_id": "system"
            },
            {
                "session_id": "session_001",
                "content": "I need to search a collapsed building in downtown San Francisco. The coordinates are approximately 37.7749, -122.4194.",
                "message_type": "text",
                "user_id": "user"
            },
            {
                "session_id": "session_001",
                "content": "Great! I've set the mission center to coordinates 37.7749, -122.4194. Now, what size area would you like to search? (e.g., '5 square kilometers' or '2 hectares')",
                "message_type": "text",
                "user_id": "system"
            },
            {
                "session_id": "session_001",
                "content": "Let's search about 2.5 square kilometers around the building.",
                "message_type": "text",
                "user_id": "user"
            },
            {
                "session_id": "session_001",
                "content": "Perfect! I've set the search area to 2.5 square kilometers. Now, at what altitude should the drones fly? (e.g., '50 meters' or '100 feet')",
                "message_type": "text",
                "user_id": "system"
            }
        ]

        # Create a sample chat session first
        chat_session = ChatSession(
            id="session_001",
            title="Urban Search Mission Planning",
            mission_id=mission.mission_id
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

        # Update session_id in chat messages
        for chat_data in chat_messages_data:
            chat_data["session_id"] = chat_session.id

        for chat_data in chat_messages_data:
            chat_message = ChatMessageDB(**chat_data)
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
