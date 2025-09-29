"""
Drone Simulator for SAR Mission Testing

This module provides a realistic drone simulator that mimics real drone behavior
for testing the SAR system without requiring actual hardware.
"""

import asyncio
import json
import math
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class FlightMode(Enum):
    """Drone flight modes"""
    IDLE = "idle"
    TAKEOFF = "takeoff"
    LANDING = "landing"
    MANUAL = "manual"
    AUTO = "auto"
    RTL = "rtl"  # Return to launch
    LOITER = "loiter"
    MISSION = "mission"


class DroneStatus(Enum):
    """Drone operational status"""
    OFFLINE = "offline"
    ONLINE = "online"
    FLYING = "flying"
    LANDING = "landing"
    ERROR = "error"
    LOW_BATTERY = "low_battery"
    CONNECTION_LOST = "connection_lost"


@dataclass
class Position:
    """Geographic position with altitude"""
    latitude: float
    longitude: float
    altitude: float
    heading: float = 0.0
    ground_speed: float = 0.0


@dataclass
class Battery:
    """Battery status information"""
    level: float  # Percentage 0-100
    voltage: float  # Volts
    current: float  # Amps
    temperature: float  # Celsius
    cycles: int = 0
    time_remaining: int = 0  # seconds


@dataclass
class TelemetryData:
    """Complete telemetry data packet"""
    timestamp: datetime
    position: Position
    battery: Battery
    attitude: Dict[str, float]  # roll, pitch, yaw
    velocity: Dict[str, float]  # vx, vy, vz
    signal_strength: int  # 0-100
    flight_mode: FlightMode
    status: DroneStatus
    armed: bool = False
    mission_progress: float = 0.0
    wind_speed: float = 0.0
    wind_direction: float = 0.0


@dataclass
class Waypoint:
    """Navigation waypoint"""
    latitude: float
    longitude: float
    altitude: float
    speed: float = 5.0  # m/s
    wait_time: float = 0.0  # seconds to wait at waypoint
    action: str = "navigate"  # navigate, takeoff, land, loiter


@dataclass
class Mission:
    """Mission definition"""
    id: str
    name: str
    waypoints: List[Waypoint] = field(default_factory=list)
    search_area: Optional[List[List[float]]] = None
    search_pattern: str = "lawnmower"
    search_altitude: float = 25.0
    search_speed: float = 3.0
    recording_mode: str = "continuous"


