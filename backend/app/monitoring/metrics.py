"""
Comprehensive Monitoring and Metrics Collection
Production-grade observability for SAR Drone System

Also provides a lightweight Prometheus metrics surface with minimal counters/gauges
used by the API endpoint. These are optional and safely no-op if prometheus_client
is not installed.
"""
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        Info,
        start_http_server,
        REGISTRY,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    from prometheus_client.core import CollectorRegistry
    PROM_AVAILABLE = True
except Exception:  # pragma: no cover - allow running without prometheus
    Counter = Histogram = Gauge = Summary = Info = None  # type: ignore
    start_http_server = None  # type: ignore
    CollectorRegistry = object  # type: ignore
    REGISTRY = None  # type: ignore
    generate_latest = None  # type: ignore
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"  # type: ignore
    PROM_AVAILABLE = False
import psutil
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    network_io: Dict[str, int] = field(default_factory=dict)
    load_average: List[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    active_connections: int = 0
    active_missions: int = 0
    active_drones: int = 0
    total_discoveries: int = 0
    api_requests_total: int = 0
    api_errors_total: int = 0
    avg_response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DroneMetrics:
    """Drone-specific metrics"""
    drone_id: str
    battery_level: float
    signal_strength: float
    altitude: float
    speed: float
    distance_from_base: float
    mission_id: Optional[str] = None
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    status: str = "unknown"

class MetricsCollector:
    """Comprehensive metrics collection system"""
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.registry = CollectorRegistry() if PROM_AVAILABLE else CollectorRegistry
        self._setup_prometheus_metrics()
        self._system_metrics = SystemMetrics()
        self._app_metrics = ApplicationMetrics()
        self._drone_metrics: Dict[str, DroneMetrics] = {}
        self._collection_active = False
        
    def _setup_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        if not PROM_AVAILABLE:
            return
        
        # System metrics
        self.cpu_usage = Gauge('system_cpu_percent', 'CPU usage percentage', registry=self.registry)
        self.memory_usage = Gauge('system_memory_percent', 'Memory usage percentage', registry=self.registry)
        self.disk_usage = Gauge('system_disk_percent', 'Disk usage percentage', registry=self.registry)
        self.load_average = Gauge('system_load_average', 'System load average', registry=self.registry)
        
        # Network metrics
        self.network_bytes_sent = Counter('system_network_bytes_sent_total', 'Total network bytes sent', registry=self.registry)
        self.network_bytes_recv = Counter('system_network_bytes_recv_total', 'Total network bytes received', registry=self.registry)
        
        # Application metrics
        self.active_connections = Gauge('app_active_connections', 'Active WebSocket connections', registry=self.registry)
        self.active_missions = Gauge('app_active_missions', 'Active missions', registry=self.registry)
        self.active_drones = Gauge('app_active_drones', 'Active drones', registry=self.registry)
        self.total_discoveries = Counter('app_discoveries_total', 'Total discoveries made', registry=self.registry)
        
        # API metrics
        self.api_requests_total = Counter('app_http_requests_total', 'Total HTTP requests', 
                                        ['method', 'endpoint', 'status'], registry=self.registry)
        self.api_request_duration = Histogram('app_http_request_duration_seconds', 'HTTP request duration',
                                            ['method', 'endpoint'], registry=self.registry)
        self.api_errors_total = Counter('app_http_errors_total', 'Total HTTP errors',
                                      ['method', 'endpoint', 'error_type'], registry=self.registry)
        
        # Drone metrics
        self.drone_battery = Gauge('drone_battery_level', 'Drone battery level percentage',
                                 ['drone_id', 'mission_id'], registry=self.registry)
        self.drone_signal = Gauge('drone_signal_strength', 'Drone signal strength percentage',
                                ['drone_id', 'mission_id'], registry=self.registry)
        self.drone_altitude = Gauge('drone_altitude_meters', 'Drone altitude in meters',
                                  ['drone_id', 'mission_id'], registry=self.registry)
        self.drone_speed = Gauge('drone_speed_ms', 'Drone speed in m/s',
                               ['drone_id', 'mission_id'], registry=self.registry)
        self.drone_distance = Gauge('drone_distance_from_base_meters', 'Distance from base in meters',
                                  ['drone_id', 'mission_id'], registry=self.registry)
        self.drone_connection_status = Gauge('drone_connection_status', 'Drone connection status (1=connected, 0=disconnected)',
                                           ['drone_id'], registry=self.registry)
        
        # Mission metrics
        self.mission_duration = Histogram('mission_duration_seconds', 'Mission duration in seconds',
                                        ['mission_type', 'terrain_type'], registry=self.registry)
        self.mission_coverage = Gauge('mission_coverage_percent', 'Mission coverage percentage',
                                    ['mission_id'], registry=self.registry)
        self.mission_efficiency = Gauge('mission_efficiency_score', 'Mission efficiency score',
                                      ['mission_id'], registry=self.registry)
        
        # AI/ML metrics
        self.ai_inference_time = Histogram('ai_inference_duration_seconds', 'AI inference time',
                                         ['model_type', 'input_type'], registry=self.registry)
        self.ai_accuracy = Gauge('ai_detection_accuracy', 'AI detection accuracy',
                               ['model_type', 'object_type'], registry=self.registry)
        self.ai_confidence = Histogram('ai_detection_confidence', 'AI detection confidence',
                                     ['model_type', 'object_type'], registry=self.registry)
        
        # Database metrics
        self.db_connections = Gauge('database_connections_active', 'Active database connections', registry=self.registry)
        self.db_query_duration = Histogram('database_query_duration_seconds', 'Database query duration',
                                         ['query_type'], registry=self.registry)
        self.db_errors_total = Counter('database_errors_total', 'Total database errors',
                                     ['error_type'], registry=self.registry)
        
        # Cache metrics
        self.cache_hits = Counter('cache_hits_total', 'Total cache hits', ['cache_type'], registry=self.registry)
        self.cache_misses = Counter('cache_misses_total', 'Total cache misses', ['cache_type'], registry=self.registry)
        self.cache_size = Gauge('cache_size_bytes', 'Cache size in bytes', ['cache_type'], registry=self.registry)
        
        # Custom business metrics
        self.sar_success_rate = Gauge('sar_mission_success_rate', 'SAR mission success rate', registry=self.registry)
        self.survivor_detection_rate = Counter('survivor_detections_total', 'Total survivor detections',
                                             ['confidence_level'], registry=self.registry)
        self.emergency_events = Counter('emergency_events_total', 'Total emergency events',
                                      ['event_type', 'severity'], registry=self.registry)
    
    async def start_collection(self):
        """Start metrics collection"""
        if self._collection_active:
            return
            
        self._collection_active = True
        logger.info(f"Starting metrics collection on port {self.port}")
        
        # Start Prometheus HTTP server
        if PROM_AVAILABLE and start_http_server is not None:
            start_http_server(self.port, registry=self.registry)
        
        # Start background collection tasks
        asyncio.create_task(self._collect_system_metrics())
        asyncio.create_task(self._collect_application_metrics())
        asyncio.create_task(self._collect_drone_metrics())
        
        logger.info("Metrics collection started")
    
    async def stop_collection(self):
        """Stop metrics collection"""
        self._collection_active = False
        logger.info("Metrics collection stopped")
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        while self._collection_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_usage.set(memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.disk_usage.set(disk_percent)
                
                # Load average (Unix systems)
                if hasattr(psutil, 'getloadavg'):
                    load_avg = psutil.getloadavg()[0]
                    self.load_average.set(load_avg)
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.network_bytes_sent._value._value = net_io.bytes_sent
                self.network_bytes_recv._value._value = net_io.bytes_recv
                
                # Update internal metrics
                self._system_metrics = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_percent=disk_percent,
                    network_io={'sent': net_io.bytes_sent, 'recv': net_io.bytes_recv},
                    load_average=list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [],
                    timestamp=datetime.utcnow()
                )
                
                await asyncio.sleep(10)  # Collect every 10 seconds
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        while self._collection_active:
            try:
                # These would be populated from actual application state
                # For now, we'll use placeholder values
                
                self.active_connections.set(self._app_metrics.active_connections)
                self.active_missions.set(self._app_metrics.active_missions)
                self.active_drones.set(self._app_metrics.active_drones)
                
                await asyncio.sleep(5)  # Collect every 5 seconds
                
            except Exception as e:
                logger.error(f"Error collecting application metrics: {e}")
                await asyncio.sleep(15)
    
    async def _collect_drone_metrics(self):
        """Collect drone-specific metrics"""
        while self._collection_active:
            try:
                current_time = datetime.utcnow()
                
                for drone_id, drone_metrics in self._drone_metrics.items():
                    # Check if drone is still connected (heartbeat within last 30 seconds)
                    time_since_heartbeat = (current_time - drone_metrics.last_heartbeat).total_seconds()
                    is_connected = time_since_heartbeat < 30
                    
                    # Update connection status
                    self.drone_connection_status.labels(drone_id=drone_id).set(1 if is_connected else 0)
                    
                    if is_connected:
                        # Update drone metrics
                        self.drone_battery.labels(
                            drone_id=drone_id,
                            mission_id=drone_metrics.mission_id or 'none'
                        ).set(drone_metrics.battery_level)
                        
                        self.drone_signal.labels(
                            drone_id=drone_id,
                            mission_id=drone_metrics.mission_id or 'none'
                        ).set(drone_metrics.signal_strength)
                        
                        self.drone_altitude.labels(
                            drone_id=drone_id,
                            mission_id=drone_metrics.mission_id or 'none'
                        ).set(drone_metrics.altitude)
                        
                        self.drone_speed.labels(
                            drone_id=drone_id,
                            mission_id=drone_metrics.mission_id or 'none'
                        ).set(drone_metrics.speed)
                        
                        self.drone_distance.labels(
                            drone_id=drone_id,
                            mission_id=drone_metrics.mission_id or 'none'
                        ).set(drone_metrics.distance_from_base)
                
                await asyncio.sleep(2)  # Collect every 2 seconds
                
            except Exception as e:
                logger.error(f"Error collecting drone metrics: {e}")
                await asyncio.sleep(10)
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics"""
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if status_code >= 400:
            error_type = 'client_error' if status_code < 500 else 'server_error'
            self.api_errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type=error_type
            ).inc()
    
    def record_ai_inference(self, model_type: str, input_type: str, duration: float, 
                           accuracy: Optional[float] = None, confidence: Optional[float] = None):
        """Record AI/ML inference metrics"""
        self.ai_inference_time.labels(
            model_type=model_type,
            input_type=input_type
        ).observe(duration)
        
        if accuracy is not None:
            self.ai_accuracy.labels(
                model_type=model_type,
                object_type=input_type
            ).set(accuracy)
        
        if confidence is not None:
            self.ai_confidence.labels(
                model_type=model_type,
                object_type=input_type
            ).observe(confidence)
    
    def record_discovery(self, discovery_type: str, confidence: float):
        """Record discovery metrics"""
        self.total_discoveries.inc()
        
        # Record confidence distribution
        self.ai_confidence.labels(
            model_type='yolo',
            object_type=discovery_type
        ).observe(confidence)
        
        # Record survivor detections separately
        if discovery_type == 'person' and confidence > 0.7:
            confidence_level = 'high' if confidence > 0.9 else 'medium'
            self.survivor_detection_rate.labels(confidence_level=confidence_level).inc()
    
    def record_mission_metrics(self, mission_id: str, mission_type: str, terrain_type: str,
                              duration: float, coverage: float, efficiency: float):
        """Record mission metrics"""
        self.mission_duration.labels(
            mission_type=mission_type,
            terrain_type=terrain_type
        ).observe(duration)
        
        self.mission_coverage.labels(mission_id=mission_id).set(coverage)
        self.mission_efficiency.labels(mission_id=mission_id).set(efficiency)
    
    def update_drone_metrics(self, drone_id: str, metrics: DroneMetrics):
        """Update drone metrics"""
        self._drone_metrics[drone_id] = metrics
    
    def update_application_metrics(self, active_connections: int, active_missions: int, 
                                  active_drones: int):
        """Update application state metrics"""
        self._app_metrics.active_connections = active_connections
        self._app_metrics.active_missions = active_missions
        self._app_metrics.active_drones = active_drones
        self._app_metrics.timestamp = datetime.utcnow()
    
    def record_emergency_event(self, event_type: str, severity: str):
        """Record emergency events"""
        self.emergency_events.labels(
            event_type=event_type,
            severity=severity
        ).inc()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        return {
            "system": {
                "cpu_percent": self._system_metrics.cpu_percent,
                "memory_percent": self._system_metrics.memory_percent,
                "disk_percent": self._system_metrics.disk_percent,
                "timestamp": self._system_metrics.timestamp.isoformat()
            },
            "application": {
                "active_connections": self._app_metrics.active_connections,
                "active_missions": self._app_metrics.active_missions,
                "active_drones": self._app_metrics.active_drones,
                "timestamp": self._app_metrics.timestamp.isoformat()
            },
            "drones": {
                drone_id: {
                    "battery_level": metrics.battery_level,
                    "signal_strength": metrics.signal_strength,
                    "altitude": metrics.altitude,
                    "speed": metrics.speed,
                    "status": metrics.status,
                    "last_heartbeat": metrics.last_heartbeat.isoformat()
                }
                for drone_id, metrics in self._drone_metrics.items()
            }
        }

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Context manager for request timing
@asynccontextmanager
async def time_request(method: str, endpoint: str):
    """Context manager for timing API requests"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        # This would be called with actual status code in the actual request handler
        # metrics_collector.record_api_request(method, endpoint, status_code, duration)

# -------------------- Lightweight metrics for API exposure --------------------
# Minimal set requested by Phase 5: drones_online_total, missions_active_total,
# telemetry_updates_total. These use the default registry and are safe if the
# prometheus_client library is missing.

if PROM_AVAILABLE:
    drones_online_total = Gauge("drones_online_total", "Number of online drones")
    missions_active_total = Gauge("missions_active_total", "Number of active missions")
    telemetry_updates_total = Counter("telemetry_updates_total", "Total telemetry updates received")
else:
    drones_online_total = missions_active_total = telemetry_updates_total = None  # type: ignore


def set_drones_online(count: int) -> None:
    if PROM_AVAILABLE and drones_online_total is not None:
        try:
            drones_online_total.set(max(0, int(count)))
        except Exception:
            pass


def set_missions_active(count: int) -> None:
    if PROM_AVAILABLE and missions_active_total is not None:
        try:
            missions_active_total.set(max(0, int(count)))
        except Exception:
            pass


def inc_telemetry_updates(amount: int = 1) -> None:
    if PROM_AVAILABLE and telemetry_updates_total is not None:
        try:
            telemetry_updates_total.inc(amount if amount > 0 else 1)
        except Exception:
            pass


def export_prometheus_text() -> tuple[bytes, str]:
    """Export metrics in Prometheus text format (bytes, content_type)."""
    if PROM_AVAILABLE and generate_latest is not None and REGISTRY is not None:
        try:
            return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
        except Exception:
            return b"", CONTENT_TYPE_LATEST
    # If prometheus not available, return empty payload
    return b"", CONTENT_TYPE_LATEST
