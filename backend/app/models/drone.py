from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Drone(Base):
    """Represents a physical drone unit with its capabilities and current status."""
    __tablename__ = "drones"
    
    # Identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    serial_number = Column(String(100))
    
    # Current status
    status = Column(String(50), default="offline")
    connection_status = Column(String(50), default="disconnected")
    
    # Location and position
    current_position = Column(JSON)  # [lat, lng, alt]
    home_position = Column(JSON)  # [lat, lng, alt]
    
    # Battery and power
    battery_level = Column(Float, default=0.0)
    battery_voltage = Column(Float)
    charging_status = Column(Boolean, default=False)
    
    # Performance capabilities
    max_flight_time = Column(Integer, default=25)
    cruise_speed = Column(Float, default=10.0)
    max_range = Column(Float, default=5000.0)
    coverage_rate = Column(Float, default=0.1)
    
    # Communication
    signal_strength = Column(Integer, default=0)
    last_heartbeat = Column(DateTime)
    ip_address = Column(String(45))
    
    # Hardware configuration
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
    
    # Timestamps
    first_connected = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mission_assignments = relationship("MissionDrone", back_populates="drone")
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
