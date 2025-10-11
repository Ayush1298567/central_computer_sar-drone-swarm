"""
Real-time Stream Processing System for SAR Operations
High-performance data pipeline with Kafka, Redis, and advanced analytics
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import aioredis
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import deque
import hashlib

logger = logging.getLogger(__name__)

class StreamType(Enum):
    TELEMETRY = "telemetry"
    VIDEO_FRAMES = "video_frames"
    DISCOVERIES = "discoveries"
    ALERTS = "alerts"
    COMMANDS = "commands"
    AI_DECISIONS = "ai_decisions"
    PERFORMANCE_METRICS = "performance_metrics"

class MessagePriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class StreamMessage:
    """Standardized stream message format"""
    message_id: str
    stream_type: StreamType
    drone_id: str
    mission_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    priority: MessagePriority = MessagePriority.MEDIUM
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "message_id": self.message_id,
            "stream_type": self.stream_type.value,
            "drone_id": self.drone_id,
            "mission_id": self.mission_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamMessage':
        """Create from dictionary"""
        return cls(
            message_id=data["message_id"],
            stream_type=StreamType(data["stream_type"]),
            drone_id=data["drone_id"],
            mission_id=data.get("mission_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            priority=MessagePriority(data.get("priority", 3)),
            correlation_id=data.get("correlation_id")
        )

class SARStreamProcessor:
    """High-performance real-time stream processing for SAR operations"""
    
    def __init__(self, kafka_bootstrap_servers: str = "localhost:9092"):
        self.kafka_servers = kafka_bootstrap_servers
        self.producer = None
        self.consumers = {}
        self.redis_client = None
        self.processing_tasks = {}
        self.is_running = False
        
        # Analytics components
        self.telemetry_buffer = {}  # Drone ID -> deque of recent telemetry
        self.anomaly_detectors = {}
        self.performance_monitors = {}
        
        # Initialize components
        asyncio.create_task(self._initialize_components())
    
    async def _initialize_components(self):
        """Initialize Kafka and Redis connections with production settings"""
        try:
            # Initialize Kafka producer with high-throughput configuration
            self.producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=5,
                retry_backoff_ms=100,
                batch_size=32768,  # 32KB batches
                linger_ms=5,  # Wait up to 5ms to batch messages
                compression_type='gzip',
                max_in_flight_requests_per_connection=5,
                request_timeout_ms=30000,
                delivery_timeout_ms=120000
            )
            
            # Initialize Redis for caching and session storage
            self.redis_client = aioredis.from_url(
                "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            
            # Initialize stream consumers
            await self._initialize_consumers()
            
            logger.info("Stream processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize stream processor: {e}")
            raise
    
    async def _initialize_consumers(self):
        """Initialize Kafka consumers for different stream types with optimized settings"""
        consumer_config = {
            'bootstrap_servers': self.kafka_servers,
            'value_deserializer': lambda m: json.loads(m.decode('utf-8')),
            'key_deserializer': lambda k: k.decode('utf-8') if k else None,
            'auto_offset_reset': 'latest',
            'enable_auto_commit': True,
            'group_id': 'sar_processor_group',
            'max_poll_records': 500,  # Process up to 500 messages at once
            'fetch_max_wait_ms': 100,  # Wait up to 100ms for new messages
            'fetch_min_bytes': 1024,  # Wait for at least 1KB of data
            'session_timeout_ms': 30000,
            'heartbeat_interval_ms': 10000
        }
        
        # Create consumers for different stream types
        for stream_type in StreamType:
            topic_name = f"sar_{stream_type.value}"
            consumer = KafkaConsumer(topic_name, **consumer_config)
            self.consumers[stream_type] = consumer
            
            # Start processing task for this consumer
            task = asyncio.create_task(self._process_stream(stream_type, consumer))
            self.processing_tasks[stream_type] = task
        
        logger.info(f"Initialized {len(self.consumers)} stream consumers")
    
    async def publish_message(self, message: StreamMessage) -> bool:
        """Publish message to appropriate Kafka topic with error handling"""
        try:
            topic_name = f"sar_{message.stream_type.value}"
            
            # Prepare message data
            message_data = message.to_dict()
            
            # Publish to Kafka with timeout
            future = self.producer.send(
                topic_name,
                key=message.drone_id,
                value=message_data,
                timestamp_ms=int(message.timestamp.timestamp() * 1000)
            )
            
            # Wait for confirmation with timeout
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Published {message.stream_type.value} message for drone {message.drone_id}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to publish message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")
            return False
    
    async def _process_stream(self, stream_type: StreamType, consumer):
        """Process messages from a specific stream type with batching"""
        logger.info(f"Starting stream processor for {stream_type.value}")
        
        try:
            while True:
                # Poll for messages in batches
                message_batch = consumer.poll(timeout_ms=100, max_records=100)
                
                if message_batch:
                    # Process batch of messages
                    for topic_partition, messages in message_batch.items():
                        await self._process_message_batch(stream_type, messages)
                    
                    # Commit offsets after processing
                    consumer.commit()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.001)
                
        except Exception as e:
            logger.error(f"Stream processing error for {stream_type.value}: {e}")
    
    async def _process_message_batch(self, stream_type: StreamType, messages: List):
        """Process a batch of messages efficiently"""
        try:
            # Convert messages to StreamMessage objects
            stream_messages = []
            for message in messages:
                try:
                    stream_msg = StreamMessage.from_dict(message.value)
                    stream_messages.append(stream_msg)
                except Exception as e:
                    logger.error(f"Failed to parse message: {e}")
                    continue
            
            # Process messages in parallel
            if stream_messages:
                tasks = [self._handle_stream_message(stream_type, msg) for msg in stream_messages]
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
    
    async def _handle_stream_message(self, stream_type: StreamType, message: StreamMessage):
        """Handle individual stream message with comprehensive processing"""
        try:
            # Route to appropriate processor based on stream type
            if stream_type == StreamType.TELEMETRY:
                await self._process_telemetry_data(message)
            elif stream_type == StreamType.VIDEO_FRAMES:
                await self._process_video_frame(message)
            elif stream_type == StreamType.DISCOVERIES:
                await self._process_discovery(message)
            elif stream_type == StreamType.ALERTS:
                await self._process_alert(message)
            elif stream_type == StreamType.COMMANDS:
                await self._process_command(message)
            elif stream_type == StreamType.AI_DECISIONS:
                await self._process_ai_decision(message)
            elif stream_type == StreamType.PERFORMANCE_METRICS:
                await self._process_performance_metrics(message)
            
        except Exception as e:
            logger.error(f"Error handling {stream_type.value} message: {e}")
    
    async def _process_telemetry_data(self, message: StreamMessage):
        """Process telemetry data with real-time analytics and anomaly detection"""
        try:
            drone_id = message.drone_id
            telemetry_data = message.data
            
            # Store in time-series buffer for analytics
            if drone_id not in self.telemetry_buffer:
                self.telemetry_buffer[drone_id] = deque(maxlen=1000)  # Keep last 1000 readings
            
            self.telemetry_buffer[drone_id].append({
                "timestamp": message.timestamp,
                "data": telemetry_data
            })
            
            # Store in time-series database
            await self._store_telemetry_data(drone_id, message.mission_id, telemetry_data, message.timestamp)
            
            # Perform real-time analysis
            analysis_results = await self._analyze_telemetry_realtime(drone_id, telemetry_data, message.timestamp)
            
            # Check for anomalies
            if analysis_results.get("anomaly_detected", False):
                await self._handle_telemetry_anomaly(drone_id, message.mission_id, analysis_results, message.timestamp)
            
            # Update drone status in cache
            await self._update_drone_status_cache(drone_id, telemetry_data, message.timestamp)
            
            # Generate alerts if needed
            await self._check_telemetry_alerts(drone_id, telemetry_data, message.timestamp)
            
            # Update performance metrics
            await self._update_performance_metrics(drone_id, telemetry_data, message.timestamp)
            
        except Exception as e:
            logger.error(f"Telemetry processing error: {e}")
    
    async def _process_video_frame(self, message: StreamMessage):
        """Process video frames with computer vision analysis"""
        try:
            drone_id = message.drone_id
            frame_data = message.data
            
            # Process frame with computer vision
            from ..ml.computer_vision import sar_cv
            
            # Convert frame data to numpy array (assuming base64 encoded)
            import base64
            frame_bytes = base64.b64decode(frame_data.get("frame_data", ""))
            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
            
            if frame is not None:
                # Analyze frame
                analysis = await sar_cv.analyze_frame(frame, frame_data.get("metadata", {}))
                
                # Store analysis results
                await self._store_frame_analysis(drone_id, message.mission_id, analysis)
                
                # Check for critical detections
                critical_detections = [d for d in analysis.detections if d.priority.value == "critical"]
                if critical_detections:
                    await self._handle_critical_detection(drone_id, message.mission_id, critical_detections, analysis)
                
                # Update discovery tracking
                await self._update_discovery_tracking(drone_id, message.mission_id, analysis.detections)
            
        except Exception as e:
            logger.error(f"Video frame processing error: {e}")
    
    async def _process_discovery(self, message: StreamMessage):
        """Process discovery notifications with priority handling"""
        try:
            drone_id = message.drone_id
            discovery_data = message.data
            
            # Store discovery in database
            await self._store_discovery(drone_id, message.mission_id, discovery_data, message.timestamp)
            
            # Determine priority and routing
            priority = discovery_data.get("priority", "medium")
            
            if priority == "critical":
                # Immediate notification for critical discoveries
                await self._send_critical_notification(discovery_data)
            
            # Update mission progress
            await self._update_mission_progress(message.mission_id, discovery_data)
            
            # Generate AI analysis of discovery
            await self._analyze_discovery_with_ai(drone_id, message.mission_id, discovery_data)
            
        except Exception as e:
            logger.error(f"Discovery processing error: {e}")
    
    async def _process_alert(self, message: StreamMessage):
        """Process system alerts with escalation handling"""
        try:
            alert_data = message.data
            alert_type = alert_data.get("alert_type", "unknown")
            severity = alert_data.get("severity", "medium")
            
            # Store alert in database
            await self._store_alert(alert_data, message.timestamp)
            
            # Route based on severity
            if severity == "critical":
                await self._handle_critical_alert(alert_data, message.timestamp)
            elif severity == "high":
                await self._handle_high_priority_alert(alert_data, message.timestamp)
            else:
                await self._handle_standard_alert(alert_data, message.timestamp)
            
            # Update system metrics
            await self._update_alert_metrics(alert_type, severity)
            
        except Exception as e:
            logger.error(f"Alert processing error: {e}")
    
    async def _process_command(self, message: StreamMessage):
        """Process drone commands with validation and routing"""
        try:
            drone_id = message.drone_id
            command_data = message.data
            
            # Validate command
            validation_result = await self._validate_command(drone_id, command_data)
            
            if validation_result["valid"]:
                # Route command to appropriate drone
                await self._route_command_to_drone(drone_id, command_data)
                
                # Log command execution
                await self._log_command_execution(drone_id, command_data, message.timestamp)
            else:
                # Handle invalid command
                await self._handle_invalid_command(drone_id, command_data, validation_result["errors"])
            
        except Exception as e:
            logger.error(f"Command processing error: {e}")
    
    async def _process_ai_decision(self, message: StreamMessage):
        """Process AI decisions with logging and validation"""
        try:
            decision_data = message.data
            
            # Store decision in knowledge base
            await self._store_ai_decision(decision_data, message.timestamp)
            
            # Validate decision quality
            quality_score = await self._assess_decision_quality(decision_data)
            
            # Update AI performance metrics
            await self._update_ai_performance_metrics(decision_data, quality_score)
            
            # Trigger learning if decision quality is low
            if quality_score < 0.5:
                await self._trigger_ai_learning(decision_data)
            
        except Exception as e:
            logger.error(f"AI decision processing error: {e}")
    
    async def _process_performance_metrics(self, message: StreamMessage):
        """Process performance metrics with trend analysis"""
        try:
            metrics_data = message.data
            
            # Store metrics in time-series database
            await self._store_performance_metrics(metrics_data, message.timestamp)
            
            # Analyze trends
            trend_analysis = await self._analyze_performance_trends(metrics_data)
            
            # Update dashboards and alerts
            await self._update_performance_dashboards(metrics_data, trend_analysis)
            
            # Check for performance degradation
            if trend_analysis.get("degradation_detected", False):
                await self._handle_performance_degradation(metrics_data, trend_analysis)
            
        except Exception as e:
            logger.error(f"Performance metrics processing error: {e}")
    
    async def _analyze_telemetry_realtime(self, drone_id: str, data: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
        """Real-time telemetry analysis with anomaly detection"""
        try:
            analysis_results = {
                "anomaly_detected": False,
                "anomaly_type": None,
                "anomaly_score": 0.0,
                "performance_metrics": {},
                "recommendations": []
            }
            
            # Battery analysis
            battery_level = data.get("battery_level", 0)
            if battery_level < 20:
                analysis_results["anomaly_detected"] = True
                analysis_results["anomaly_type"] = "low_battery"
                analysis_results["anomaly_score"] = (20 - battery_level) / 20
                analysis_results["recommendations"].append("Return to base immediately")
            
            # GPS analysis
            gps_fix_type = data.get("gps_fix_type", 0)
            if gps_fix_type < 2:
                analysis_results["anomaly_detected"] = True
                analysis_results["anomaly_type"] = "gps_degradation"
                analysis_results["anomaly_score"] = 0.8
                analysis_results["recommendations"].append("GPS signal degraded - switch to manual control")
            
            # Signal strength analysis
            signal_strength = data.get("signal_strength", 100)
            if signal_strength < 30:
                analysis_results["anomaly_detected"] = True
                analysis_results["anomaly_type"] = "communication_loss"
                analysis_results["anomaly_score"] = (30 - signal_strength) / 30
                analysis_results["recommendations"].append("Communication signal weak - prepare for loss")
            
            # Performance metrics
            analysis_results["performance_metrics"] = {
                "battery_efficiency": self._calculate_battery_efficiency(drone_id, data),
                "flight_stability": self._calculate_flight_stability(drone_id, data),
                "communication_quality": signal_strength / 100.0
            }
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Telemetry analysis error: {e}")
            return {"anomaly_detected": False}
    
    def _calculate_battery_efficiency(self, drone_id: str, data: Dict[str, Any]) -> float:
        """Calculate battery efficiency based on current and historical data"""
        try:
            if drone_id not in self.telemetry_buffer or len(self.telemetry_buffer[drone_id]) < 10:
                return 1.0  # Default efficiency
            
            # Get recent telemetry data
            recent_data = list(self.telemetry_buffer[drone_id])[-10:]
            
            # Calculate battery consumption rate
            battery_levels = [entry["data"].get("battery_level", 100) for entry in recent_data]
            if len(battery_levels) > 1:
                consumption_rate = (battery_levels[0] - battery_levels[-1]) / len(battery_levels)
                expected_consumption = 2.0  # Expected consumption per reading
                
                efficiency = max(0.0, min(1.0, expected_consumption / max(consumption_rate, 0.1)))
                return efficiency
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Battery efficiency calculation error: {e}")
            return 1.0
    
    def _calculate_flight_stability(self, drone_id: str, data: Dict[str, Any]) -> float:
        """Calculate flight stability based on attitude and acceleration data"""
        try:
            if drone_id not in self.telemetry_buffer or len(self.telemetry_buffer[drone_id]) < 5:
                return 1.0  # Default stability
            
            # Get recent telemetry data
            recent_data = list(self.telemetry_buffer[drone_id])[-5:]
            
            # Calculate attitude variance
            roll_values = []
            pitch_values = []
            for entry in recent_data:
                attitude = entry["data"].get("attitude", {})
                roll_values.append(attitude.get("roll", 0))
                pitch_values.append(attitude.get("pitch", 0))
            
            if len(roll_values) > 1:
                roll_variance = np.var(roll_values)
                pitch_variance = np.var(pitch_values)
                
                # Convert variance to stability score (lower variance = higher stability)
                stability = max(0.0, min(1.0, 1.0 - (roll_variance + pitch_variance) / 100.0))
                return stability
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Flight stability calculation error: {e}")
            return 1.0
    
    async def _store_telemetry_data(self, drone_id: str, mission_id: str, data: Dict[str, Any], timestamp: datetime):
        """Store telemetry data in time-series database"""
        try:
            # This would integrate with TimescaleDB
            # For now, store in Redis as a cache
            cache_key = f"telemetry:{drone_id}:{timestamp.isoformat()}"
            await self.redis_client.setex(cache_key, 3600, json.dumps(data, default=str))
            
        except Exception as e:
            logger.error(f"Failed to store telemetry data: {e}")
    
    async def _update_drone_status_cache(self, drone_id: str, data: Dict[str, Any], timestamp: datetime):
        """Update drone status in Redis cache"""
        try:
            status_key = f"drone_status:{drone_id}"
            status_data = {
                "last_update": timestamp.isoformat(),
                "battery_level": data.get("battery_level", 0),
                "position": data.get("position", {}),
                "status": data.get("flight_mode", "unknown"),
                "signal_strength": data.get("signal_strength", 0)
            }
            
            await self.redis_client.setex(status_key, 300, json.dumps(status_data))  # 5 minute TTL
            
        except Exception as e:
            logger.error(f"Failed to update drone status cache: {e}")
    
    async def _check_telemetry_alerts(self, drone_id: str, data: Dict[str, Any], timestamp: datetime):
        """Check telemetry data for alert conditions"""
        try:
            alerts = []
            
            # Battery alerts
            battery_level = data.get("battery_level", 100)
            if battery_level < 15:
                alerts.append({
                    "type": "critical_battery",
                    "message": f"Critical battery level: {battery_level}%",
                    "drone_id": drone_id,
                    "priority": "critical"
                })
            elif battery_level < 25:
                alerts.append({
                    "type": "low_battery",
                    "message": f"Low battery level: {battery_level}%",
                    "drone_id": drone_id,
                    "priority": "high"
                })
            
            # GPS alerts
            gps_fix_type = data.get("gps_fix_type", 3)
            if gps_fix_type < 2:
                alerts.append({
                    "type": "gps_degradation",
                    "message": f"GPS signal degraded (fix type: {gps_fix_type})",
                    "drone_id": drone_id,
                    "priority": "high"
                })
            
            # Communication alerts
            signal_strength = data.get("signal_strength", 100)
            if signal_strength < 20:
                alerts.append({
                    "type": "communication_loss",
                    "message": f"Communication signal very weak: {signal_strength}%",
                    "drone_id": drone_id,
                    "priority": "critical"
                })
            
            # Send alerts
            for alert in alerts:
                alert_message = StreamMessage(
                    message_id=str(uuid.uuid4()),
                    stream_type=StreamType.ALERTS,
                    drone_id=drone_id,
                    mission_id=None,
                    timestamp=timestamp,
                    data=alert,
                    priority=MessagePriority.CRITICAL if alert["priority"] == "critical" else MessagePriority.HIGH
                )
                await self.publish_message(alert_message)
            
        except Exception as e:
            logger.error(f"Telemetry alert check error: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                "stream_processor": {
                    "running": self.is_running,
                    "consumers": len(self.consumers),
                    "processing_tasks": len(self.processing_tasks)
                },
                "kafka": {
                    "connected": self.producer is not None,
                    "servers": self.kafka_servers
                },
                "redis": {
                    "connected": self.redis_client is not None
                },
                "analytics": {
                    "active_drones": len(self.telemetry_buffer),
                    "total_messages_processed": sum(len(buffer) for buffer in self.telemetry_buffer.values())
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}
    
    async def shutdown(self):
        """Graceful shutdown of stream processor"""
        try:
            self.is_running = False
            
            # Cancel processing tasks
            for task in self.processing_tasks.values():
                task.cancel()
            
            # Close Kafka producer
            if self.producer:
                self.producer.close()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Stream processor shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

# Global stream processor instance
stream_processor = SARStreamProcessor()
