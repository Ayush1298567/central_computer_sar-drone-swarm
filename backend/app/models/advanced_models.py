"""
Advanced database models for production SAR system
Includes vector embeddings, knowledge graphs, and ML model metadata
"""
from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Integer, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from ..core.database import Base

class VectorEmbedding(Base):
    """Store vector embeddings for RAG system and semantic search"""
    __tablename__ = "vector_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_type = Column(String(50), nullable=False, index=True)  # mission, discovery, knowledge, terrain
    content_id = Column(String(100), nullable=False, index=True)
    embedding_model = Column(String(100), nullable=False)  # sentence-transformers model name
    embedding_vector = Column(ARRAY(Float), nullable=False)  # Vector stored as array
    embedding_dimension = Column(Integer, nullable=False)  # Vector dimension for validation
    content_text = Column(Text)  # Original text that was embedded
    metadata = Column(JSONB)  # Additional metadata
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_embedding_content', 'content_type', 'content_id'),
        Index('idx_embedding_model', 'embedding_model'),
        Index('idx_embedding_created', 'created_at'),
        UniqueConstraint('content_type', 'content_id', 'embedding_model', name='unique_content_embedding'),
    )

class MissionKnowledge(Base):
    """Knowledge base for mission patterns, outcomes, and optimization"""
    __tablename__ = "mission_knowledge"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_type = Column(String(50), nullable=False)  # pattern, outcome, lesson, optimization
    mission_pattern = Column(String(100), nullable=False, index=True)
    terrain_type = Column(String(50), index=True)
    weather_conditions = Column(JSONB)
    search_pattern = Column(String(50))  # grid, spiral, sector, etc.
    drone_count = Column(Integer)
    mission_duration_minutes = Column(Integer)
    
    # Performance metrics
    success_rate = Column(Float)  # 0.0 to 1.0
    discovery_rate = Column(Float)  # discoveries per hour
    coverage_efficiency = Column(Float)  # area covered per hour
    battery_efficiency = Column(Float)  # mission duration vs battery usage
    
    # Knowledge content
    optimal_parameters = Column(JSONB)  # Best practices for this scenario
    lessons_learned = Column(Text)
    failure_modes = Column(JSONB)  # Common failure patterns
    success_factors = Column(JSONB)  # Key success factors
    
    # Confidence and reliability
    confidence_score = Column(Float, default=0.5)  # 0.0 to 1.0
    sample_size = Column(Integer, default=1)  # Number of missions this knowledge is based on
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    success_impact = Column(Float, default=0.0)  # Measured impact on mission success
    
    @hybrid_property
    def reliability_score(self):
        """Calculate knowledge reliability based on sample size and confidence"""
        return min(self.confidence_score * (1 + 0.1 * min(self.sample_size, 10)), 1.0)
    
    @hybrid_property
    def knowledge_weight(self):
        """Calculate weight for this knowledge in decision making"""
        return self.reliability_score * (1 + 0.2 * min(self.usage_count / 10, 1))
    
    __table_args__ = (
        Index('idx_knowledge_pattern', 'mission_pattern'),
        Index('idx_knowledge_terrain', 'terrain_type'),
        Index('idx_knowledge_reliability', 'confidence_score', 'sample_size'),
        Index('idx_knowledge_updated', 'last_updated'),
    )

