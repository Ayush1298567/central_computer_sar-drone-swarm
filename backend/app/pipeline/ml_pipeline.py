"""
Advanced ML Pipeline for SAR Drone System
Model training, inference, and continuous learning
"""
import asyncio
import logging
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
import lightgbm as lgb
from tensorflow import keras
from tensorflow.keras import layers
import mlflow
import mlflow.sklearn
import mlflow.tensorflow
from kafka import KafkaProducer, KafkaConsumer
import json
import redis

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    model_type: str  # classification, regression, clustering
    algorithm: str   # random_forest, xgboost, neural_network
    features: List[str]
    target: str
    hyperparameters: Dict[str, Any]
    training_data_query: str
    validation_split: float = 0.2
    retrain_interval: timedelta = timedelta(days=1)
    last_trained: Optional[datetime] = None
    version: str = "1.0"
    accuracy_threshold: float = 0.8

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_time: float
    inference_time: float
    data_size: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PredictionRequest:
    """Prediction request"""
    model_name: str
    features: Dict[str, Any]
    request_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PredictionResult:
    """Prediction result"""
    request_id: str
    prediction: Any
    confidence: float
    model_version: str
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

class MLPipeline:
    """Comprehensive ML pipeline system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.model_metrics: Dict[str, List[ModelMetrics]] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        
        # Initialize MLflow
        mlflow.set_tracking_uri(self.config.get('mlflow_uri', 'http://localhost:5000'))
        mlflow.set_experiment("SAR_Drone_ML_Models")
        
        # Initialize connections
        self._setup_connections()
        
        # Initialize default models
        self._setup_default_models()
        
        self.running = False
    
    def _setup_connections(self):
        """Setup database and messaging connections"""
        try:
            # Redis connection for model caching
            redis_config = self.config.get('redis', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 1),
                decode_responses=True
            )
            
            # Kafka connections for real-time inference
            kafka_config = self.config.get('kafka', {})
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=kafka_config.get('bootstrap_servers', ['localhost:9092']),
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            self.kafka_consumer = KafkaConsumer(
                'ml_inference_requests',
                bootstrap_servers=kafka_config.get('bootstrap_servers', ['localhost:9092']),
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            logger.info("ML pipeline connections established")
            
        except Exception as e:
            logger.error(f"Failed to setup ML connections: {e}")
            raise
    
    def _setup_default_models(self):
        """Setup default ML models"""
        
        # Discovery Classification Model
        discovery_model_config = ModelConfig(
            name="discovery_classifier",
            model_type="classification",
            algorithm="random_forest",
            features=["confidence", "image_quality", "weather_visibility", "terrain_type"],
            target="discovery_type",
            hyperparameters={
                "n_estimators": 100,
                "max_depth": 10,
                "random_state": 42
            },
            training_data_query="""
                SELECT confidence, image_quality, weather_visibility, terrain_type, discovery_type
                FROM discoveries 
                WHERE confidence > 0.5 AND discovery_type IS NOT NULL
            """,
            accuracy_threshold=0.85
        )
        
        self.add_model_config(discovery_model_config)
        
        # Mission Success Prediction Model
        mission_model_config = ModelConfig(
            name="mission_success_predictor",
            model_type="regression",
            algorithm="xgboost",
            features=["terrain_type", "weather_conditions", "drone_count", "mission_duration"],
            target="success_rate",
            hyperparameters={
                "n_estimators": 200,
                "max_depth": 6,
                "learning_rate": 0.1,
                "random_state": 42
            },
            training_data_query="""
                SELECT terrain_type, weather_conditions, drone_count, mission_duration, success_rate
                FROM missions 
                WHERE status = 'completed' AND success_rate IS NOT NULL
            """,
            accuracy_threshold=0.8
        )
        
        self.add_model_config(mission_model_config)
        
        # Drone Battery Prediction Model
        battery_model_config = ModelConfig(
            name="battery_predictor",
            model_type="regression",
            algorithm="neural_network",
            features=["current_battery", "flight_time", "weather_conditions", "mission_type"],
            target="battery_remaining_time",
            hyperparameters={
                "hidden_layers": [64, 32, 16],
                "activation": "relu",
                "optimizer": "adam",
                "epochs": 100,
                "batch_size": 32
            },
            training_data_query="""
                SELECT current_battery, flight_time, weather_conditions, mission_type, battery_remaining_time
                FROM drone_telemetry 
                WHERE battery_remaining_time IS NOT NULL
            """,
            accuracy_threshold=0.75
        )
        
        self.add_model_config(battery_model_config)
        
        # Survivor Detection Model (Computer Vision)
        survivor_model_config = ModelConfig(
            name="survivor_detector",
            model_type="classification",
            algorithm="neural_network",
            features=["image_features", "terrain_type", "lighting_conditions"],
            target="survivor_present",
            hyperparameters={
                "hidden_layers": [128, 64, 32],
                "activation": "relu",
                "optimizer": "adam",
                "epochs": 50,
                "batch_size": 16
            },
            training_data_query="""
                SELECT image_features, terrain_type, lighting_conditions, survivor_present
                FROM image_analysis 
                WHERE image_features IS NOT NULL AND survivor_present IS NOT NULL
            """,
            accuracy_threshold=0.9
        )
        
        self.add_model_config(survivor_model_config)
    
    def add_model_config(self, config: ModelConfig):
        """Add model configuration"""
        self.model_configs[config.name] = config
        self.model_metrics[config.name] = []
        logger.info(f"Added model configuration: {config.name}")
    
    async def start_pipeline(self):
        """Start the ML pipeline"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting ML pipeline")
        
        # Train all models
        await self._train_all_models()
        
        # Start model retraining scheduler
        asyncio.create_task(self._model_retraining_scheduler())
        
        # Start real-time inference processor
        asyncio.create_task(self._inference_processor())
        
        # Start model monitoring
        asyncio.create_task(self._model_monitor())
    
    async def stop_pipeline(self):
        """Stop the ML pipeline"""
        self.running = False
        logger.info("ML pipeline stopped")
    
    async def _train_all_models(self):
        """Train all configured models"""
        for model_name, config in self.model_configs.items():
            try:
                await self._train_model(model_name)
            except Exception as e:
                logger.error(f"Failed to train model {model_name}: {e}")
    
    async def _train_model(self, model_name: str):
        """Train a specific model"""
        config = self.model_configs.get(model_name)
        if not config:
            logger.error(f"Model configuration not found: {model_name}")
            return
        
        logger.info(f"Training model: {model_name}")
        
        start_time = datetime.utcnow()
        
        # Load training data
        training_data = await self._load_training_data(config)
        if training_data is None or len(training_data) == 0:
            logger.warning(f"No training data available for model: {model_name}")
            return
        
        # Prepare features and target
        X, y = await self._prepare_training_data(training_data, config)
        
        if len(X) == 0:
            logger.warning(f"Empty training data for model: {model_name}")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.validation_split, random_state=42
        )
        
        # Train model
        model = await self._train_model_algorithm(X_train, y_train, config)
        
        # Evaluate model
        metrics = await self._evaluate_model(model, X_test, y_test, config)
        
        # Store model if it meets accuracy threshold
        if metrics.accuracy >= config.accuracy_threshold:
            await self._store_model(model_name, model, config, metrics)
            logger.info(f"Model {model_name} trained successfully with accuracy: {metrics.accuracy:.3f}")
        else:
            logger.warning(f"Model {model_name} accuracy {metrics.accuracy:.3f} below threshold {config.accuracy_threshold}")
        
        # Update model config
        config.last_trained = datetime.utcnow()
    
    async def _load_training_data(self, config: ModelConfig) -> Optional[pd.DataFrame]:
        """Load training data from database"""
        try:
            # This would connect to the actual database
            # For now, generate synthetic data
            return self._generate_synthetic_data(config)
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return None
    
    def _generate_synthetic_data(self, config: ModelConfig) -> pd.DataFrame:
        """Generate synthetic training data"""
        np.random.seed(42)
        n_samples = 1000
        
        data = {}
        
        for feature in config.features:
            if feature == "confidence":
                data[feature] = np.random.uniform(0.5, 1.0, n_samples)
            elif feature == "image_quality":
                data[feature] = np.random.uniform(0.6, 1.0, n_samples)
            elif feature == "weather_visibility":
                data[feature] = np.random.uniform(5.0, 20.0, n_samples)
            elif feature == "terrain_type":
                data[feature] = np.random.choice(["mountain", "forest", "urban", "water"], n_samples)
            elif feature == "current_battery":
                data[feature] = np.random.uniform(20.0, 100.0, n_samples)
            elif feature == "flight_time":
                data[feature] = np.random.uniform(0, 120, n_samples)
            elif feature == "weather_conditions":
                data[feature] = np.random.choice(["good", "fair", "poor"], n_samples)
            elif feature == "mission_type":
                data[feature] = np.random.choice(["search", "rescue", "surveillance"], n_samples)
            elif feature == "drone_count":
                data[feature] = np.random.randint(1, 6, n_samples)
            elif feature == "mission_duration":
                data[feature] = np.random.uniform(0.5, 8.0, n_samples)
            else:
                data[feature] = np.random.randn(n_samples)
        
        # Generate target based on model type
        if config.model_type == "classification":
            if config.target == "discovery_type":
                data[config.target] = np.random.choice(["person", "vehicle", "structure", "debris"], n_samples)
            elif config.target == "survivor_present":
                data[config.target] = np.random.choice([0, 1], n_samples)
        elif config.model_type == "regression":
            if config.target == "success_rate":
                data[config.target] = np.random.uniform(0.6, 1.0, n_samples)
            elif config.target == "battery_remaining_time":
                data[config.target] = np.random.uniform(5, 60, n_samples)
        
        return pd.DataFrame(data)
    
    async def _prepare_training_data(self, data: pd.DataFrame, config: ModelConfig) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for model training"""
        # Select features
        X = data[config.features].copy()
        y = data[config.target].copy()
        
        # Handle categorical variables
        for feature in config.features:
            if X[feature].dtype == 'object':
                if feature not in self.encoders:
                    self.encoders[feature] = LabelEncoder()
                    X[feature] = self.encoders[feature].fit_transform(X[feature])
                else:
                    X[feature] = self.encoders[feature].transform(X[feature])
        
        # Handle target variable for classification
        if config.model_type == "classification" and y.dtype == 'object':
            if config.target not in self.encoders:
                self.encoders[config.target] = LabelEncoder()
                y = self.encoders[config.target].fit_transform(y)
            else:
                y = self.encoders[config.target].transform(y)
        
        # Scale features
        scaler_key = f"{config.name}_scaler"
        if scaler_key not in self.scalers:
            self.scalers[scaler_key] = StandardScaler()
            X_scaled = self.scalers[scaler_key].fit_transform(X)
        else:
            X_scaled = self.scalers[scaler_key].transform(X)
        
        return X_scaled, y.values
    
    async def _train_model_algorithm(self, X_train: np.ndarray, y_train: np.ndarray, 
                                   config: ModelConfig) -> Any:
        """Train model using specified algorithm"""
        
        if config.algorithm == "random_forest":
            model = RandomForestClassifier(**config.hyperparameters)
            model.fit(X_train, y_train)
        
        elif config.algorithm == "xgboost":
            if config.model_type == "classification":
                model = xgb.XGBClassifier(**config.hyperparameters)
            else:
                model = xgb.XGBRegressor(**config.hyperparameters)
            model.fit(X_train, y_train)
        
        elif config.algorithm == "neural_network":
            model = await self._train_neural_network(X_train, y_train, config)
        
        else:
            raise ValueError(f"Unsupported algorithm: {config.algorithm}")
        
        return model
    
    async def _train_neural_network(self, X_train: np.ndarray, y_train: np.ndarray, 
                                  config: ModelConfig) -> keras.Model:
        """Train neural network model"""
        input_dim = X_train.shape[1]
        
        model = keras.Sequential()
        model.add(layers.Dense(input_dim, activation=config.hyperparameters.get('activation', 'relu')))
        
        # Add hidden layers
        for hidden_size in config.hyperparameters.get('hidden_layers', [64, 32]):
            model.add(layers.Dense(hidden_size, activation=config.hyperparameters.get('activation', 'relu')))
            model.add(layers.Dropout(0.2))
        
        # Add output layer
        if config.model_type == "classification":
            n_classes = len(np.unique(y_train))
            if n_classes == 2:
                model.add(layers.Dense(1, activation='sigmoid'))
                model.compile(
                    optimizer=config.hyperparameters.get('optimizer', 'adam'),
                    loss='binary_crossentropy',
                    metrics=['accuracy']
                )
            else:
                model.add(layers.Dense(n_classes, activation='softmax'))
                model.compile(
                    optimizer=config.hyperparameters.get('optimizer', 'adam'),
                    loss='sparse_categorical_crossentropy',
                    metrics=['accuracy']
                )
        else:  # regression
            model.add(layers.Dense(1))
            model.compile(
                optimizer=config.hyperparameters.get('optimizer', 'adam'),
                loss='mse',
                metrics=['mae']
            )
        
        # Train model
        epochs = config.hyperparameters.get('epochs', 100)
        batch_size = config.hyperparameters.get('batch_size', 32)
        
        model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
        
        return model
    
    async def _evaluate_model(self, model: Any, X_test: np.ndarray, y_test: np.ndarray, 
                            config: ModelConfig) -> ModelMetrics:
        """Evaluate model performance"""
        start_time = time.time()
        
        # Make predictions
        if config.algorithm == "neural_network":
            y_pred = model.predict(X_test)
            if config.model_type == "classification":
                if y_pred.shape[1] == 1:  # binary classification
                    y_pred = (y_pred > 0.5).astype(int).flatten()
                else:  # multiclass
                    y_pred = np.argmax(y_pred, axis=1)
        else:
            y_pred = model.predict(X_test)
        
        inference_time = time.time() - start_time
        
        # Calculate metrics
        if config.model_type == "classification":
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        else:  # regression
            # For regression, use R² score as accuracy
            from sklearn.metrics import r2_score
            accuracy = r2_score(y_test, y_pred)
            precision = recall = f1 = accuracy  # Same as accuracy for regression
        
        return ModelMetrics(
            model_name=config.name,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            training_time=0,  # Will be set by caller
            inference_time=inference_time,
            data_size=len(X_test)
        )
    
    async def _store_model(self, model_name: str, model: Any, config: ModelConfig, metrics: ModelMetrics):
        """Store trained model"""
        try:
            # Store model in memory
            self.models[model_name] = model
            
            # Store model in Redis for fast access
            model_key = f"model:{model_name}"
            if config.algorithm == "neural_network":
                # Save Keras model to bytes
                model_bytes = model.to_json().encode()
                self.redis_client.set(f"{model_key}:json", model_bytes, ex=86400)  # 24 hours
            else:
                # Serialize sklearn/XGBoost models
                model_bytes = pickle.dumps(model)
                self.redis_client.set(f"{model_key}:pickle", model_bytes, ex=86400)
            
            # Store model metadata
            metadata = {
                "version": config.version,
                "algorithm": config.algorithm,
                "features": config.features,
                "accuracy": metrics.accuracy,
                "trained_at": datetime.utcnow().isoformat()
            }
            self.redis_client.set(f"{model_key}:metadata", json.dumps(metadata), ex=86400)
            
            # Log to MLflow
            with mlflow.start_run():
                mlflow.log_params(config.hyperparameters)
                mlflow.log_metrics({
                    "accuracy": metrics.accuracy,
                    "precision": metrics.precision,
                    "recall": metrics.recall,
                    "f1_score": metrics.f1_score
                })
                
                if config.algorithm == "neural_network":
                    mlflow.tensorflow.log_model(model, f"models/{model_name}")
                else:
                    mlflow.sklearn.log_model(model, f"models/{model_name}")
            
            # Store metrics
            self.model_metrics[model_name].append(metrics)
            
            logger.info(f"Model {model_name} stored successfully")
            
        except Exception as e:
            logger.error(f"Error storing model {model_name}: {e}")
    
    async def _model_retraining_scheduler(self):
        """Schedule model retraining"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                for model_name, config in self.model_configs.items():
                    if config.last_trained is None:
                        continue
                    
                    time_since_training = current_time - config.last_trained
                    if time_since_training >= config.retrain_interval:
                        logger.info(f"Scheduling retraining for model: {model_name}")
                        asyncio.create_task(self._train_model(model_name))
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in retraining scheduler: {e}")
                await asyncio.sleep(3600)
    
    async def _inference_processor(self):
        """Process real-time inference requests"""
        while self.running:
            try:
                # Poll for inference requests
                message_batch = self.kafka_consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        request = PredictionRequest(**message.value)
                        await self._process_inference_request(request)
                
            except Exception as e:
                logger.error(f"Error in inference processor: {e}")
                await asyncio.sleep(5)
    
    async def _process_inference_request(self, request: PredictionRequest):
        """Process single inference request"""
        try:
            start_time = time.time()
            
            # Load model
            model = await self._load_model_for_inference(request.model_name)
            if model is None:
                logger.error(f"Model not found for inference: {request.model_name}")
                return
            
            # Prepare features
            features = await self._prepare_inference_features(request.features, request.model_name)
            
            # Make prediction
            prediction = model.predict(features.reshape(1, -1))
            
            # Calculate confidence (simplified)
            confidence = 0.8  # This would be calculated based on model output
            
            processing_time = time.time() - start_time
            
            # Create result
            result = PredictionResult(
                request_id=request.request_id,
                prediction=prediction[0] if len(prediction.shape) > 0 else prediction,
                confidence=confidence,
                model_version="1.0",
                processing_time=processing_time
            )
            
            # Send result back
            self.kafka_producer.send(
                'ml_inference_results',
                {
                    "request_id": result.request_id,
                    "prediction": float(result.prediction),
                    "confidence": result.confidence,
                    "model_version": result.model_version,
                    "processing_time": result.processing_time,
                    "timestamp": result.timestamp.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing inference request {request.request_id}: {e}")
    
    async def _load_model_for_inference(self, model_name: str) -> Optional[Any]:
        """Load model for inference"""
        # Check if model is in memory
        if model_name in self.models:
            return self.models[model_name]
        
        # Try to load from Redis
        model_key = f"model:{model_name}"
        try:
            config = self.model_configs[model_name]
            
            if config.algorithm == "neural_network":
                model_json = self.redis_client.get(f"{model_key}:json")
                if model_json:
                    model = keras.models.model_from_json(model_json.decode())
                    # Note: In production, you'd also need to load weights
                    return model
            else:
                model_bytes = self.redis_client.get(f"{model_key}:pickle")
                if model_bytes:
                    return pickle.loads(model_bytes)
        except Exception as e:
            logger.error(f"Error loading model from Redis: {e}")
        
        return None
    
    async def _prepare_inference_features(self, features: Dict[str, Any], model_name: str) -> np.ndarray:
        """Prepare features for inference"""
        config = self.model_configs[model_name]
        
        # Convert to array
        feature_array = []
        for feature in config.features:
            value = features.get(feature, 0)
            
            # Handle categorical encoding
            if feature in self.encoders:
                try:
                    value = self.encoders[feature].transform([value])[0]
                except ValueError:
                    # Handle unseen categories
                    value = 0
            elif isinstance(value, str):
                # Simple string to numeric conversion
                value = hash(value) % 1000
            
            feature_array.append(value)
        
        feature_array = np.array(feature_array)
        
        # Apply scaling
        scaler_key = f"{model_name}_scaler"
        if scaler_key in self.scalers:
            feature_array = self.scalers[scaler_key].transform(feature_array.reshape(1, -1)).flatten()
        
        return feature_array
    
    async def _model_monitor(self):
        """Monitor model performance"""
        while self.running:
            try:
                # Check model performance metrics
                for model_name in self.model_configs.keys():
                    await self._check_model_performance(model_name)
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in model monitor: {e}")
                await asyncio.sleep(3600)
    
    async def _check_model_performance(self, model_name: str):
        """Check model performance and trigger retraining if needed"""
        metrics_history = self.model_metrics.get(model_name, [])
        if len(metrics_history) < 2:
            return
        
        # Check if accuracy is degrading
        recent_accuracy = metrics_history[-1].accuracy
        previous_accuracy = metrics_history[-2].accuracy
        
        if recent_accuracy < previous_accuracy * 0.95:  # 5% degradation
            logger.warning(f"Model {model_name} performance degrading, scheduling retraining")
            asyncio.create_task(self._train_model(model_name))
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get ML pipeline status"""
        return {
            "total_models": len(self.model_configs),
            "trained_models": len(self.models),
            "models": {
                model_name: {
                    "config": {
                        "algorithm": config.algorithm,
                        "model_type": config.model_type,
                        "features": config.features,
                        "target": config.target,
                        "accuracy_threshold": config.accuracy_threshold
                    },
                    "status": "trained" if model_name in self.models else "not_trained",
                    "last_trained": config.last_trained.isoformat() if config.last_trained else None,
                    "metrics": [
                        {
                            "accuracy": m.accuracy,
                            "precision": m.precision,
                            "recall": m.recall,
                            "f1_score": m.f1_score,
                            "timestamp": m.timestamp.isoformat()
                        }
                        for m in self.model_metrics.get(model_name, [])[-5:]  # Last 5 metrics
                    ]
                }
                for model_name, config in self.model_configs.items()
            }
        }

# Global ML pipeline instance
ml_pipeline = None

def initialize_ml_pipeline(config: Dict[str, Any]):
    """Initialize global ML pipeline"""
    global ml_pipeline
    ml_pipeline = MLPipeline(config)
    return ml_pipeline
