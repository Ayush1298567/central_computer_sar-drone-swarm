"""
Real-time Data Processing Pipeline for SAR Mission Commander
High-performance streaming data processing for mission-critical operations
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import queue

from ..utils.logging import get_logger

logger = get_logger(__name__)

class DataType(Enum):
    TELEMETRY = "telemetry"
    VIDEO_FRAME = "video_frame"
    SENSOR_DATA = "sensor_data"
    AI_INFERENCE = "ai_inference"
    DISCOVERY = "discovery"
    MISSION_UPDATE = "mission_update"
    EMERGENCY = "emergency"
    PERFORMANCE_METRIC = "performance_metric"

class ProcessingPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DataPacket:
    """Data packet for processing pipeline"""
    packet_id: str
    data_type: DataType
    priority: ProcessingPriority
    timestamp: datetime
    source_id: str  # drone_id, sensor_id, etc.
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class ProcessingStage:
    """Processing stage configuration"""
    stage_id: str
    stage_name: str
    processor_func: Callable
    input_types: List[DataType]
    output_types: List[DataType]
    priority: ProcessingPriority
    max_concurrent: int = 5
    timeout_seconds: int = 30
    retry_on_failure: bool = True
    enabled: bool = True

@dataclass
class PipelineMetrics:
    """Pipeline performance metrics"""
    total_packets_processed: int
    total_processing_time_ms: float
    average_processing_time_ms: float
    packets_per_second: float
    error_rate: float
    queue_depth: int
    active_processors: int
    memory_usage_mb: float
    last_updated: datetime

class RealTimePipeline:
    """Real-time data processing pipeline"""
    
    def __init__(self):
        self.processing_stages = {}
        self.data_queues = {}
        self.processing_workers = {}
        self.pipeline_metrics = PipelineMetrics(
            total_packets_processed=0,
            total_processing_time_ms=0.0,
            average_processing_time_ms=0.0,
            packets_per_second=0.0,
            error_rate=0.0,
            queue_depth=0,
            active_processors=0,
            memory_usage_mb=0.0,
            last_updated=datetime.now()
        )
        
        # Pipeline configuration
        self.max_queue_size = 10000
        self.processing_timeout = 30
        self.metrics_update_interval = 5  # seconds
        
        # Thread pool for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        
        # Pipeline state
        self.pipeline_active = False
        self.processing_tasks = []
        self.metrics_task = None
        
        # Data packet tracking
        self.packet_counter = 0
        self.processed_packets = deque(maxlen=1000)  # Keep last 1000 processed packets
        self.failed_packets = deque(maxlen=100)      # Keep last 100 failed packets
        
        # Performance tracking
        self.processing_times = deque(maxlen=1000)
        self.throughput_history = deque(maxlen=100)
        
        # Initialize default processing stages
        self._initialize_default_stages()
    
    def _initialize_default_stages(self):
        """Initialize default processing stages"""
        
        # Telemetry processing stage
        self.add_processing_stage(
            stage_id="telemetry_processor",
            stage_name="Telemetry Processor",
            processor_func=self._process_telemetry_data,
            input_types=[DataType.TELEMETRY],
            output_types=[DataType.MISSION_UPDATE],
            priority=ProcessingPriority.HIGH,
            max_concurrent=10
        )
        
        # Video processing stage
        self.add_processing_stage(
            stage_id="video_processor",
            stage_name="Video Frame Processor",
            processor_func=self._process_video_frame,
            input_types=[DataType.VIDEO_FRAME],
            output_types=[DataType.AI_INFERENCE, DataType.DISCOVERY],
            priority=ProcessingPriority.HIGH,
            max_concurrent=5
        )
        
        # AI inference stage
        self.add_processing_stage(
            stage_id="ai_processor",
            stage_name="AI Inference Processor",
            processor_func=self._process_ai_inference,
            input_types=[DataType.AI_INFERENCE],
            output_types=[DataType.DISCOVERY],
            priority=ProcessingPriority.CRITICAL,
            max_concurrent=3
        )
        
        # Emergency processing stage
        self.add_processing_stage(
            stage_id="emergency_processor",
            stage_name="Emergency Response Processor",
            processor_func=self._process_emergency_data,
            input_types=[DataType.EMERGENCY],
            output_types=[DataType.MISSION_UPDATE],
            priority=ProcessingPriority.CRITICAL,
            max_concurrent=5
        )
        
        # Performance monitoring stage
        self.add_processing_stage(
            stage_id="performance_processor",
            stage_name="Performance Monitoring Processor",
            processor_func=self._process_performance_metrics,
            input_types=[DataType.PERFORMANCE_METRIC],
            output_types=[DataType.MISSION_UPDATE],
            priority=ProcessingPriority.LOW,
            max_concurrent=3
        )
    
    def add_processing_stage(self, stage_id: str, stage_name: str, processor_func: Callable,
                           input_types: List[DataType], output_types: List[DataType],
                           priority: ProcessingPriority = ProcessingPriority.MEDIUM,
                           max_concurrent: int = 5, timeout_seconds: int = 30,
                           retry_on_failure: bool = True, enabled: bool = True):
        """Add a processing stage to the pipeline"""
        try:
            stage = ProcessingStage(
                stage_id=stage_id,
                stage_name=stage_name,
                processor_func=processor_func,
                input_types=input_types,
                output_types=output_types,
                priority=priority,
                max_concurrent=max_concurrent,
                timeout_seconds=timeout_seconds,
                retry_on_failure=retry_on_failure,
                enabled=enabled
            )
            
            self.processing_stages[stage_id] = stage
            
            # Initialize queue for this stage
            self.data_queues[stage_id] = asyncio.Queue(maxsize=self.max_queue_size)
            
            logger.info(f"Added processing stage: {stage_name} (ID: {stage_id})")
            
        except Exception as e:
            logger.error(f"Error adding processing stage {stage_id}: {e}")
    
    async def start_pipeline(self):
        """Start the real-time processing pipeline"""
        try:
            if self.pipeline_active:
                logger.warning("Pipeline is already active")
                return
            
            self.pipeline_active = True
            
            # Start processing workers for each stage
            for stage_id, stage in self.processing_stages.items():
                if stage.enabled:
                    # Start workers for this stage
                    for worker_id in range(stage.max_concurrent):
                        task = asyncio.create_task(
                            self._processing_worker(stage_id, worker_id)
                        )
                        self.processing_tasks.append(task)
            
            # Start metrics collection task
            self.metrics_task = asyncio.create_task(self._metrics_collector())
            
            logger.info(f"Started real-time pipeline with {len(self.processing_tasks)} workers")
            
        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")
            self.pipeline_active = False
    
    async def stop_pipeline(self):
        """Stop the real-time processing pipeline"""
        try:
            self.pipeline_active = False
            
            # Cancel all processing tasks
            for task in self.processing_tasks:
                task.cancel()
            
            # Cancel metrics task
            if self.metrics_task:
                self.metrics_task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.processing_tasks, return_exceptions=True)
            
            if self.metrics_task:
                await asyncio.gather(self.metrics_task, return_exceptions=True)
            
            self.processing_tasks = []
            self.metrics_task = None
            
            logger.info("Stopped real-time pipeline")
            
        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")
    
    async def submit_data(self, data_type: DataType, source_id: str, payload: Dict[str, Any],
                         priority: ProcessingPriority = ProcessingPriority.MEDIUM,
                         metadata: Dict[str, Any] = None) -> str:
        """Submit data to the processing pipeline"""
        try:
            # Generate packet ID
            self.packet_counter += 1
            packet_id = f"pkt_{self.packet_counter:08d}_{int(time.time())}"
            
            # Create data packet
            packet = DataPacket(
                packet_id=packet_id,
                data_type=data_type,
                priority=priority,
                timestamp=datetime.now(),
                source_id=source_id,
                payload=payload,
                metadata=metadata or {}
            )
            
            # Find appropriate processing stage
            target_stage = self._find_processing_stage(data_type)
            
            if target_stage:
                # Add to processing queue
                await self.data_queues[target_stage.stage_id].put(packet)
                logger.debug(f"Submitted packet {packet_id} to stage {target_stage.stage_id}")
                return packet_id
            else:
                logger.warning(f"No processing stage found for data type: {data_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting data: {e}")
            return None
    
    def _find_processing_stage(self, data_type: DataType) -> Optional[ProcessingStage]:
        """Find the appropriate processing stage for a data type"""
        try:
            for stage in self.processing_stages.values():
                if stage.enabled and data_type in stage.input_types:
                    return stage
            return None
            
        except Exception as e:
            logger.error(f"Error finding processing stage: {e}")
            return None
    
    async def _processing_worker(self, stage_id: str, worker_id: int):
        """Processing worker for a specific stage"""
        try:
            stage = self.processing_stages[stage_id]
            queue = self.data_queues[stage_id]
            
            logger.info(f"Started processing worker {worker_id} for stage {stage.stage_name}")
            
            while self.pipeline_active:
                try:
                    # Get packet from queue with timeout
                    packet = await asyncio.wait_for(
                        queue.get(), timeout=1.0
                    )
                    
                    if packet:
                        await self._process_packet(stage, packet, worker_id)
                        
                except asyncio.TimeoutError:
                    continue  # No packet available, continue waiting
                except Exception as e:
                    logger.error(f"Error in processing worker {worker_id}: {e}")
                    await asyncio.sleep(1)  # Brief pause before continuing
            
            logger.info(f"Stopped processing worker {worker_id} for stage {stage.stage_name}")
            
        except Exception as e:
            logger.error(f"Error in processing worker {worker_id}: {e}")
    
    async def _process_packet(self, stage: ProcessingStage, packet: DataPacket, worker_id: int):
        """Process a single data packet"""
        try:
            start_time = time.time()
            
            # Update packet status
            packet.processing_status = ProcessingStatus.PROCESSING
            packet.processing_start_time = datetime.now()
            
            # Process packet with timeout
            try:
                result = await asyncio.wait_for(
                    stage.processor_func(packet),
                    timeout=stage.timeout_seconds
                )
                
                # Update packet status
                packet.processing_status = ProcessingStatus.COMPLETED
                packet.processing_end_time = datetime.now()
                
                # Record processing time
                processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                self.processing_times.append(processing_time)
                self.processed_packets.append(packet)
                
                # Update metrics
                self.pipeline_metrics.total_packets_processed += 1
                self.pipeline_metrics.total_processing_time_ms += processing_time
                
                # Forward results to next stages if any
                if result and isinstance(result, list):
                    for output_packet in result:
                        await self._forward_packet(output_packet)
                
                logger.debug(f"Processed packet {packet.packet_id} in {processing_time:.2f}ms")
                
            except asyncio.TimeoutError:
                await self._handle_processing_timeout(stage, packet)
                
            except Exception as e:
                await self._handle_processing_error(stage, packet, e)
                
        except Exception as e:
            logger.error(f"Error processing packet {packet.packet_id}: {e}")
    
    async def _forward_packet(self, packet: DataPacket):
        """Forward processed packet to next stages"""
        try:
            # Find stages that can process this output
            for stage in self.processing_stages.values():
                if stage.enabled and packet.data_type in stage.input_types:
                    await self.data_queues[stage.stage_id].put(packet)
                    
        except Exception as e:
            logger.error(f"Error forwarding packet: {e}")
    
    async def _handle_processing_timeout(self, stage: ProcessingStage, packet: DataPacket):
        """Handle processing timeout"""
        try:
            logger.warning(f"Processing timeout for packet {packet.packet_id} in stage {stage.stage_id}")
            
            packet.processing_status = ProcessingStatus.FAILED
            packet.processing_end_time = datetime.now()
            
            if stage.retry_on_failure and packet.retry_count < packet.max_retries:
                packet.retry_count += 1
                packet.processing_status = ProcessingStatus.PENDING
                
                # Re-queue packet for retry
                await self.data_queues[stage.stage_id].put(packet)
                logger.info(f"Retrying packet {packet.packet_id} (attempt {packet.retry_count})")
            else:
                self.failed_packets.append(packet)
                
        except Exception as e:
            logger.error(f"Error handling processing timeout: {e}")
    
    async def _handle_processing_error(self, stage: ProcessingStage, packet: DataPacket, error: Exception):
        """Handle processing error"""
        try:
            logger.error(f"Processing error for packet {packet.packet_id}: {error}")
            
            packet.processing_status = ProcessingStatus.FAILED
            packet.processing_end_time = datetime.now()
            
            if stage.retry_on_failure and packet.retry_count < packet.max_retries:
                packet.retry_count += 1
                packet.processing_status = ProcessingStatus.PENDING
                
                # Re-queue packet for retry
                await self.data_queues[stage.stage_id].put(packet)
                logger.info(f"Retrying packet {packet.packet_id} after error (attempt {packet.retry_count})")
            else:
                self.failed_packets.append(packet)
                
        except Exception as e:
            logger.error(f"Error handling processing error: {e}")
    
    async def _metrics_collector(self):
        """Collect and update pipeline metrics"""
        try:
            while self.pipeline_active:
                await asyncio.sleep(self.metrics_update_interval)
                
                # Calculate current metrics
                await self._update_pipeline_metrics()
                
        except Exception as e:
            logger.error(f"Error in metrics collector: {e}")
    
    async def _update_pipeline_metrics(self):
        """Update pipeline performance metrics"""
        try:
            current_time = time.time()
            
            # Calculate average processing time
            if self.processing_times:
                self.pipeline_metrics.average_processing_time_ms = sum(self.processing_times) / len(self.processing_times)
            
            # Calculate packets per second
            if len(self.processed_packets) > 1:
                time_span = (self.processed_packets[-1].timestamp - self.processed_packets[0].timestamp).total_seconds()
                if time_span > 0:
                    self.pipeline_metrics.packets_per_second = len(self.processed_packets) / time_span
            
            # Calculate error rate
            total_packets = len(self.processed_packets) + len(self.failed_packets)
            if total_packets > 0:
                self.pipeline_metrics.error_rate = len(self.failed_packets) / total_packets
            
            # Calculate queue depth
            total_queue_depth = 0
            for queue in self.data_queues.values():
                total_queue_depth += queue.qsize()
            self.pipeline_metrics.queue_depth = total_queue_depth
            
            # Count active processors
            self.pipeline_metrics.active_processors = len([t for t in self.processing_tasks if not t.done()])
            
            # Update timestamp
            self.pipeline_metrics.last_updated = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating pipeline metrics: {e}")
    
    # Default processing functions
    async def _process_telemetry_data(self, packet: DataPacket) -> List[DataPacket]:
        """Process telemetry data"""
        try:
            telemetry = packet.payload
            
            # Process telemetry data (simplified)
            processed_data = {
                'drone_id': packet.source_id,
                'timestamp': packet.timestamp.isoformat(),
                'position': telemetry.get('position', {}),
                'battery_level': telemetry.get('battery_level', 0),
                'status': telemetry.get('status', 'unknown'),
                'processed_at': datetime.now().isoformat()
            }
            
            # Create mission update packet
            mission_update = DataPacket(
                packet_id=f"update_{packet.packet_id}",
                data_type=DataType.MISSION_UPDATE,
                priority=ProcessingPriority.MEDIUM,
                timestamp=datetime.now(),
                source_id=packet.source_id,
                payload=processed_data
            )
            
            return [mission_update]
            
        except Exception as e:
            logger.error(f"Error processing telemetry data: {e}")
            return []
    
    async def _process_video_frame(self, packet: DataPacket) -> List[DataPacket]:
        """Process video frame data"""
        try:
            frame_data = packet.payload
            
            # Process video frame (simplified)
            # In real implementation, this would run computer vision algorithms
            
            # Create AI inference packet
            ai_inference = DataPacket(
                packet_id=f"ai_{packet.packet_id}",
                data_type=DataType.AI_INFERENCE,
                priority=ProcessingPriority.HIGH,
                timestamp=datetime.now(),
                source_id=packet.source_id,
                payload={
                    'frame_id': frame_data.get('frame_id'),
                    'detections': [],  # Would contain actual detections
                    'processing_time_ms': 50.0,
                    'confidence_threshold': 0.7
                }
            )
            
            return [ai_inference]
            
        except Exception as e:
            logger.error(f"Error processing video frame: {e}")
            return []
    
    async def _process_ai_inference(self, packet: DataPacket) -> List[DataPacket]:
        """Process AI inference results"""
        try:
            inference_data = packet.payload
            
            # Process AI inference results (simplified)
            detections = inference_data.get('detections', [])
            
            results = []
            for detection in detections:
                if detection.get('confidence', 0) > 0.7:  # High confidence detection
                    discovery = DataPacket(
                        packet_id=f"disc_{packet.packet_id}_{len(results)}",
                        data_type=DataType.DISCOVERY,
                        priority=ProcessingPriority.HIGH,
                        timestamp=datetime.now(),
                        source_id=packet.source_id,
                        payload={
                            'detection': detection,
                            'inference_id': packet.packet_id,
                            'confidence': detection.get('confidence', 0)
                        }
                    )
                    results.append(discovery)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing AI inference: {e}")
            return []
    
    async def _process_emergency_data(self, packet: DataPacket) -> List[DataPacket]:
        """Process emergency data"""
        try:
            emergency_data = packet.payload
            
            # Process emergency data (simplified)
            emergency_type = emergency_data.get('type', 'unknown')
            severity = emergency_data.get('severity', 'medium')
            
            # Create mission update for emergency
            mission_update = DataPacket(
                packet_id=f"emergency_{packet.packet_id}",
                data_type=DataType.MISSION_UPDATE,
                priority=ProcessingPriority.CRITICAL,
                timestamp=datetime.now(),
                source_id=packet.source_id,
                payload={
                    'emergency_type': emergency_type,
                    'severity': severity,
                    'location': emergency_data.get('location', {}),
                    'recommended_action': emergency_data.get('recommended_action', 'investigate'),
                    'timestamp': packet.timestamp.isoformat()
                }
            )
            
            return [mission_update]
            
        except Exception as e:
            logger.error(f"Error processing emergency data: {e}")
            return []
    
    async def _process_performance_metrics(self, packet: DataPacket) -> List[DataPacket]:
        """Process performance metrics"""
        try:
            metrics_data = packet.payload
            
            # Process performance metrics (simplified)
            processed_metrics = {
                'source_id': packet.source_id,
                'metric_type': metrics_data.get('metric_type', 'unknown'),
                'value': metrics_data.get('value', 0),
                'timestamp': packet.timestamp.isoformat(),
                'processed_at': datetime.now().isoformat()
            }
            
            # Create mission update packet
            mission_update = DataPacket(
                packet_id=f"perf_{packet.packet_id}",
                data_type=DataType.MISSION_UPDATE,
                priority=ProcessingPriority.LOW,
                timestamp=datetime.now(),
                source_id=packet.source_id,
                payload=processed_metrics
            )
            
            return [mission_update]
            
        except Exception as e:
            logger.error(f"Error processing performance metrics: {e}")
            return []
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        try:
            return {
                'active': self.pipeline_active,
                'total_stages': len(self.processing_stages),
                'active_workers': len([t for t in self.processing_tasks if not t.done()]),
                'queue_depths': {stage_id: queue.qsize() for stage_id, queue in self.data_queues.items()},
                'metrics': {
                    'total_packets_processed': self.pipeline_metrics.total_packets_processed,
                    'average_processing_time_ms': self.pipeline_metrics.average_processing_time_ms,
                    'packets_per_second': self.pipeline_metrics.packets_per_second,
                    'error_rate': self.pipeline_metrics.error_rate,
                    'queue_depth': self.pipeline_metrics.queue_depth
                },
                'processed_packets_count': len(self.processed_packets),
                'failed_packets_count': len(self.failed_packets)
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {}

# Global instance
real_time_pipeline = RealTimePipeline()
