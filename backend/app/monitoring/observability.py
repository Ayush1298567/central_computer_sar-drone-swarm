"""
Production Monitoring and Observability System
Comprehensive monitoring, logging, and alerting for SAR operations
"""
import asyncio
import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
import structlog
from collections import defaultdict, deque
import traceback
import sys

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Alert:
    """Alert definition"""
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: str
    threshold: float
    evaluation_interval: int  # seconds
    cooldown_period: int  # seconds
    is_enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

@dataclass
class MetricData:
    """Metric data point"""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: datetime
    metric_type: MetricType

@dataclass
class SystemHealth:
    """System health status"""
    component: str
    status: str  # healthy, degraded, unhealthy
    metrics: Dict[str, float]
    last_check: datetime
    issues: List[str]

class PrometheusMetrics:
    """Prometheus metrics collector"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics = {}
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize all Prometheus metrics"""
        try:
            # API Metrics
            self.metrics['api_requests_total'] = Counter(
                'sar_api_requests_total',
                'Total number of API requests',
                ['method', 'endpoint', 'status_code'],
                registry=self.registry
            )
            
            self.metrics['api_request_duration'] = Histogram(
                'sar_api_request_duration_seconds',
                'API request duration in seconds',
                ['method', 'endpoint'],
                registry=self.registry
            )
            
            # Mission Metrics
            self.metrics['missions_active'] = Gauge(
                'sar_missions_active',
                'Number of active missions',
                registry=self.registry
            )
            
            self.metrics['missions_completed_total'] = Counter(
                'sar_missions_completed_total',
                'Total number of completed missions',
                ['status'],
                registry=self.registry
            )
            
            self.metrics['mission_duration'] = Histogram(
                'sar_mission_duration_minutes',
                'Mission duration in minutes',
                ['mission_type'],
                registry=self.registry
            )
            
            # Drone Metrics
            self.metrics['drones_online'] = Gauge(
                'sar_drones_online',
                'Number of online drones',
                registry=self.registry
            )
            
            self.metrics['drone_battery_level'] = Gauge(
                'sar_drone_battery_level_percent',
                'Drone battery level percentage',
                ['drone_id'],
                registry=self.registry
            )
            
            self.metrics['drone_signal_strength'] = Gauge(
                'sar_drone_signal_strength_percent',
                'Drone signal strength percentage',
                ['drone_id'],
                registry=self.registry
            )
            
            # AI Metrics
            self.metrics['ai_decisions_total'] = Counter(
                'sar_ai_decisions_total',
                'Total number of AI decisions',
                ['decision_type', 'confidence_level'],
                registry=self.registry
            )
            
            self.metrics['ai_decision_accuracy'] = Gauge(
                'sar_ai_decision_accuracy',
                'AI decision accuracy score',
                ['decision_type'],
                registry=self.registry
            )
            
            self.metrics['ai_inference_duration'] = Histogram(
                'sar_ai_inference_duration_seconds',
                'AI model inference duration',
                ['model_type'],
                registry=self.registry
            )
            
            # Computer Vision Metrics
            self.metrics['cv_frames_processed_total'] = Counter(
                'sar_cv_frames_processed_total',
                'Total number of frames processed',
                ['drone_id'],
                registry=self.registry
            )
            
            self.metrics['cv_detections_total'] = Counter(
                'sar_cv_detections_total',
                'Total number of object detections',
                ['detection_type', 'confidence_level'],
                registry=self.registry
            )
            
            self.metrics['cv_processing_duration'] = Histogram(
                'sar_cv_processing_duration_seconds',
                'Computer vision processing duration',
                ['processing_type'],
                registry=self.registry
            )
            
            # Database Metrics
            self.metrics['db_connections_active'] = Gauge(
                'sar_db_connections_active',
                'Number of active database connections',
                ['database_type'],
                registry=self.registry
            )
            
            self.metrics['db_query_duration'] = Histogram(
                'sar_db_query_duration_seconds',
                'Database query duration',
                ['query_type', 'database_type'],
                registry=self.registry
            )
            
            self.metrics['db_errors_total'] = Counter(
                'sar_db_errors_total',
                'Total number of database errors',
                ['error_type', 'database_type'],
                registry=self.registry
            )
            
            # Stream Processing Metrics
            self.metrics['kafka_messages_processed_total'] = Counter(
                'sar_kafka_messages_processed_total',
                'Total number of Kafka messages processed',
                ['topic', 'status'],
                registry=self.registry
            )
            
            self.metrics['kafka_lag'] = Gauge(
                'sar_kafka_consumer_lag',
                'Kafka consumer lag',
                ['topic', 'partition'],
                registry=self.registry
            )
            
            # System Metrics
            self.metrics['system_cpu_usage'] = Gauge(
                'sar_system_cpu_usage_percent',
                'System CPU usage percentage',
                registry=self.registry
            )
            
            self.metrics['system_memory_usage'] = Gauge(
                'sar_system_memory_usage_percent',
                'System memory usage percentage',
                registry=self.registry
            )
            
            self.metrics['system_disk_usage'] = Gauge(
                'sar_system_disk_usage_percent',
                'System disk usage percentage',
                ['mount_point'],
                registry=self.registry
            )
            
            logger.info("Prometheus metrics initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus metrics: {e}")
    
    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record API request metrics"""
        try:
            self.metrics['api_requests_total'].labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            self.metrics['api_request_duration'].labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record API request metrics: {e}")
    
    def update_mission_metrics(self, active_count: int, completed_status: str = None):
        """Update mission-related metrics"""
        try:
            self.metrics['missions_active'].set(active_count)
            
            if completed_status:
                self.metrics['missions_completed_total'].labels(
                    status=completed_status
                ).inc()
                
        except Exception as e:
            logger.error(f"Failed to update mission metrics: {e}")
    
    def update_drone_metrics(self, drone_id: str, battery_level: float, signal_strength: float):
        """Update drone-related metrics"""
        try:
            self.metrics['drone_battery_level'].labels(drone_id=drone_id).set(battery_level)
            self.metrics['drone_signal_strength'].labels(drone_id=drone_id).set(signal_strength)
            
        except Exception as e:
            logger.error(f"Failed to update drone metrics: {e}")
    
    def record_ai_decision(self, decision_type: str, confidence_level: str, duration: float, accuracy: float = None):
        """Record AI decision metrics"""
        try:
            self.metrics['ai_decisions_total'].labels(
                decision_type=decision_type,
                confidence_level=confidence_level
            ).inc()
            
            self.metrics['ai_inference_duration'].labels(
                model_type=decision_type
            ).observe(duration)
            
            if accuracy is not None:
                self.metrics['ai_decision_accuracy'].labels(
                    decision_type=decision_type
                ).set(accuracy)
                
        except Exception as e:
            logger.error(f"Failed to record AI decision metrics: {e}")
    
    def record_cv_processing(self, drone_id: str, detection_type: str, confidence_level: str, duration: float):
        """Record computer vision processing metrics"""
        try:
            self.metrics['cv_frames_processed_total'].labels(drone_id=drone_id).inc()
            
            if detection_type and confidence_level:
                self.metrics['cv_detections_total'].labels(
                    detection_type=detection_type,
                    confidence_level=confidence_level
                ).inc()
            
            self.metrics['cv_processing_duration'].labels(
                processing_type="frame_analysis"
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record CV processing metrics: {e}")
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['system_cpu_usage'].set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['system_memory_usage'].set(memory.percent)
            
            # Disk usage
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self.metrics['system_disk_usage'].labels(
                        mount_point=partition.mountpoint
                    ).set(usage.percent)
                except PermissionError:
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")

class StructuredLogger:
    """Enhanced structured logging with correlation IDs"""
    
    def __init__(self):
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger()
        self.correlation_ids = {}
    
    def get_logger(self, component: str, correlation_id: str = None):
        """Get logger with component and correlation ID"""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        return self.logger.bind(
            component=component,
            correlation_id=correlation_id
        )
    
    def log_api_request(self, method: str, endpoint: str, user_id: str = None, **kwargs):
        """Log API request with structured data"""
        self.logger.info(
            "API request",
            method=method,
            endpoint=endpoint,
            user_id=user_id,
            **kwargs
        )
    
    def log_mission_event(self, mission_id: str, event_type: str, **kwargs):
        """Log mission-related event"""
        self.logger.info(
            "Mission event",
            mission_id=mission_id,
            event_type=event_type,
            **kwargs
        )
    
    def log_drone_event(self, drone_id: str, event_type: str, **kwargs):
        """Log drone-related event"""
        self.logger.info(
            "Drone event",
            drone_id=drone_id,
            event_type=event_type,
            **kwargs
        )
    
    def log_ai_decision(self, decision_id: str, decision_type: str, **kwargs):
        """Log AI decision with full context"""
        self.logger.info(
            "AI decision",
            decision_id=decision_id,
            decision_type=decision_type,
            **kwargs
        )
    
    def log_error(self, error_type: str, component: str, **kwargs):
        """Log error with full context"""
        self.logger.error(
            "System error",
            error_type=error_type,
            component=component,
            **kwargs
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        self.logger.info(
            "Performance metric",
            operation=operation,
            duration_seconds=duration,
            **kwargs
        )

class AlertManager:
    """Advanced alert management system"""
    
    def __init__(self):
        self.alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_callbacks = {}
        self.metric_buffer = defaultdict(lambda: deque(maxlen=100))
        
        # Initialize default alerts
        self._initialize_default_alerts()
    
    def _initialize_default_alerts(self):
        """Initialize default system alerts"""
        try:
            default_alerts = [
                Alert(
                    alert_id="high_cpu_usage",
                    name="High CPU Usage",
                    description="System CPU usage is above 80%",
                    severity=AlertSeverity.HIGH,
                    condition="cpu_usage > 80",
                    threshold=80.0,
                    evaluation_interval=30,
                    cooldown_period=300
                ),
                Alert(
                    alert_id="high_memory_usage",
                    name="High Memory Usage",
                    description="System memory usage is above 85%",
                    severity=AlertSeverity.HIGH,
                    condition="memory_usage > 85",
                    threshold=85.0,
                    evaluation_interval=30,
                    cooldown_period=300
                ),
                Alert(
                    alert_id="low_battery",
                    name="Low Battery",
                    description="Drone battery level is below 20%",
                    severity=AlertSeverity.CRITICAL,
                    condition="battery_level < 20",
                    threshold=20.0,
                    evaluation_interval=10,
                    cooldown_period=60
                ),
                Alert(
                    alert_id="poor_signal",
                    name="Poor Signal Strength",
                    description="Drone signal strength is below 30%",
                    severity=AlertSeverity.HIGH,
                    condition="signal_strength < 30",
                    threshold=30.0,
                    evaluation_interval=15,
                    cooldown_period=120
                ),
                Alert(
                    alert_id="database_errors",
                    name="Database Errors",
                    description="High number of database errors",
                    severity=AlertSeverity.MEDIUM,
                    condition="db_errors_per_minute > 10",
                    threshold=10.0,
                    evaluation_interval=60,
                    cooldown_period=600
                ),
                Alert(
                    alert_id="ai_decision_low_confidence",
                    name="Low AI Decision Confidence",
                    description="AI decisions with very low confidence",
                    severity=AlertSeverity.MEDIUM,
                    condition="ai_confidence < 0.3",
                    threshold=0.3,
                    evaluation_interval=60,
                    cooldown_period=300
                )
            ]
            
            for alert in default_alerts:
                self.alerts[alert.alert_id] = alert
            
            logger.info(f"Initialized {len(default_alerts)} default alerts")
            
        except Exception as e:
            logger.error(f"Failed to initialize default alerts: {e}")
    
    def register_alert_callback(self, alert_id: str, callback: Callable):
        """Register callback for alert notifications"""
        self.alert_callbacks[alert_id] = callback
    
    async def evaluate_alerts(self, metrics: Dict[str, float]):
        """Evaluate all alerts against current metrics"""
        try:
            for alert_id, alert in self.alerts.items():
                if not alert.is_enabled:
                    continue
                
                # Check cooldown period
                if alert.last_triggered:
                    time_since_last = (datetime.utcnow() - alert.last_triggered).total_seconds()
                    if time_since_last < alert.cooldown_period:
                        continue
                
                # Evaluate alert condition
                if self._evaluate_condition(alert.condition, metrics):
                    await self._trigger_alert(alert, metrics)
                    
        except Exception as e:
            logger.error(f"Alert evaluation failed: {e}")
    
    def _evaluate_condition(self, condition: str, metrics: Dict[str, float]) -> bool:
        """Evaluate alert condition against metrics"""
        try:
            # Simple condition evaluation (in production, use a proper expression parser)
            if "cpu_usage" in condition:
                cpu_usage = metrics.get("cpu_usage", 0)
                if "cpu_usage > 80" in condition:
                    return cpu_usage > 80
                elif "cpu_usage > 90" in condition:
                    return cpu_usage > 90
            
            elif "memory_usage" in condition:
                memory_usage = metrics.get("memory_usage", 0)
                if "memory_usage > 85" in condition:
                    return memory_usage > 85
                elif "memory_usage > 95" in condition:
                    return memory_usage > 95
            
            elif "battery_level" in condition:
                battery_level = metrics.get("battery_level", 100)
                if "battery_level < 20" in condition:
                    return battery_level < 20
                elif "battery_level < 10" in condition:
                    return battery_level < 10
            
            elif "signal_strength" in condition:
                signal_strength = metrics.get("signal_strength", 100)
                if "signal_strength < 30" in condition:
                    return signal_strength < 30
                elif "signal_strength < 20" in condition:
                    return signal_strength < 20
            
            return False
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    async def _trigger_alert(self, alert: Alert, metrics: Dict[str, float]):
        """Trigger alert notification"""
        try:
            alert.last_triggered = datetime.utcnow()
            alert.trigger_count += 1
            
            alert_data = {
                "alert_id": alert.alert_id,
                "name": alert.name,
                "description": alert.description,
                "severity": alert.severity.value,
                "triggered_at": alert.last_triggered.isoformat(),
                "trigger_count": alert.trigger_count,
                "current_metrics": metrics,
                "condition": alert.condition
            }
            
            # Add to alert history
            self.alert_history.append(alert_data)
            
            # Call registered callbacks
            if alert.alert_id in self.alert_callbacks:
                await self.alert_callbacks[alert.alert_id](alert_data)
            
            # Log alert
            logger.warning(f"Alert triggered: {alert.name}", **alert_data)
            
        except Exception as e:
            logger.error(f"Failed to trigger alert {alert.alert_id}: {e}")
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        return list(self.alert_history)[-limit:]

class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.health_checks = {}
        self.health_status = {}
        self._initialize_health_checks()
    
    def _initialize_health_checks(self):
        """Initialize health check functions"""
        self.health_checks = {
            "database": self._check_database_health,
            "redis": self._check_redis_health,
            "kafka": self._check_kafka_health,
            "ai_models": self._check_ai_models_health,
            "computer_vision": self._check_cv_health,
            "stream_processing": self._check_stream_processing_health,
            "api": self._check_api_health
        }
    
    async def check_all_health(self) -> Dict[str, SystemHealth]:
        """Check health of all system components"""
        try:
            health_results = {}
            
            for component, check_func in self.health_checks.items():
                try:
                    health_status = await check_func()
                    health_results[component] = health_status
                    self.health_status[component] = health_status
                except Exception as e:
                    health_results[component] = SystemHealth(
                        component=component,
                        status="unhealthy",
                        metrics={},
                        last_check=datetime.utcnow(),
                        issues=[f"Health check failed: {str(e)}"]
                    )
            
            return health_results
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {}
    
    async def _check_database_health(self) -> SystemHealth:
        """Check database connectivity and performance"""
        try:
            # This would integrate with actual database connections
            issues = []
            metrics = {}
            
            # Simulate database check
            connection_time = 0.05  # Simulated
            metrics["connection_time"] = connection_time
            metrics["active_connections"] = 5  # Simulated
            
            if connection_time > 0.1:
                issues.append("Slow database connection")
            
            status = "healthy" if not issues else "degraded"
            
            return SystemHealth(
                component="database",
                status=status,
                metrics=metrics,
                last_check=datetime.utcnow(),
                issues=issues
            )
            
        except Exception as e:
            return SystemHealth(
                component="database",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                issues=[f"Database health check failed: {str(e)}"]
            )
    
    async def _check_redis_health(self) -> SystemHealth:
        """Check Redis connectivity and performance"""
        try:
            issues = []
            metrics = {}
            
            # Simulate Redis check
            ping_time = 0.01  # Simulated
            metrics["ping_time"] = ping_time
            metrics["memory_usage"] = 45.2  # Simulated percentage
            
            if ping_time > 0.05:
                issues.append("Slow Redis response")
            
            if metrics["memory_usage"] > 80:
                issues.append("High Redis memory usage")
            
            status = "healthy" if not issues else "degraded"
            
            return SystemHealth(
                component="redis",
                status=status,
                metrics=metrics,
                last_check=datetime.utcnow(),
                issues=issues
            )
            
        except Exception as e:
            return SystemHealth(
                component="redis",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                issues=[f"Redis health check failed: {str(e)}"]
            )
    
    async def _check_kafka_health(self) -> SystemHealth:
        """Check Kafka connectivity and performance"""
        try:
            issues = []
            metrics = {}
            
            # Simulate Kafka check
            metrics["consumer_lag"] = 10  # Simulated
            metrics["producer_latency"] = 15  # Simulated milliseconds
            
            if metrics["consumer_lag"] > 100:
                issues.append("High Kafka consumer lag")
            
            if metrics["producer_latency"] > 100:
                issues.append("High Kafka producer latency")
            
            status = "healthy" if not issues else "degraded"
            
            return SystemHealth(
                component="kafka",
                status=status,
                metrics=metrics,
                last_check=datetime.utcnow(),
                issues=issues
            )
            
        except Exception as e:
            return SystemHealth(
                component="kafka",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                issues=[f"Kafka health check failed: {str(e)}"]
            )
    
    async def _check_ai_models_health(self) -> SystemHealth:
        """Check AI models availability and performance"""
        try:
            issues = []
            metrics = {}
            
            # Simulate AI model check
            metrics["models_loaded"] = 5  # Simulated
            metrics["average_inference_time"] = 0.15  # Simulated seconds
            metrics["model_accuracy"] = 0.87  # Simulated accuracy
            
            if metrics["average_inference_time"] > 1.0:
                issues.append("Slow AI model inference")
            
            if metrics["model_accuracy"] < 0.8:
                issues.append("Low AI model accuracy")
            
            status = "healthy" if not issues else "degraded"
            
            return SystemHealth(
                component="ai_models",
                status=status,
                metrics=metrics,
                last_check=datetime.utcnow(),
                issues=issues
            )
            
        except Exception as e:
            return SystemHealth(
                component="ai_models",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                issues=[f"AI models health check failed: {str(e)}"]
            )
    
    async def _check_cv_health(self) -> SystemHealth:
        """Check computer vision system health"""
        try:
            issues = []
            metrics = {}
            
            # Simulate CV system check
            metrics["frames_processed_per_second"] = 15.5  # Simulated
            metrics["detection_accuracy"] = 0.92  # Simulated
            metrics["processing_latency"] = 0.08  # Simulated seconds
            
            if metrics["frames_processed_per_second"] < 10:
                issues.append("Low CV processing throughput")
            
            if metrics["detection_accuracy"] < 0.85:
                issues.append("Low CV detection accuracy")
            
            status = "healthy" if not issues else "degraded"
            
            return SystemHealth(
                component="computer_vision",
                status=status,
                metrics=metrics,
                last_check=datetime.utcnow(),
                issues=issues
            )
            
        except Exception as e:
            return SystemHealth(
                component="computer_vision",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                issues=[f"Computer vision health check failed: {str(e)}"]
            )
    
    async def _check_stream_processing_health(self) -> SystemHealth:
        """Check stream processing health"""
        try:
            issues = []
            metrics = {}
            
            # Simulate stream processing check
            metrics["messages_processed_per_second"] = 150.0  # Simulated
            metrics["processing_latency"] = 0.05  # Simulated seconds
            metrics["error_rate"] = 0.001  # Simulated error rate
            
            if metrics["processing_latency"] > 0.2:
                issues.append("High stream processing latency")
            
            if metrics["error_rate"] > 0.01:
                issues.append("High stream processing error rate")
            
            status = "healthy" if not issues else "degraded"
            
            return SystemHealth(
                component="stream_processing",
                status=status,
                metrics=metrics,
                last_check=datetime.utcnow(),
                issues=issues
            )
            
        except Exception as e:
            return SystemHealth(
                component="stream_processing",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                issues=[f"Stream processing health check failed: {str(e)}"]
            )
    
    async def _check_api_health(self) -> SystemHealth:
        """Check API health"""
        try:
            issues = []
            metrics = {}
            
            # Simulate API check
            metrics["response_time"] = 0.12  # Simulated seconds
            metrics["requests_per_second"] = 45.0  # Simulated
            metrics["error_rate"] = 0.005  # Simulated error rate
            
            if metrics["response_time"] > 0.5:
                issues.append("Slow API response time")
            
            if metrics["error_rate"] > 0.02:
                issues.append("High API error rate")
            
            status = "healthy" if not issues else "degraded"
            
            return SystemHealth(
                component="api",
                status=status,
                metrics=metrics,
                last_check=datetime.utcnow(),
                issues=issues
            )
            
        except Exception as e:
            return SystemHealth(
                component="api",
                status="unhealthy",
                metrics={},
                last_check=datetime.utcnow(),
                issues=[f"API health check failed: {str(e)}"]
            )

class ObservabilitySystem:
    """Main observability system coordinating all monitoring components"""
    
    def __init__(self, prometheus_port: int = 8001):
        self.prometheus_port = prometheus_port
        self.metrics = PrometheusMetrics()
        self.logger = StructuredLogger()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        
        self.is_running = False
        self.monitoring_tasks = []
        
        # Start Prometheus server
        try:
            start_http_server(self.prometheus_port, registry=self.metrics.registry)
            logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")
    
    async def start_monitoring(self):
        """Start all monitoring tasks"""
        try:
            self.is_running = True
            
            # Start monitoring tasks
            self.monitoring_tasks = [
                asyncio.create_task(self._system_metrics_loop()),
                asyncio.create_task(self._health_check_loop()),
                asyncio.create_task(self._alert_evaluation_loop())
            ]
            
            logger.info("Observability system started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        try:
            self.is_running = False
            
            # Cancel all monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()
            
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            
            logger.info("Observability system stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
    
    async def _system_metrics_loop(self):
        """Continuously update system metrics"""
        while self.is_running:
            try:
                self.metrics.update_system_metrics()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"System metrics update failed: {e}")
                await asyncio.sleep(30)
    
    async def _health_check_loop(self):
        """Continuously check system health"""
        while self.is_running:
            try:
                health_results = await self.health_checker.check_all_health()
                
                # Log health status
                for component, health in health_results.items():
                    if health.status != "healthy":
                        self.logger.log_error(
                            "health_check",
                            component,
                            status=health.status,
                            issues=health.issues,
                            metrics=health.metrics
                        )
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                await asyncio.sleep(60)
    
    async def _alert_evaluation_loop(self):
        """Continuously evaluate alerts"""
        while self.is_running:
            try:
                # Get current system metrics
                current_metrics = {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "battery_level": 85.0,  # Would get from actual drone data
                    "signal_strength": 75.0,  # Would get from actual drone data
                    "db_errors_per_minute": 2.0,  # Would get from actual database
                    "ai_confidence": 0.85  # Would get from actual AI decisions
                }
                
                await self.alert_manager.evaluate_alerts(current_metrics)
                await asyncio.sleep(30)  # Evaluate every 30 seconds
            except Exception as e:
                logger.error(f"Alert evaluation failed: {e}")
                await asyncio.sleep(30)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            return {
                "observability_system": {
                    "running": self.is_running,
                    "prometheus_port": self.prometheus_port,
                    "monitoring_tasks": len(self.monitoring_tasks)
                },
                "health_status": {comp: asdict(health) for comp, health in self.health_checker.health_status.items()},
                "alert_summary": {
                    "total_alerts": len(self.alert_manager.alerts),
                    "enabled_alerts": sum(1 for alert in self.alert_manager.alerts.values() if alert.is_enabled),
                    "recent_alerts": len(self.alert_manager.get_alert_history(10))
                },
                "metrics_status": {
                    "total_metrics": len(self.metrics.metrics),
                    "prometheus_server": "running"
                }
            }
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

# Global observability system instance
observability_system = ObservabilitySystem()
