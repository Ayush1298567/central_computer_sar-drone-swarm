from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Integer, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .mission import Base

class Drone(Base):
    """
    Represents a physical drone unit with its capabilities and current status.
    """
    __tablename__ = "drones"

    # Identification
    id = Column(String(50), primary_key=True)  # Unique drone identifier
    name = Column(String(100), nullable=False)
    model = Column(String(100))  # Drone hardware model
    serial_number = Column(String(100))

    # Current status
    status = Column(String(50), default="offline")  # offline, online, flying, charging, maintenance
    connection_status = Column(String(50), default="disconnected")  # disconnected, connected, unstable

    # Location and position
    current_position = Column(JSON)  # Current GPS coordinates [lat, lng, alt]
    home_position = Column(JSON)  # Launch/return position [lat, lng, alt]

    # Battery and power
    battery_level = Column(Float, default=0.0)  # Current battery percentage (0-100)
    battery_voltage = Column(Float)  # Current battery voltage
    charging_status = Column(Boolean, default=False)

    # Performance capabilities (learned over time)
    max_flight_time = Column(Integer, default=25)  # Maximum flight time in minutes
    cruise_speed = Column(Float, default=10.0)  # Cruise speed in m/s
    max_range = Column(Float, default=5000.0)  # Maximum range in meters
    coverage_rate = Column(Float, default=0.1)  # km²/minute coverage rate

    # Communication
    signal_strength = Column(Integer, default=0)  # Signal strength (0-100)
    last_heartbeat = Column(DateTime)  # Last communication timestamp
    ip_address = Column(String(45))  # IP address for communication

    # Hardware configuration
    camera_specs = Column(JSON)  # Camera specifications and capabilities
    sensor_specs = Column(JSON)  # LiDAR and other sensor specifications
    flight_controller = Column(String(50))  # Flight controller type/version

    # Performance tracking
    total_flight_hours = Column(Float, default=0.0)
    missions_completed = Column(Integer, default=0)
    average_performance_score = Column(Float, default=0.0)  # 0-1 performance rating

    # Maintenance
    last_maintenance = Column(DateTime)
    next_maintenance_due = Column(DateTime)
    maintenance_notes = Column(Text)

    # Timestamps
    first_connected = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mission_assignments = relationship("DroneAssignment", back_populates="drone")
    telemetry_data = relationship("TelemetryData", back_populates="drone")
    discoveries = relationship("Discovery", back_populates="drone")

    def to_dict(self):
        """Convert drone to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "connection_status": self.connection_status,
            "current_position": self.current_position,
            "battery_level": self.battery_level,
            "signal_strength": self.signal_strength,
            "max_flight_time": self.max_flight_time,
            "coverage_rate": self.coverage_rate,
            "missions_completed": self.missions_completed,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }

    def update_performance_metrics(self, flight_time: float, area_covered: float):
        """Update drone performance metrics based on completed mission."""
        if flight_time > 0 and area_covered > 0:
            new_coverage_rate = area_covered / (flight_time / 60)  # km²/minute
            # Exponential moving average to update coverage rate
            self.coverage_rate = 0.8 * self.coverage_rate + 0.2 * new_coverage_rate

        self.missions_completed += 1
        self.total_flight_hours += flight_time / 60

class TelemetryData(Base):
    """
    Real-time telemetry data from drones during missions.
    """
    __tablename__ = "telemetry_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drone_id = Column(String(50), ForeignKey("drones.id"), nullable=False)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"))

    # Position and orientation
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    heading = Column(Float)  # Compass heading in degrees
    ground_speed = Column(Float)  # Speed over ground in m/s
    vertical_speed = Column(Float)  # Vertical speed in m/s

    # Battery and power
    battery_percentage = Column(Float)
    battery_voltage = Column(Float)
    power_consumption = Column(Float)  # Current power draw in watts

    # Flight status
    flight_mode = Column(String(50))  # AUTO, GUIDED, RTL, etc.
    armed_status = Column(Boolean)
    gps_fix_type = Column(Integer)  # GPS fix quality
    satellite_count = Column(Integer)

    # Environmental
    temperature = Column(Float)  # Ambient temperature
    humidity = Column(Float)
    pressure = Column(Float)  # Barometric pressure
    wind_speed = Column(Float)
    wind_direction = Column(Float)

    # Communication
    signal_strength = Column(Integer)
    data_rate = Column(Float)  # Data transmission rate

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    drone = relationship("Drone", back_populates="telemetry_data")