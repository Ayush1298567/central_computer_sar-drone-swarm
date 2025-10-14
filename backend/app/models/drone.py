from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from ..core.database import Base


class DroneStatus(Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    FLYING = "flying"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    IDLE = "idle"
    MISSION = "mission"
    RETURNING = "returning"


class Drone(Base):
    """Represents a physical drone unit with its capabilities and current status."""
    __tablename__ = "drones"

    # Identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    status = Column(String(50), default="offline")
    drone_type = Column(String(50))
    max_altitude = Column(Float)
    max_speed = Column(Float)
    battery_capacity = Column(Float)
    camera_resolution = Column(String(50))
    has_thermal = Column(Boolean, default=False)
    has_night_vision = Column(Boolean, default=False)
    mission_id = Column(Integer)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # Enhanced identification and tracking
    drone_id = Column(String(50), nullable=False, index=True)
    serial_number = Column(String(100))
    connection_status = Column(String(50), default="disconnected")
    
    # Location and position
    position_lat = Column(Float)
    position_lng = Column(Float)
    position_alt = Column(Float)
    heading = Column(Float, default=0.0)
    speed = Column(Float, default=0.0)
    altitude = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    # Battery and power
    battery_level = Column(Float, default=0.0)
    battery_voltage = Column(Float)
    charging_status = Column(Boolean, default=False)

    # Performance capabilities
    max_flight_time = Column(Integer, default=25)
    cruise_speed = Column(Float, default=10.0)
    max_range = Column(Float, default=5000.0)
    coverage_rate = Column(Float, default=0.1)
    capabilities = Column(JSON)

    # Camera and sensor specs
    camera_specs = Column(JSON)
    sensor_specs = Column(JSON)
    flight_controller = Column(String(50))

    # Performance tracking
    total_flight_hours = Column(Float, default=0.0)
    missions_completed = Column(Integer, default=0)
    average_performance_score = Column(Float, default=0.0)

    # Maintenance
    last_maintenance = Column(DateTime)
    next_maintenance_due = Column(DateTime)
    maintenance_notes = Column(Text)

    # Communication
    signal_strength = Column(Integer, default=0)
    last_heartbeat = Column(DateTime)
    ip_address = Column(String(45))

    # Timestamps
    first_connected = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (forward references to avoid circular imports)
    mission_assignments = relationship("MissionDrone", back_populates="drone")
    telemetry_data = relationship("TelemetryData", back_populates="drone")
    discoveries = relationship("Discovery", back_populates="drone")
    
    def to_dict(self):
        """Convert drone to dictionary for API responses."""
        return {
            "id": self.id,
            "drone_id": self.drone_id,
            "name": self.name,
            "model": self.model,
            "serial_number": self.serial_number,
            "status": self.status,
            "connection_status": self.connection_status,
            "battery_level": self.battery_level,
            "position_lat": self.position_lat,
            "position_lng": self.position_lng,
            "position_alt": self.position_alt,
            "heading": self.heading,
            "speed": self.speed,
            "altitude": self.altitude,
            "is_active": self.is_active,
            "max_flight_time": self.max_flight_time,
            "max_altitude": self.max_altitude,
            "max_speed": self.max_speed,
            "cruise_speed": self.cruise_speed,
            "max_range": self.max_range,
            "coverage_rate": self.coverage_rate,
            "capabilities": self.capabilities,
            "signal_strength": self.signal_strength,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "ip_address": self.ip_address,
            "flight_controller": self.flight_controller,
            "total_flight_hours": self.total_flight_hours,
            "missions_completed": self.missions_completed,
            "average_performance_score": self.average_performance_score,
            "last_maintenance": self.last_maintenance.isoformat() if self.last_maintenance else None,
            "next_maintenance_due": self.next_maintenance_due.isoformat() if self.next_maintenance_due else None,
            "maintenance_notes": self.maintenance_notes,
            "first_connected": self.first_connected.isoformat() if self.first_connected else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }
    
    def update_performance_metrics(self, flight_time: float, area_covered: float):
        """Update drone performance metrics based on completed mission."""
        if flight_time > 0 and area_covered > 0:
            new_coverage_rate = area_covered / (flight_time / 60)
            # Exponential moving average
            self.coverage_rate = 0.8 * self.coverage_rate + 0.2 * new_coverage_rate
        
        self.missions_completed += 1
        self.total_flight_hours += flight_time / 60


class TelemetryData(Base):
    """Real-time telemetry data from drones during missions."""
    __tablename__ = "telemetry_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    
    # Position and orientation
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    heading = Column(Float)
    ground_speed = Column(Float)
    vertical_speed = Column(Float)
    
    # Battery and power
    battery_percentage = Column(Float)
    battery_voltage = Column(Float)
    power_consumption = Column(Float)
    
    # Flight status
    flight_mode = Column(String(50))
    armed_status = Column(Boolean)
    gps_fix_type = Column(Integer)
    satellite_count = Column(Integer)
    
    # Environmental
    temperature = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    
    # Communication
    signal_strength = Column(Integer)
    data_rate = Column(Float)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    drone = relationship("Drone", back_populates="telemetry_data")


class DroneStateHistory(Base):
    """Historical drone state snapshots for mission persistence and analysis."""
    __tablename__ = "drone_state_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), index=True, nullable=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), index=True, nullable=False)

    # State snapshot
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50))
    connection_status = Column(String(50))

    position_lat = Column(Float)
    position_lng = Column(Float)
    position_alt = Column(Float)
    heading = Column(Float)
    speed = Column(Float)

    battery_level = Column(Float)
    signal_strength = Column(Integer)

    # Optional payload for extensibility
    extra = Column(JSON)

    # Index hints (SQLAlchemy will generate based on index=True above; explicit composite indices recommended in Alembic)
