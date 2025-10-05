"""
Complete ETL Pipeline for SAR Drone System
Data extraction, transformation, and loading with ML integration
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from kafka import KafkaProducer, KafkaConsumer
import redis
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Data source configuration"""
    name: str
    type: str  # database, kafka, api, file
    config: Dict[str, Any]
    enabled: bool = True
    last_sync: Optional[datetime] = None
    sync_interval: timedelta = timedelta(minutes=5)

@dataclass
class TransformationRule:
    """Data transformation rule"""
    name: str
    source_field: str
    target_field: str
    transformation_type: str  # map, filter, aggregate, calculate
    parameters: Dict[str, Any]
    enabled: bool = True

@dataclass
class PipelineJob:
    """ETL pipeline job"""
    id: str
    name: str
    description: str
    source: DataSource
    transformations: List[TransformationRule]
    target: str
    schedule: str  # cron expression
    status: str = "idle"  # idle, running, completed, failed
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ETLPipeline:
    """Comprehensive ETL pipeline system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.jobs: Dict[str, PipelineJob] = {}
        self.data_sources: Dict[str, DataSource] = {}
        self.transformations: Dict[str, List[TransformationRule]] = {}
        
        # Initialize connections
        self._setup_connections()
        
        # Initialize default pipelines
        self._setup_default_pipelines()
        
        # Start pipeline scheduler
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def _setup_connections(self):
        """Setup database and messaging connections"""
        try:
            # Database connections
            self.db_engine = create_engine(self.config.get('database_url'))
            
            # Redis connection
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                decode_responses=True
            )
            
            # Kafka connections
            kafka_config = self.config.get('kafka', {})
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=kafka_config.get('bootstrap_servers', ['localhost:9092']),
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            self.kafka_consumer = KafkaConsumer(
                bootstrap_servers=kafka_config.get('bootstrap_servers', ['localhost:9092']),
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            logger.info("ETL pipeline connections established")
            
        except Exception as e:
            logger.error(f"Failed to setup ETL connections: {e}")
            raise
    
    def _setup_default_pipelines(self):
        """Setup default ETL pipelines"""
        
        # Telemetry data pipeline
        telemetry_source = DataSource(
            name="drone_telemetry",
            type="kafka",
            config={
                "topic": "drone_telemetry",
                "consumer_group": "etl_telemetry"
            },
            sync_interval=timedelta(seconds=30)
        )
        
        telemetry_transformations = [
            TransformationRule(
                name="clean_gps_data",
                source_field="position",
                target_field="cleaned_position",
                transformation_type="clean",
                parameters={"remove_outliers": True, "smooth_data": True}
            ),
            TransformationRule(
                name="calculate_velocity",
                source_field="position_history",
                target_field="velocity",
                transformation_type="calculate",
                parameters={"method": "derivative", "window_size": 5}
            ),
            TransformationRule(
                name="add_timestamp_index",
                source_field="timestamp",
                target_field="time_index",
                transformation_type="map",
                parameters={"format": "unix_timestamp"}
            )
        ]
        
        telemetry_job = PipelineJob(
            id=str(uuid.uuid4()),
            name="telemetry_processing",
            description="Process drone telemetry data",
            source=telemetry_source,
            transformations=telemetry_transformations,
            target="processed_telemetry",
            schedule="*/30 * * * * *"  # Every 30 seconds
        )
        
        self.add_job(telemetry_job)
        
        # Discovery data pipeline
        discovery_source = DataSource(
            name="discovery_data",
            type="kafka",
            config={
                "topic": "discoveries",
                "consumer_group": "etl_discoveries"
            },
            sync_interval=timedelta(minutes=1)
        )
        
        discovery_transformations = [
            TransformationRule(
                name="validate_confidence",
                source_field="confidence",
                target_field="validated_confidence",
                transformation_type="filter",
                parameters={"min_confidence": 0.5, "max_confidence": 1.0}
            ),
            TransformationRule(
                name="geocode_location",
                source_field="coordinates",
                target_field="geocoded_location",
                transformation_type="map",
                parameters={"service": "reverse_geocoding"}
            ),
            TransformationRule(
                name="classify_priority",
                source_field="discovery_type",
                target_field="priority_level",
                transformation_type="map",
                parameters={
                    "mapping": {
                        "person": "high",
                        "vehicle": "medium",
                        "structure": "low",
                        "debris": "low"
                    }
                }
            )
        ]
        
        discovery_job = PipelineJob(
            id=str(uuid.uuid4()),
            name="discovery_processing",
            description="Process discovery data",
            source=discovery_source,
            transformations=discovery_transformations,
            target="processed_discoveries",
            schedule="0 */1 * * * *"  # Every minute
        )
        
        self.add_job(discovery_job)
        
        # Mission analytics pipeline
        mission_source = DataSource(
            name="mission_data",
            type="database",
            config={
                "table": "missions",
                "query": "SELECT * FROM missions WHERE status = 'completed'"
            },
            sync_interval=timedelta(hours=1)
        )
        
        mission_transformations = [
            TransformationRule(
                name="calculate_efficiency",
                source_field="mission_metrics",
                target_field="efficiency_score",
                transformation_type="calculate",
                parameters={
                    "formula": "coverage_percentage * (1 - (duration_hours / max_duration))"
                }
            ),
            TransformationRule(
                name="aggregate_discoveries",
                source_field="discovery_count",
                target_field="discovery_summary",
                transformation_type="aggregate",
                parameters={"group_by": "mission_type", "aggregation": "sum"}
            )
        ]
        
        mission_job = PipelineJob(
            id=str(uuid.uuid4()),
            name="mission_analytics",
            description="Generate mission analytics",
            source=mission_source,
            transformations=mission_transformations,
            target="mission_analytics",
            schedule="0 0 */1 * * *"  # Every hour
        )
        
        self.add_job(mission_job)
    
    def add_job(self, job: PipelineJob):
        """Add ETL job to pipeline"""
        self.jobs[job.id] = job
        self.data_sources[job.source.name] = job.source
        self.transformations[job.id] = job.transformations
        
        logger.info(f"Added ETL job: {job.name}")
    
    def remove_job(self, job_id: str):
        """Remove ETL job from pipeline"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            del self.jobs[job_id]
            
            # Clean up related data
            if job.source.name in self.data_sources:
                del self.data_sources[job.source.name]
            if job_id in self.transformations:
                del self.transformations[job_id]
            
            logger.info(f"Removed ETL job: {job.name}")
    
    async def start_pipeline(self):
        """Start the ETL pipeline"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting ETL pipeline")
        
        # Start pipeline scheduler
        asyncio.create_task(self._pipeline_scheduler())
        
        # Start real-time data processing
        asyncio.create_task(self._real_time_processor())
    
    async def stop_pipeline(self):
        """Stop the ETL pipeline"""
        self.running = False
        logger.info("ETL pipeline stopped")
    
    async def _pipeline_scheduler(self):
        """Schedule and execute ETL jobs"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                for job in self.jobs.values():
                    if job.status == "idle" and self._should_run_job(job, current_time):
                        # Schedule job execution
                        asyncio.create_task(self._execute_job(job))
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in pipeline scheduler: {e}")
                await asyncio.sleep(30)
    
    def _should_run_job(self, job: PipelineJob, current_time: datetime) -> bool:
        """Check if job should run based on schedule"""
        if job.last_run is None:
            return True
        
        # Simple schedule checking (in production, use cron parser)
        if job.schedule == "*/30 * * * * *":  # Every 30 seconds
            return (current_time - job.last_run).total_seconds() >= 30
        elif job.schedule == "0 */1 * * * *":  # Every minute
            return (current_time - job.last_run).total_seconds() >= 60
        elif job.schedule == "0 0 */1 * * *":  # Every hour
            return (current_time - job.last_run).total_seconds() >= 3600
        
        return False
    
    async def _execute_job(self, job: PipelineJob):
        """Execute ETL job"""
        try:
            job.status = "running"
            job.last_run = datetime.utcnow()
            
            logger.info(f"Executing ETL job: {job.name}")
            
            # Extract data
            raw_data = await self._extract_data(job.source)
            
            if raw_data is None or len(raw_data) == 0:
                logger.warning(f"No data extracted for job: {job.name}")
                job.status = "completed"
                return
            
            # Transform data
            transformed_data = await self._transform_data(raw_data, job.transformations)
            
            # Load data
            await self._load_data(transformed_data, job.target)
            
            job.status = "completed"
            job.metadata["last_processed_count"] = len(transformed_data)
            job.metadata["last_execution_time"] = (datetime.utcnow() - job.last_run).total_seconds()
            
            logger.info(f"ETL job completed: {job.name}")
            
        except Exception as e:
            job.status = "failed"
            job.metadata["last_error"] = str(e)
            logger.error(f"ETL job failed: {job.name} - {e}")
    
    async def _extract_data(self, source: DataSource) -> Optional[List[Dict[str, Any]]]:
        """Extract data from source"""
        try:
            if source.type == "kafka":
                return await self._extract_from_kafka(source)
            elif source.type == "database":
                return await self._extract_from_database(source)
            elif source.type == "api":
                return await self._extract_from_api(source)
            elif source.type == "file":
                return await self._extract_from_file(source)
            else:
                logger.error(f"Unsupported source type: {source.type}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting data from {source.name}: {e}")
            return None
    
    async def _extract_from_kafka(self, source: DataSource) -> List[Dict[str, Any]]:
        """Extract data from Kafka topic"""
        config = source.config
        topic = config["topic"]
        consumer_group = config.get("consumer_group", "etl_consumer")
        
        # Create consumer for this specific extraction
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.kafka_consumer.config['bootstrap_servers'],
            group_id=consumer_group,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
            consumer_timeout_ms=5000  # 5 second timeout
        )
        
        messages = []
        try:
            message_batch = consumer.poll(timeout_ms=5000)
            for topic_partition, message_list in message_batch.items():
                for message in message_list:
                    messages.append(message.value)
        finally:
            consumer.close()
        
        return messages
    
    async def _extract_from_database(self, source: DataSource) -> List[Dict[str, Any]]:
        """Extract data from database"""
        config = source.config
        query = config.get("query", f"SELECT * FROM {config['table']}")
        
        with self.db_engine.connect() as connection:
            result = connection.execute(text(query))
            columns = result.keys()
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def _extract_from_api(self, source: DataSource) -> List[Dict[str, Any]]:
        """Extract data from API"""
        # This would implement API data extraction
        # For now, return empty list
        return []
    
    async def _extract_from_file(self, source: DataSource) -> List[Dict[str, Any]]:
        """Extract data from file"""
        # This would implement file data extraction
        # For now, return empty list
        return []
    
    async def _transform_data(self, data: List[Dict[str, Any]], 
                            transformations: List[TransformationRule]) -> List[Dict[str, Any]]:
        """Transform data using transformation rules"""
        if not data:
            return data
        
        df = pd.DataFrame(data)
        original_columns = df.columns.tolist()
        
        for transformation in transformations:
            if not transformation.enabled:
                continue
            
            try:
                if transformation.transformation_type == "clean":
                    df = await self._apply_clean_transformation(df, transformation)
                elif transformation.transformation_type == "calculate":
                    df = await self._apply_calculate_transformation(df, transformation)
                elif transformation.transformation_type == "map":
                    df = await self._apply_map_transformation(df, transformation)
                elif transformation.transformation_type == "filter":
                    df = await self._apply_filter_transformation(df, transformation)
                elif transformation.transformation_type == "aggregate":
                    df = await self._apply_aggregate_transformation(df, transformation)
                
            except Exception as e:
                logger.error(f"Error applying transformation {transformation.name}: {e}")
                continue
        
        # Convert back to list of dictionaries
        return df.to_dict('records')
    
    async def _apply_clean_transformation(self, df: pd.DataFrame, 
                                        transformation: TransformationRule) -> pd.DataFrame:
        """Apply data cleaning transformation"""
        source_field = transformation.source_field
        target_field = transformation.target_field
        params = transformation.parameters
        
        if source_field not in df.columns:
            return df
        
        # Remove outliers if requested
        if params.get("remove_outliers", False):
            Q1 = df[source_field].quantile(0.25)
            Q3 = df[source_field].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df = df[(df[source_field] >= lower_bound) & (df[source_field] <= upper_bound)]
        
        # Smooth data if requested
        if params.get("smooth_data", False):
            df[target_field] = df[source_field].rolling(window=params.get("window_size", 3)).mean()
        else:
            df[target_field] = df[source_field]
        
        return df
    
    async def _apply_calculate_transformation(self, df: pd.DataFrame, 
                                            transformation: TransformationRule) -> pd.DataFrame:
        """Apply calculation transformation"""
        source_field = transformation.source_field
        target_field = transformation.target_field
        params = transformation.parameters
        
        if params.get("method") == "derivative":
            # Calculate velocity from position data
            window_size = params.get("window_size", 5)
            df[target_field] = df[source_field].diff().rolling(window=window_size).mean()
        
        elif params.get("method") == "formula":
            # Apply custom formula
            formula = params.get("formula", "")
            # This would evaluate the formula safely
            df[target_field] = eval(formula, {"df": df, "np": np})
        
        return df
    
    async def _apply_map_transformation(self, df: pd.DataFrame, 
                                      transformation: TransformationRule) -> pd.DataFrame:
        """Apply mapping transformation"""
        source_field = transformation.source_field
        target_field = transformation.target_field
        params = transformation.parameters
        
        if source_field not in df.columns:
            return df
        
        if "mapping" in params:
            # Direct value mapping
            mapping = params["mapping"]
            df[target_field] = df[source_field].map(mapping)
        
        elif "format" in params:
            # Format transformation
            if params["format"] == "unix_timestamp":
                df[target_field] = pd.to_datetime(df[source_field]).astype(int) // 10**9
        
        return df
    
    async def _apply_filter_transformation(self, df: pd.DataFrame, 
                                         transformation: TransformationRule) -> pd.DataFrame:
        """Apply filtering transformation"""
        source_field = transformation.source_field
        target_field = transformation.target_field
        params = transformation.parameters
        
        if source_field not in df.columns:
            return df
        
        # Apply filters
        filtered_df = df.copy()
        
        if "min_confidence" in params:
            filtered_df = filtered_df[filtered_df[source_field] >= params["min_confidence"]]
        
        if "max_confidence" in params:
            filtered_df = filtered_df[filtered_df[source_field] <= params["max_confidence"]]
        
        # Create validated field
        filtered_df[target_field] = filtered_df[source_field]
        
        return filtered_df
    
    async def _apply_aggregate_transformation(self, df: pd.DataFrame, 
                                           transformation: TransformationRule) -> pd.DataFrame:
        """Apply aggregation transformation"""
        source_field = transformation.source_field
        target_field = transformation.target_field
        params = transformation.parameters
        
        if source_field not in df.columns:
            return df
        
        group_by = params.get("group_by", [])
        aggregation = params.get("aggregation", "sum")
        
        if group_by and isinstance(group_by, str):
            group_by = [group_by]
        
        if group_by:
            grouped = df.groupby(group_by)[source_field].agg(aggregation)
            # Convert back to DataFrame format
            df[target_field] = df[source_field]  # Simplified for now
        else:
            df[target_field] = df[source_field].agg(aggregation)
        
        return df
    
    async def _load_data(self, data: List[Dict[str, Any]], target: str):
        """Load transformed data to target"""
        if not data:
            return
        
        try:
            # Store in Redis for real-time access
            await self._load_to_redis(data, target)
            
            # Store in database for persistence
            await self._load_to_database(data, target)
            
            # Publish to Kafka for downstream consumers
            await self._load_to_kafka(data, target)
            
        except Exception as e:
            logger.error(f"Error loading data to {target}: {e}")
            raise
    
    async def _load_to_redis(self, data: List[Dict[str, Any]], target: str):
        """Load data to Redis"""
        key = f"etl:{target}:latest"
        
        # Store as JSON
        self.redis_client.set(key, json.dumps(data), ex=3600)  # 1 hour TTL
        
        # Store individual records for fast access
        for i, record in enumerate(data):
            record_key = f"etl:{target}:record:{i}"
            self.redis_client.set(record_key, json.dumps(record), ex=3600)
    
    async def _load_to_database(self, data: List[Dict[str, Any]], target: str):
        """Load data to database"""
        if not data:
            return
        
        df = pd.DataFrame(data)
        
        # Create table name from target
        table_name = target.replace("-", "_")
        
        # Load to database
        df.to_sql(table_name, self.db_engine, if_exists='append', index=False)
    
    async def _load_to_kafka(self, data: List[Dict[str, Any]], target: str):
        """Load data to Kafka"""
        topic = f"processed_{target}"
        
        for record in data:
            self.kafka_producer.send(topic, record)
        
        self.kafka_producer.flush()
    
    async def _real_time_processor(self):
        """Process real-time data streams"""
        while self.running:
            try:
                # Process real-time telemetry
                await self._process_real_time_telemetry()
                
                # Process real-time discoveries
                await self._process_real_time_discoveries()
                
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error(f"Error in real-time processor: {e}")
                await asyncio.sleep(5)
    
    async def _process_real_time_telemetry(self):
        """Process real-time telemetry data"""
        # This would implement real-time telemetry processing
        pass
    
    async def _process_real_time_discoveries(self):
        """Process real-time discovery data"""
        # This would implement real-time discovery processing
        pass
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get pipeline status and statistics"""
        return {
            "total_jobs": len(self.jobs),
            "running_jobs": len([job for job in self.jobs.values() if job.status == "running"]),
            "failed_jobs": len([job for job in self.jobs.values() if job.status == "failed"]),
            "jobs": {
                job_id: {
                    "name": job.name,
                    "status": job.status,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "metadata": job.metadata
                }
                for job_id, job in self.jobs.items()
            }
        }

# Global ETL pipeline instance
etl_pipeline = None

def initialize_etl_pipeline(config: Dict[str, Any]):
    """Initialize global ETL pipeline"""
    global etl_pipeline
    etl_pipeline = ETLPipeline(config)
    return etl_pipeline