class DronePerformanceModel(Base):
    """ML model metadata and performance tracking for drone optimization"""
    __tablename__ = "drone_performance_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False, unique=True)
    model_version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=False)  # coverage_prediction, battery_estimation, terrain_classification, etc.
    
    # Model configuration
    model_architecture = Column(String(100))  # CNN, LSTM, Transformer, etc.
    input_features = Column(ARRAY(String))  # List of input feature names
    output_classes = Column(ARRAY(String))  # For classification models
    model_parameters = Column(JSONB)  # Hyperparameters, config
    
    # Training data
    training_data_size = Column(Integer)
    training_data_period = Column(String(50))  # Time period of training data
    validation_split = Column(Float, default=0.2)
    
    # Performance metrics
    training_accuracy = Column(Float)
    validation_accuracy = Column(Float)
    test_accuracy = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    f1_score = Column(Float)
    mse = Column(Float)  # For regression models
    mae = Column(Float)  # For regression models
    
    # Model lifecycle
    training_status = Column(String(20), default="not_trained")  # not_trained, training, trained, failed
    deployment_status = Column(String(20), default="training")  # training, staging, production, deprecated
    is_active = Column(Boolean, default=False)
    last_trained = Column(DateTime)
    last_validated = Column(DateTime)
    next_retrain_due = Column(DateTime)
    
    # Model artifacts
    model_path = Column(String(500))  # Path to saved model file
    preprocessing_pipeline = Column(JSONB)  # Preprocessing steps
    feature_importance = Column(JSONB)  # Feature importance scores
    
    # Performance tracking in production
    inference_count = Column(Integer, default=0)
    avg_inference_time = Column(Float)  # milliseconds
    accuracy_drift = Column(Float)  # Performance degradation over time
    last_performance_check = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_model_type', 'model_type'),
        Index('idx_model_status', 'deployment_status', 'is_active'),
        Index('idx_model_performance', 'validation_accuracy'),
    )

class TelemetryStream(Base):
    """High-frequency telemetry data for real-time analysis and ML training"""
    __tablename__ = "telemetry_streams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drone_id = Column(String(50), nullable=False, index=True)
    mission_id = Column(String(50), index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Position and movement (high precision)
    position_lat = Column(Float, nullable=False)
    position_lng = Column(Float, nullable=False)
    position_alt = Column(Float, nullable=False)
    velocity_x = Column(Float)  # m/s
    velocity_y = Column(Float)  # m/s
    velocity_z = Column(Float)  # m/s
    acceleration_x = Column(Float)  # m/s²
    acceleration_y = Column(Float)  # m/s²
    acceleration_z = Column(Float)  # m/s²
    
    # Orientation
    roll = Column(Float)  # degrees
    pitch = Column(Float)  # degrees
    yaw = Column(Float)  # degrees
    angular_velocity_x = Column(Float)  # deg/s
    angular_velocity_y = Column(Float)  # deg/s
    angular_velocity_z = Column(Float)  # deg/s
    
    # System status
    battery_level = Column(Float)  # percentage
    battery_voltage = Column(Float)  # volts
    battery_current = Column(Float)  # amperes
    power_consumption = Column(Float)  # watts
    temperature_cpu = Column(Float)  # celsius
    temperature_motor = Column(Float)  # celsius
    temperature_battery = Column(Float)  # celsius
    
    # Flight control
    flight_mode = Column(String(50))  # AUTO, GUIDED, STABILIZE, etc.
    armed_status = Column(Boolean)
    gps_fix_type = Column(Integer)  # 0=no GPS, 1=no fix, 2=2D fix, 3=3D fix
    satellite_count = Column(Integer)
    hdop = Column(Float)  # Horizontal dilution of precision
    
    # Environmental sensors
    wind_speed = Column(Float)  # m/s
    wind_direction = Column(Float)  # degrees
    air_density = Column(Float)  # kg/m³
    barometric_pressure = Column(Float)  # Pa
    humidity = Column(Float)  # percentage
    
    # Communication
    signal_strength = Column(Integer)  # RSSI
    data_rate = Column(Float)  # bits per second
    packet_loss = Column(Float)  # percentage
    latency = Column(Float)  # milliseconds
    
    # Mission-specific data
    waypoint_index = Column(Integer)
    distance_to_target = Column(Float)  # meters
    mission_progress = Column(Float)  # percentage
    
    # Anomaly detection
    anomaly_score = Column(Float, default=0.0)  # 0.0 to 1.0
    anomaly_type = Column(String(50))  # battery, gps, communication, etc.
    is_anomaly = Column(Boolean, default=False, index=True)
    anomaly_confidence = Column(Float)
    
    # ML features (computed from raw data)
    ml_features = Column(JSONB)  # Computed features for ML models
    
    __table_args__ = (
        Index('idx_telemetry_drone_time', 'drone_id', 'timestamp'),
        Index('idx_telemetry_mission', 'mission_id'),
        Index('idx_telemetry_anomaly', 'is_anomaly', 'anomaly_score'),
        Index('idx_telemetry_timestamp', 'timestamp'),
        # TimescaleDB hypertable will be created via migration
    )

class KnowledgeGraph(Base):
    """Knowledge graph relationships for SAR domain knowledge"""
    __tablename__ = "knowledge_graph"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Graph structure
    source_node_id = Column(String(100), nullable=False, index=True)
    source_node_type = Column(String(50), nullable=False)  # mission, drone, terrain, weather, etc.
    target_node_id = Column(String(100), nullable=False, index=True)
    target_node_type = Column(String(50), nullable=False)
    
    # Relationship details
    relationship_type = Column(String(50), nullable=False)  # causes, improves, prevents, requires, etc.
    relationship_strength = Column(Float, default=1.0)  # 0.0 to 1.0
    confidence = Column(Float, default=1.0)  # Confidence in this relationship
    
    # Context and evidence
    context = Column(Text)  # Description of the relationship
    evidence = Column(JSONB)  # Supporting evidence (mission IDs, metrics, etc.)
    evidence_count = Column(Integer, default=1)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float)  # How often this relationship leads to success
    
    __table_args__ = (
        Index('idx_kg_source', 'source_node_id', 'source_node_type'),
        Index('idx_kg_target', 'target_node_id', 'target_node_type'),
        Index('idx_kg_relationship', 'relationship_type'),
        Index('idx_kg_strength', 'relationship_strength', 'confidence'),
        UniqueConstraint('source_node_id', 'target_node_id', 'relationship_type', name='unique_relationship'),
    )

