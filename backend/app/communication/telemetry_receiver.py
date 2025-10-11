"""
Telemetry Receiver for SAR Drone Swarm System

This module provides a unified interface for receiving and processing
telemetry data from multiple sources (Redis, WebSocket, MAVLink).
It aggregates telemetry streams and distributes them to subscribers.

Author: SAR Drone Swarm System
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, List, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import deque

from .pi_communication import PiCommunicationHub, PiTelemetry, REDIS_AVAILABLE

logger = logging.getLogger(__name__)


class TelemetrySource(Enum):
    """Sources of telemetry data"""
    RASPBERRY_PI = "raspberry_pi"
    MAVLINK = "mavlink"
    WEBSOCKET = "websocket"
    SIMULATION = "simulation"


@dataclass
class AggregatedTelemetry:
    """
    Aggregated telemetry from multiple sources.
    Combines data from various sources into a unified format.
    """
    drone_id: str
    timestamp: datetime
    source: TelemetrySource
    
    # Position data
    position: Dict[str, float]  # lat, lon, alt
    heading: float
    ground_speed: float
    vertical_speed: float
    
    # Status data
    battery_voltage: float
    battery_remaining: float
    signal_strength: float
    
    # Mission data
    mission_status: str
    current_waypoint: Optional[int] = None
    waypoints_remaining: int = 0
    
    # Detection data
    recent_detections: List[Dict] = field(default_factory=list)
    detection_count: int = 0
    
    # System health
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    temperature: Optional[float] = None
    disk_usage: Optional[float] = None
    
    # Communication metrics
    packet_loss: float = 0.0
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = {
            'drone_id': self.drone_id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value,
            'position': self.position,
            'heading': self.heading,
            'ground_speed': self.ground_speed,
            'vertical_speed': self.vertical_speed,
            'battery_voltage': self.battery_voltage,
            'battery_remaining': self.battery_remaining,
            'signal_strength': self.signal_strength,
            'mission_status': self.mission_status,
            'current_waypoint': self.current_waypoint,
            'waypoints_remaining': self.waypoints_remaining,
            'recent_detections': self.recent_detections,
            'detection_count': self.detection_count,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'temperature': self.temperature,
            'disk_usage': self.disk_usage,
            'packet_loss': self.packet_loss,
            'latency_ms': self.latency_ms
        }
        return data


@dataclass
class TelemetryStatistics:
    """Statistics for telemetry reception"""
    drone_id: str
    messages_received: int = 0
    last_received: Optional[datetime] = None
    average_frequency: float = 0.0  # Hz
    packet_loss_rate: float = 0.0
    average_latency: float = 0.0  # ms
    uptime_percentage: float = 0.0


class TelemetryReceiver:
    """
    Unified telemetry receiver that aggregates data from multiple sources.
    
    Features:
        - Multi-source aggregation (Redis, MAVLink, WebSocket, simulation)
        - Data validation and sanitization
        - Buffering and rate limiting
        - Statistics tracking
        - Callback notification system
        - Historical data retention
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        history_size: int = 100,
        min_update_interval: float = 0.1  # seconds
    ):
        """
        Initialize telemetry receiver.
        
        Args:
            redis_url: Redis connection URL
            history_size: Number of telemetry messages to keep in history
            min_update_interval: Minimum time between telemetry updates (rate limiting)
        """
        self.redis_url = redis_url
        self.history_size = history_size
        self.min_update_interval = min_update_interval
        
        self.pi_comm_hub: Optional[PiCommunicationHub] = None
        self._running = False
        
        # Data storage
        self._latest_telemetry: Dict[str, AggregatedTelemetry] = {}
        self._telemetry_history: Dict[str, deque] = {}
        self._statistics: Dict[str, TelemetryStatistics] = {}
        self._last_update_time: Dict[str, datetime] = {}
        
        # Subscribers
        self._telemetry_subscribers: Set[Callable] = set()
        self._drone_specific_subscribers: Dict[str, Set[Callable]] = {}
        
        # Tasks
        self._tasks: List[asyncio.Task] = []
    
    async def start(self) -> bool:
        """
        Start the telemetry receiver.
        
        Returns:
            True if started successfully
        """
        try:
            logger.info("Starting Telemetry Receiver")
            
            # Start Pi communication hub if Redis is available
            if REDIS_AVAILABLE:
                try:
                    self.pi_comm_hub = PiCommunicationHub(self.redis_url)
                    if await self.pi_comm_hub.start():
                        # Subscribe to all telemetry
                        await self.pi_comm_hub.subscribe_all_telemetry()
                        
                        # Register callback
                        self.pi_comm_hub.register_telemetry_callback(self._handle_pi_telemetry)
                        
                        logger.info("Pi communication hub started")
                    else:
                        logger.warning("Failed to start Pi communication hub, continuing without Redis")
                        self.pi_comm_hub = None
                except Exception as e:
                    logger.warning(f"Redis not available: {e}. Telemetry receiver running in limited mode.")
                    self.pi_comm_hub = None
            else:
                logger.warning("Redis not available. Telemetry receiver running in limited mode.")
            
            self._running = True
            
            # Start background tasks
            self._tasks.append(asyncio.create_task(self._statistics_updater()))
            self._tasks.append(asyncio.create_task(self._stale_data_checker()))
            
            logger.info("Telemetry Receiver started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Telemetry Receiver: {e}", exc_info=True)
            return False
    
    async def stop(self) -> None:
        """Stop the telemetry receiver."""
        logger.info("Stopping Telemetry Receiver")
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Stop Pi communication hub
        if self.pi_comm_hub:
            await self.pi_comm_hub.stop()
        
        logger.info("Telemetry Receiver stopped")
    
    async def _handle_pi_telemetry(self, telemetry: PiTelemetry) -> None:
        """Handle telemetry from Raspberry Pi."""
        try:
            # Rate limiting
            drone_id = telemetry.drone_id
            last_update = self._last_update_time.get(drone_id)
            
            if last_update:
                time_since_update = (datetime.now() - last_update).total_seconds()
                if time_since_update < self.min_update_interval:
                    return  # Skip update to avoid flooding
            
            # Convert to aggregated format
            aggregated = AggregatedTelemetry(
                drone_id=drone_id,
                timestamp=telemetry.timestamp,
                source=TelemetrySource.RASPBERRY_PI,
                position=telemetry.position,
                heading=telemetry.position.get('heading', 0.0),
                ground_speed=telemetry.position.get('speed', 0.0),
                vertical_speed=telemetry.position.get('vertical_speed', 0.0),
                battery_voltage=telemetry.battery * 100.0,  # Convert to voltage estimate
                battery_remaining=telemetry.battery,
                signal_strength=telemetry.signal_strength,
                mission_status=telemetry.mission_status,
                current_waypoint=telemetry.current_waypoint,
                recent_detections=telemetry.detections[-10:] if telemetry.detections else [],
                detection_count=len(telemetry.detections),
                cpu_usage=telemetry.system_health.get('cpu_usage'),
                memory_usage=telemetry.system_health.get('memory_usage'),
                temperature=telemetry.system_health.get('temperature'),
                disk_usage=telemetry.system_health.get('disk_usage')
            )
            
            # Store telemetry
            await self._store_telemetry(aggregated)
            
            # Update statistics
            await self._update_statistics(drone_id)
            
            # Notify subscribers
            await self._notify_subscribers(aggregated)
            
            # Update last update time
            self._last_update_time[drone_id] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error handling Pi telemetry: {e}", exc_info=True)
    
    async def _store_telemetry(self, telemetry: AggregatedTelemetry) -> None:
        """Store telemetry data."""
        drone_id = telemetry.drone_id
        
        # Update latest
        self._latest_telemetry[drone_id] = telemetry
        
        # Update history
        if drone_id not in self._telemetry_history:
            self._telemetry_history[drone_id] = deque(maxlen=self.history_size)
        
        self._telemetry_history[drone_id].append(telemetry)
        
        logger.debug(f"Stored telemetry for {drone_id}")
    
    async def _update_statistics(self, drone_id: str) -> None:
        """Update statistics for a drone."""
        if drone_id not in self._statistics:
            self._statistics[drone_id] = TelemetryStatistics(drone_id=drone_id)
        
        stats = self._statistics[drone_id]
        stats.messages_received += 1
        stats.last_received = datetime.now()
        
        # Calculate average frequency
        history = self._telemetry_history.get(drone_id, deque())
        if len(history) >= 2:
            time_span = (history[-1].timestamp - history[0].timestamp).total_seconds()
            if time_span > 0:
                stats.average_frequency = len(history) / time_span
    
    async def _notify_subscribers(self, telemetry: AggregatedTelemetry) -> None:
        """Notify all subscribers of new telemetry."""
        # Global subscribers
        for subscriber in self._telemetry_subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(telemetry)
                else:
                    subscriber(telemetry)
            except Exception as e:
                logger.error(f"Error in telemetry subscriber: {e}")
        
        # Drone-specific subscribers
        drone_subscribers = self._drone_specific_subscribers.get(telemetry.drone_id, set())
        for subscriber in drone_subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(telemetry)
                else:
                    subscriber(telemetry)
            except Exception as e:
                logger.error(f"Error in drone-specific subscriber: {e}")
    
    async def _statistics_updater(self) -> None:
        """Periodically update statistics."""
        while self._running:
            try:
                await asyncio.sleep(10.0)  # Update every 10 seconds
                
                # Update uptime percentages
                for drone_id, stats in self._statistics.items():
                    if stats.last_received:
                        time_since_last = (datetime.now() - stats.last_received).total_seconds()
                        # Consider drone connected if received data in last 30 seconds
                        stats.uptime_percentage = 100.0 if time_since_last < 30.0 else 0.0
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
    
    async def _stale_data_checker(self) -> None:
        """Check for stale telemetry data."""
        while self._running:
            try:
                await asyncio.sleep(30.0)  # Check every 30 seconds
                
                now = datetime.now()
                stale_threshold = timedelta(seconds=60)
                
                for drone_id, telemetry in list(self._latest_telemetry.items()):
                    if now - telemetry.timestamp > stale_threshold:
                        logger.warning(f"Stale telemetry data for {drone_id} (age: {now - telemetry.timestamp})")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error checking stale data: {e}")
    
    def subscribe(self, callback: Callable, drone_id: Optional[str] = None) -> None:
        """
        Subscribe to telemetry updates.
        
        Args:
            callback: Callback function (can be sync or async)
            drone_id: Specific drone ID to subscribe to, or None for all drones
        """
        if drone_id:
            if drone_id not in self._drone_specific_subscribers:
                self._drone_specific_subscribers[drone_id] = set()
            self._drone_specific_subscribers[drone_id].add(callback)
            logger.info(f"Added subscriber for drone {drone_id}")
        else:
            self._telemetry_subscribers.add(callback)
            logger.info("Added global telemetry subscriber")
    
    def unsubscribe(self, callback: Callable, drone_id: Optional[str] = None) -> None:
        """
        Unsubscribe from telemetry updates.
        
        Args:
            callback: Callback function to remove
            drone_id: Specific drone ID, or None for global subscription
        """
        if drone_id:
            if drone_id in self._drone_specific_subscribers:
                self._drone_specific_subscribers[drone_id].discard(callback)
        else:
            self._telemetry_subscribers.discard(callback)
    
    def get_latest_telemetry(self, drone_id: str) -> Optional[AggregatedTelemetry]:
        """
        Get latest telemetry for specific drone.
        
        Args:
            drone_id: Drone identifier
            
        Returns:
            Latest telemetry or None if not available
        """
        return self._latest_telemetry.get(drone_id)
    
    def get_all_latest_telemetry(self) -> Dict[str, AggregatedTelemetry]:
        """
        Get latest telemetry for all drones.
        
        Returns:
            Dictionary mapping drone IDs to latest telemetry
        """
        return self._latest_telemetry.copy()
    
    def get_telemetry_history(
        self,
        drone_id: str,
        max_count: Optional[int] = None
    ) -> List[AggregatedTelemetry]:
        """
        Get telemetry history for specific drone.
        
        Args:
            drone_id: Drone identifier
            max_count: Maximum number of records to return (newest first)
            
        Returns:
            List of telemetry records
        """
        history = self._telemetry_history.get(drone_id, deque())
        history_list = list(history)
        
        if max_count:
            history_list = history_list[-max_count:]
        
        return history_list
    
    def get_statistics(self, drone_id: str) -> Optional[TelemetryStatistics]:
        """
        Get telemetry statistics for specific drone.
        
        Args:
            drone_id: Drone identifier
            
        Returns:
            TelemetryStatistics or None if not available
        """
        return self._statistics.get(drone_id)
    
    def get_all_statistics(self) -> Dict[str, TelemetryStatistics]:
        """
        Get telemetry statistics for all drones.
        
        Returns:
            Dictionary mapping drone IDs to statistics
        """
        return self._statistics.copy()
    
    def get_connected_drones(self, timeout_seconds: int = 30) -> List[str]:
        """
        Get list of drones with recent telemetry.
        
        Args:
            timeout_seconds: Maximum age of telemetry to consider drone connected
            
        Returns:
            List of drone IDs
        """
        now = datetime.now()
        threshold = timedelta(seconds=timeout_seconds)
        
        connected = []
        for drone_id, telemetry in self._latest_telemetry.items():
            if now - telemetry.timestamp < threshold:
                connected.append(drone_id)
        
        return connected
    
    async def inject_telemetry(self, telemetry: AggregatedTelemetry) -> None:
        """
        Manually inject telemetry data (for testing/simulation).
        
        Args:
            telemetry: Telemetry data to inject
        """
        await self._store_telemetry(telemetry)
        await self._update_statistics(telemetry.drone_id)
        await self._notify_subscribers(telemetry)
        self._last_update_time[telemetry.drone_id] = datetime.now()


# Global instance
_telemetry_receiver: Optional[TelemetryReceiver] = None


async def get_telemetry_receiver(redis_url: str = "redis://localhost:6379") -> TelemetryReceiver:
    """
    Get or create global telemetry receiver.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        TelemetryReceiver instance
    """
    global _telemetry_receiver
    
    if _telemetry_receiver is None:
        _telemetry_receiver = TelemetryReceiver(redis_url)
        if not await _telemetry_receiver.start():
            logger.warning("Telemetry receiver started with limited functionality")
    
    return _telemetry_receiver