class DroneSimulator:
    """
    Realistic drone simulator for SAR mission testing.

    Provides:
    - Realistic flight dynamics and behavior
    - Battery consumption modeling
    - Telemetry data generation
    - Mission execution simulation
    - Environmental factor simulation
    """

    def __init__(self, drone_id: str, home_position: Tuple[float, float, float] = (40.7128, -74.0060, 0.0)):
        """
        Initialize drone simulator

        Args:
            drone_id: Unique drone identifier
            home_position: (latitude, longitude, altitude) of home location
        """
        self.drone_id = drone_id
        self.home_position = Position(*home_position)

        # Current state
        self.current_position = Position(*home_position)
        self.target_position = Position(*home_position)
        self.battery = Battery(level=100.0, voltage=16.8, current=0.0, temperature=25.0)
        self.flight_mode = FlightMode.IDLE
        self.status = DroneStatus.ONLINE
        self.armed = False

        # Mission state
        self.current_mission: Optional[Mission] = None
        self.mission_waypoints: List[Waypoint] = []
        self.current_waypoint_index = 0
        self.mission_progress = 0.0

        # Simulation parameters
        self.max_speed = 15.0  # m/s
        self.max_altitude = 120.0  # meters
        self.battery_discharge_rate = 2.5  # % per minute at cruise
        self.signal_strength = 95  # 0-100

        # Environmental conditions
        self.wind_speed = 2.0  # m/s
        self.wind_direction = 45.0  # degrees
        self.temperature = 20.0  # celsius

        # Simulation timing
        self.last_update = time.time()
        self.update_interval = 0.1  # seconds

        # Callbacks for external integration
        self.telemetry_callback = None
        self.discovery_callback = None
        self.status_callback = None

        logger.info(f"Drone simulator {drone_id} initialized at {home_position}")

    def set_telemetry_callback(self, callback):
        """Set callback for telemetry updates"""
        self.telemetry_callback = callback

    def set_discovery_callback(self, callback):
        """Set callback for discovery events"""
        self.discovery_callback = callback

    def set_status_callback(self, callback):
        """Set callback for status changes"""
        self.status_callback = callback

    async def start(self):
        """Start the drone simulator"""
        logger.info(f"Starting drone simulator {self.drone_id}")
        self.status = DroneStatus.ONLINE
        await self._simulation_loop()

    async def stop(self):
        """Stop the drone simulator"""
        logger.info(f"Stopping drone simulator {self.drone_id}")
        self.status = DroneStatus.OFFLINE
        self.flight_mode = FlightMode.IDLE

    async def arm(self):
        """Arm the drone for flight"""
        if self.status in [DroneStatus.ONLINE, DroneStatus.FLYING]:
            self.armed = True
            logger.info(f"Drone {self.drone_id} armed")
            if self.status_callback:
                await self.status_callback(self.drone_id, "armed", True)
        else:
            raise ValueError("Cannot arm drone - not in valid state")

    async def disarm(self):
        """Disarm the drone"""
        self.armed = False
        logger.info(f"Drone {self.drone_id} disarmed")
        if self.status_callback:
            await self.status_callback(self.drone_id, "armed", False)

    async def takeoff(self, altitude: float = 10.0):
        """Execute takeoff to specified altitude"""
        if not self.armed:
            raise ValueError("Cannot takeoff - drone not armed")

        logger.info(f"Drone {self.drone_id} taking off to {altitude}m")
        self.flight_mode = FlightMode.TAKEOFF
        self.status = DroneStatus.FLYING

        # Simulate takeoff sequence
        target_alt = min(altitude, self.max_altitude)
        await self._move_to_position(Position(
            self.current_position.latitude,
            self.current_position.longitude,
            target_alt,
            heading=self.current_position.heading
        ))

        self.flight_mode = FlightMode.LOITER
        if self.status_callback:
            await self.status_callback(self.drone_id, "takeoff_complete", {"altitude": target_alt})

    async def land(self):
        """Execute landing sequence"""
        logger.info(f"Drone {self.drone_id} landing")
        self.flight_mode = FlightMode.LANDING

        # Simulate landing sequence
        await self._move_to_position(Position(
            self.current_position.latitude,
            self.current_position.longitude,
            0.0,
            heading=self.current_position.heading
        ))

        self.flight_mode = FlightMode.IDLE
        self.status = DroneStatus.ONLINE
        self.armed = False

        if self.status_callback:
            await self.status_callback(self.drone_id, "landed", {})

    async def return_to_launch(self):
        """Return to home position"""
        logger.info(f"Drone {self.drone_id} returning to launch")
        self.flight_mode = FlightMode.RTL
        await self._move_to_position(self.home_position)
        await self.land()

    async def start_mission(self, mission: Mission):
        """Start executing a mission"""
        logger.info(f"Drone {self.drone_id} starting mission {mission.id}")
        self.current_mission = mission
        self.mission_waypoints = mission.waypoints
        self.current_waypoint_index = 0
        self.mission_progress = 0.0
        self.flight_mode = FlightMode.MISSION

        # Takeoff if not already flying
        if self.status != DroneStatus.FLYING:
            await self.takeoff(mission.search_altitude)

        # Execute mission waypoints
        await self._execute_mission()

    async def _execute_mission(self):
        """Execute mission waypoints"""
        if not self.mission_waypoints:
            logger.warning(f"No waypoints defined for mission {self.current_mission.id}")
            return

        total_waypoints = len(self.mission_waypoints)

        for i, waypoint in enumerate(self.mission_waypoints):
            self.current_waypoint_index = i
            self.mission_progress = (i / total_waypoints) * 100.0

            logger.info(f"Executing waypoint {i+1}/{total_waypoints}")

            # Move to waypoint
            await self._move_to_position(Position(
                waypoint.latitude,
                waypoint.longitude,
                waypoint.altitude,
                heading=self._calculate_heading(self.current_position, waypoint)
            ))

            # Wait at waypoint if specified
            if waypoint.wait_time > 0:
                await asyncio.sleep(waypoint.wait_time)

            # Simulate discovery detection (will be enhanced by MockDetectionSystem)
            if random.random() < 0.1:  # 10% chance of discovery per waypoint
                await self._simulate_discovery(waypoint)

        # Mission complete
        self.mission_progress = 100.0
        logger.info(f"Mission {self.current_mission.id} completed")

        if self.status_callback:
            await self.status_callback(self.drone_id, "mission_complete", {
                "mission_id": self.current_mission.id,
                "progress": self.mission_progress
            })

    async def _move_to_position(self, target: Position):
        """Move drone to target position with realistic flight dynamics"""
        distance = self._calculate_distance(self.current_position, target)
        bearing = self._calculate_bearing(self.current_position, target)

        # Calculate flight time based on distance and speed
        cruise_speed = min(self.max_speed, target.ground_speed or 5.0)
        flight_time = distance / cruise_speed

        # Update position gradually
        steps = int(flight_time / self.update_interval)
        if steps < 1:
            steps = 1

        for step in range(steps):
            if self.status not in [DroneStatus.FLYING]:
                break

            # Calculate intermediate position
            t = step / steps
            current_lat = self.current_position.latitude + t * (target.latitude - self.current_position.latitude)
            current_lon = self.current_position.longitude + t * (target.longitude - self.current_position.longitude)
            current_alt = self.current_position.altitude + t * (target.altitude - self.current_position.altitude)

            # Add some realistic variation due to wind and control
            wind_effect_lat = math.sin(math.radians(self.wind_direction)) * self.wind_speed * self.update_interval * 0.001
            wind_effect_lon = math.cos(math.radians(self.wind_direction)) * self.wind_speed * self.update_interval * 0.001

            self.current_position = Position(
                current_lat + wind_effect_lat,
                current_lon + wind_effect_lon,
                current_alt,
                heading=bearing,
                ground_speed=cruise_speed
            )

            # Update battery consumption
            await self._update_battery()

            # Generate and send telemetry
            await self._send_telemetry()

            await asyncio.sleep(self.update_interval)

    async def _update_battery(self):
        """Update battery level based on flight conditions"""
        if self.status == DroneStatus.FLYING:
            # Base discharge rate
            discharge_rate = self.battery_discharge_rate

            # Increase discharge rate based on flight conditions
            if self.current_position.ground_speed > 10:
                discharge_rate *= 1.5  # High speed flight
            if self.current_position.altitude > 50:
                discharge_rate *= 1.2  # High altitude flight
            if self.wind_speed > 5:
                discharge_rate *= 1.3  # Wind resistance

            # Update battery level
            self.battery.level = max(0.0, self.battery.level - (discharge_rate * self.update_interval / 60.0))

            # Update time remaining estimate
            if self.battery.level > 0:
                self.battery.time_remaining = int((self.battery.level / discharge_rate) * 60)
            else:
                self.battery.time_remaining = 0

            # Check for low battery
            if self.battery.level < 15 and self.status != DroneStatus.LOW_BATTERY:
                self.status = DroneStatus.LOW_BATTERY
                logger.warning(f"Drone {self.drone_id} battery low: {self.battery.level:.1f}%")
                if self.status_callback:
                    await self.status_callback(self.drone_id, "low_battery", {"level": self.battery.level})

    async def _send_telemetry(self):
        """Generate and send telemetry data"""
        telemetry = TelemetryData(
            timestamp=datetime.now(),
            position=self.current_position,
            battery=self.battery,
            attitude={
                "roll": random.uniform(-5, 5),
                "pitch": random.uniform(-5, 5),
                "yaw": self.current_position.heading
            },
            velocity={
                "vx": self.current_position.ground_speed * math.cos(math.radians(self.current_position.heading)),
                "vy": self.current_position.ground_speed * math.sin(math.radians(self.current_position.heading)),
                "vz": 0.0
            },
            signal_strength=self.signal_strength,
            flight_mode=self.flight_mode,
            status=self.status,
            armed=self.armed,
            mission_progress=self.mission_progress,
            wind_speed=self.wind_speed,
            wind_direction=self.wind_direction
        )

        if self.telemetry_callback:
            await self.telemetry_callback(self.drone_id, telemetry)

    async def _simulate_discovery(self, waypoint: Waypoint):
        """Simulate a discovery at the current waypoint"""
        if self.discovery_callback:
            await self.discovery_callback(self.drone_id, {
                "object_type": random.choice(["person", "vehicle", "structure", "debris"]),
                "confidence_score": random.uniform(0.7, 0.95),
                "latitude": waypoint.latitude + random.uniform(-0.001, 0.001),
                "longitude": waypoint.longitude + random.uniform(-0.001, 0.001),
                "altitude": waypoint.altitude,
                "detection_method": "simulated",
                "timestamp": datetime.now()
            })

    async def _simulation_loop(self):
        """Main simulation loop"""
        while self.status != DroneStatus.OFFLINE:
            try:
                current_time = time.time()
                if current_time - self.last_update >= self.update_interval:
                    await self._send_telemetry()
                    self.last_update = current_time

                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
                await asyncio.sleep(1.0)

    def _calculate_distance(self, pos1: Position, pos2: Position) -> float:
        """Calculate distance between two positions in meters"""
        # Simplified calculation - in reality would use proper geodetic formulas
        lat_diff = (pos2.latitude - pos1.latitude) * 111320  # meters per degree
        lon_diff = (pos2.longitude - pos1.longitude) * 111320 * math.cos(math.radians(pos1.latitude))
        alt_diff = pos2.altitude - pos1.altitude

        return math.sqrt(lat_diff**2 + lon_diff**2 + alt_diff**2)

    def _calculate_bearing(self, pos1: Position, pos2: Position) -> float:
        """Calculate bearing from pos1 to pos2"""
        lat1, lon1 = math.radians(pos1.latitude), math.radians(pos1.longitude)
        lat2, lon2 = math.radians(pos2.latitude), math.radians(pos2.longitude)

        d_lon = lon2 - lon1

        y = math.sin(d_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)

        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360

    def _calculate_heading(self, current: Position, target: Waypoint) -> float:
        """Calculate heading to target waypoint"""
        return self._calculate_bearing(current, target)

    def get_status(self) -> Dict[str, Any]:
        """Get current drone status"""
        return {
            "drone_id": self.drone_id,
            "status": self.status.value,
            "flight_mode": self.flight_mode.value,
            "armed": self.armed,
            "position": {
                "latitude": self.current_position.latitude,
                "longitude": self.current_position.longitude,
                "altitude": self.current_position.altitude,
                "heading": self.current_position.heading,
                "ground_speed": self.current_position.ground_speed
            },
            "battery": {
                "level": self.battery.level,
                "voltage": self.battery.voltage,
                "temperature": self.battery.temperature,
                "time_remaining": self.battery.time_remaining
            },
            "mission": {
                "current_mission_id": self.current_mission.id if self.current_mission else None,
                "progress": self.mission_progress,
                "current_waypoint": self.current_waypoint_index + 1,
                "total_waypoints": len(self.mission_waypoints)
            } if self.current_mission else None
        }


class DroneSwarmSimulator:
    """
    Manages multiple drone simulators for swarm testing
    """

    def __init__(self):
        self.drones: Dict[str, DroneSimulator] = {}
        self.active_missions: Dict[str, Mission] = {}

    def add_drone(self, drone_id: str, position: Tuple[float, float, float] = None) -> DroneSimulator:
        """Add a drone to the swarm"""
        if position is None:
            # Spread drones around a central location
            base_lat, base_lon = 40.7128, -74.0060
            offset = len(self.drones) * 0.001
            position = (base_lat + offset, base_lon + offset, 0.0)

        drone = DroneSimulator(drone_id, position)
        self.drones[drone_id] = drone
        return drone

    def get_drone(self, drone_id: str) -> Optional[DroneSimulator]:
        """Get drone by ID"""
        return self.drones.get(drone_id)

    def get_all_drones_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all drones"""
        return {drone_id: drone.get_status() for drone_id, drone in self.drones.items()}

    async def start_swarm(self):
        """Start all drone simulators"""
        await asyncio.gather(*[drone.start() for drone in self.drones.values()])

    async def stop_swarm(self):
        """Stop all drone simulators"""
        await asyncio.gather(*[drone.stop() for drone in self.drones.values()])