class AIDecisionLog(Base):
    """Log of AI decisions for transparency and learning"""
    __tablename__ = "ai_decision_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Decision context
    decision_type = Column(String(50), nullable=False)  # mission_planning, drone_deployment, emergency_response, etc.
    decision_id = Column(String(100), nullable=False, index=True)
    mission_id = Column(String(50), index=True)
    drone_id = Column(String(50))
    
    # Decision details
    decision_description = Column(Text, nullable=False)
    decision_options = Column(JSONB)  # Available options considered
    selected_option = Column(JSONB)  # The option that was selected
    confidence_score = Column(Float)  # AI confidence in the decision
    
    # Reasoning and explanation
    reasoning_chain = Column(JSONB)  # Step-by-step reasoning
    knowledge_sources = Column(JSONB)  # Knowledge base sources used
    model_predictions = Column(JSONB)  # ML model outputs that influenced decision
    human_feedback = Column(JSONB)  # Human corrections or confirmations
    
    # Decision outcome
    outcome = Column(String(50))  # success, failure, partial_success, unknown
    outcome_metrics = Column(JSONB)  # Quantifiable outcomes
    outcome_timestamp = Column(DateTime)
    
    # Performance tracking
    decision_time_ms = Column(Float)  # Time taken to make decision
    resources_used = Column(JSONB)  # CPU, memory, model inference time
    
    # Learning and improvement
    feedback_score = Column(Float)  # Human feedback score
    improvement_suggestions = Column(Text)
    learning_applied = Column(Boolean, default=False)  # Whether this was used for learning
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_decision_type', 'decision_type'),
        Index('idx_decision_outcome', 'outcome'),
        Index('idx_decision_confidence', 'confidence_score'),
        Index('idx_decision_timestamp', 'timestamp'),
    )

class ModelInferenceLog(Base):
    """Log of ML model inferences for monitoring and debugging"""
    __tablename__ = "model_inference_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model information
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    inference_type = Column(String(50), nullable=False)  # prediction, classification, anomaly_detection, etc.
    
    # Input data
    input_features = Column(JSONB)  # Input features used
    input_data_hash = Column(String(64))  # Hash of input data for deduplication
    
    # Model output
    predictions = Column(JSONB)  # Model predictions
    probabilities = Column(JSONB)  # Prediction probabilities (for classification)
    confidence_scores = Column(JSONB)  # Model confidence scores
    
    # Performance metrics
    inference_time_ms = Column(Float)  # Time taken for inference
    memory_used_mb = Column(Float)  # Memory used during inference
    gpu_used = Column(Boolean, default=False)
    batch_size = Column(Integer, default=1)
    
    # Context
    mission_id = Column(String(50), index=True)
    drone_id = Column(String(50), index=True)
    request_id = Column(String(100))  # For tracing requests
    
    # Validation and feedback
    ground_truth = Column(JSONB)  # Actual outcome (if available)
    prediction_accuracy = Column(Float)  # Accuracy of this prediction
    feedback_provided = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_inference_model', 'model_name', 'model_version'),
        Index('idx_inference_type', 'inference_type'),
        Index('idx_inference_timestamp', 'timestamp'),
        Index('idx_inference_accuracy', 'prediction_accuracy'),
    )

class SystemMetrics(Base):
    """System performance and health metrics"""
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric identification
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram, summary
    component = Column(String(50), nullable=False, index=True)  # api, database, ml, cv, etc.
    
    # Metric values
    value = Column(Float, nullable=False)
    labels = Column(JSONB)  # Additional labels for the metric
    
    # Timing
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    collection_interval = Column(Integer)  # seconds
    
    # Metadata
    unit = Column(String(20))  # seconds, bytes, requests, etc.
    description = Column(Text)
    
    __table_args__ = (
        Index('idx_metrics_name_time', 'metric_name', 'timestamp'),
        Index('idx_metrics_component_time', 'component', 'timestamp'),
        Index('idx_metrics_type', 'metric_type'),
    )

class AlertRule(Base):
    """Configurable alert rules for system monitoring"""
    __tablename__ = "alert_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    rule_name = Column(String(100), nullable=False, unique=True)
    rule_description = Column(Text)
    severity = Column(String(20), nullable=False)  # critical, warning, info
    
    # Rule conditions
    metric_name = Column(String(100), nullable=False)
    condition_type = Column(String(20), nullable=False)  # gt, lt, eq, ne, contains, etc.
    threshold_value = Column(Float)
    threshold_string = Column(String(100))  # For string conditions
    time_window_minutes = Column(Integer, default=5)
    
    # Rule behavior
    is_enabled = Column(Boolean, default=True)
    cooldown_minutes = Column(Integer, default=15)  # Minimum time between alerts
    max_alerts_per_hour = Column(Integer, default=10)
    
    # Notification settings
    notification_channels = Column(JSONB)  # email, slack, webhook, etc.
    notification_template = Column(Text)
    
    # Rule metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_alert_enabled', 'is_enabled'),
        Index('idx_alert_severity', 'severity'),
        Index('idx_alert_metric', 'metric_name'),
    )

class AlertHistory(Base):
    """History of triggered alerts"""
    __tablename__ = "alert_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey('alert_rules.id'), nullable=False)
    
    # Alert details
    alert_title = Column(String(200), nullable=False)
    alert_message = Column(Text)
    severity = Column(String(20), nullable=False)
    
    # Trigger context
    metric_value = Column(Float)
    threshold_value = Column(Float)
    context_data = Column(JSONB)  # Additional context when alert was triggered
    
    # Resolution
    status = Column(String(20), default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Notifications
    notifications_sent = Column(JSONB)  # List of notifications sent
    notification_failures = Column(JSONB)  # Failed notifications
    
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    rule = relationship("AlertRule")
    
    __table_args__ = (
        Index('idx_alert_history_rule', 'rule_id'),
        Index('idx_alert_history_status', 'status'),
        Index('idx_alert_history_triggered', 'triggered_at'),
        Index('idx_alert_history_severity', 'severity'),
    )
