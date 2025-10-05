import logging
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
from PIL import Image
import io
import base64
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import PyTorch with graceful fallback
try:
    import torch
    import torchvision
    from torchvision.models.detection import fasterrcnn_resnet50_fpn, FasterRCNN_ResNet50_FPN_Weights
    from torchvision import transforms
    PYTORCH_AVAILABLE = True
    logger.info("✅ PyTorch loaded successfully")
except ImportError as e:
    PYTORCH_AVAILABLE = False
    logger.warning(f"⚠️ PyTorch not available: {e}. Using fallback detection.")

# Try YOLO as alternative
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    logger.info("✅ YOLO loaded successfully")
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("⚠️ YOLO not available. Computer vision will use basic detection.")

# Try OpenCV as final fallback
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("✅ OpenCV loaded successfully")
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("⚠️ OpenCV not available. Using minimal detection.")

class AdvancedComputerVision:
    """
    Advanced computer vision system for SAR drone operations
    Supports multiple detection backends with graceful fallbacks
    """
    
    def __init__(self):
        self.model = None
        self.device = "cpu"
        self.model_type = None
        self.detection_classes = {
            0: "person",
            1: "bicycle", 
            2: "car",
            3: "motorcycle",
            4: "airplane",
            5: "bus",
            6: "train",
            7: "truck",
            8: "boat",
            9: "traffic_light",
            10: "fire_hydrant",
            11: "stop_sign",
            12: "parking_meter",
            13: "bench",
            14: "bird",
            15: "cat",
            16: "dog",
            17: "horse",
            18: "sheep",
            19: "cow",
            20: "elephant",
            21: "bear",
            22: "zebra",
            23: "giraffe",
            24: "backpack",
            25: "umbrella",
            26: "handbag",
            27: "tie",
            28: "suitcase",
            29: "frisbee",
            30: "skis",
            31: "snowboard",
            32: "sports_ball",
            33: "kite",
            34: "baseball_bat",
            35: "baseball_glove",
            36: "skateboard",
            37: "surfboard",
            38: "tennis_racket",
            39: "bottle",
            40: "wine_glass",
            41: "cup",
            42: "fork",
            43: "knife",
            44: "spoon",
            45: "bowl",
            46: "banana",
            47: "apple",
            48: "sandwich",
            49: "orange",
            50: "broccoli",
            51: "carrot",
            52: "hot_dog",
            53: "pizza",
            54: "donut",
            55: "cake",
            56: "chair",
            57: "couch",
            58: "potted_plant",
            59: "bed",
            60: "dining_table",
            61: "toilet",
            62: "tv",
            63: "laptop",
            64: "mouse",
            65: "remote",
            66: "keyboard",
            67: "cell_phone",
            68: "microwave",
            69: "oven",
            70: "toaster",
            71: "sink",
            72: "refrigerator",
            73: "book",
            74: "clock",
            75: "vase",
            76: "scissors",
            77: "teddy_bear",
            78: "hair_drier",
            79: "toothbrush"
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the best available detection model"""
        try:
            if YOLO_AVAILABLE:
                self._init_yolo()
            elif PYTORCH_AVAILABLE:
                self._init_pytorch()
            elif OPENCV_AVAILABLE:
                self._init_opencv()
            else:
                logger.critical("❌ No computer vision models available!")
                raise RuntimeError("No computer vision backend available")
                
        except Exception as e:
            logger.error(f"❌ Model initialization failed: {e}", exc_info=True)
            raise
    
    def _init_yolo(self):
        """Initialize YOLO model"""
        try:
            self.model = YOLO("yolov8n.pt")  # Lightweight model for speed
            self.model_type = "yolo"
            logger.info("✅ YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO: {e}")
            raise
    
    def _init_pytorch(self):
        """Initialize PyTorch Faster R-CNN model"""
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
            self.model = fasterrcnn_resnet50_fpn(weights=weights)
            self.model.eval()
            self.model.to(self.device)
            self.model_type = "pytorch"
            logger.info(f"✅ PyTorch model loaded on {self.device}")
        except Exception as e:
            logger.error(f"❌ Failed to load PyTorch model: {e}")
            raise
    
    def _init_opencv(self):
        """Initialize OpenCV Haar Cascade fallback"""
        try:
            # Load Haar cascade for person detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_fullbody.xml'
            self.model = cv2.CascadeClassifier(cascade_path)
            self.model_type = "opencv"
            logger.info("✅ OpenCV Haar Cascade loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load OpenCV: {e}")
            raise
    
    async def detect_objects(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        Real object detection - NO MOCKS ALLOWED
        This function must work for actual SAR operations
        """
        if not self.model:
            logger.critical("❌ No detection model available - cannot perform detection!")
            raise RuntimeError("Computer vision model not initialized")
        
        try:
            # Decode image
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            if self.model_type == "yolo":
                return await self._detect_yolo(image)
            elif self.model_type == "pytorch":
                return await self._detect_pytorch(image)
            elif self.model_type == "opencv":
                return await self._detect_opencv(image)
            else:
                raise RuntimeError(f"Unknown model type: {self.model_type}")
        
        except Exception as e:
            logger.error(f"❌ Detection failed: {e}", exc_info=True)
            raise RuntimeError(f"Object detection error: {str(e)}")
    
    async def _detect_yolo(self, image: Image.Image) -> List[Dict[str, Any]]:
        """YOLO detection implementation"""
        try:
            results = self.model(image)
            detections = []
            
            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        # Only include high-confidence detections
                        if confidence > 0.5:
                            detections.append({
                                "class": self.model.names[class_id],
                                "confidence": confidence,
                                "bbox": box.xyxy[0].tolist(),
                                "class_id": class_id,
                                "model": "yolo",
                                "timestamp": datetime.utcnow().isoformat()
                            })
            
            logger.info(f"🔍 YOLO detected {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            raise
    
    async def _detect_pytorch(self, image: Image.Image) -> List[Dict[str, Any]]:
        """PyTorch Faster R-CNN detection implementation"""
        try:
            # Preprocess image
            transform = transforms.Compose([
                transforms.ToTensor()
            ])
            
            image_tensor = transform(image).unsqueeze(0).to(self.device)
            
            # Run inference
            with torch.no_grad():
                predictions = self.model(image_tensor)[0]
            
            detections = []
            for i, (box, label, score) in enumerate(zip(
                predictions['boxes'],
                predictions['labels'],
                predictions['scores']
            )):
                if score > 0.5:  # Confidence threshold
                    class_id = label.item()
                    class_name = self.detection_classes.get(class_id, f"class_{class_id}")
                    
                    detections.append({
                        "class": class_name,
                        "confidence": score.item(),
                        "bbox": box.tolist(),
                        "class_id": class_id,
                        "model": "pytorch",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            logger.info(f"🔍 PyTorch detected {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"PyTorch detection failed: {e}")
            raise
    
    async def _detect_opencv(self, image: Image.Image) -> List[Dict[str, Any]]:
        """OpenCV Haar Cascade detection implementation"""
        try:
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect objects
            objects = self.model.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            detections = []
            for (x, y, w, h) in objects:
                detections.append({
                    "class": "person",  # Haar cascade is typically for person detection
                    "confidence": 0.8,  # Estimated confidence
                    "bbox": [x, y, x + w, y + h],
                    "class_id": 0,
                    "model": "opencv",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.info(f"🔍 OpenCV detected {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"OpenCV detection failed: {e}")
            raise
    
    async def detect_person_in_distress(self, image_data: bytes) -> Dict[str, Any]:
        """
        Specialized detection for persons in distress
        Critical for SAR operations
        """
        try:
            detections = await self.detect_objects(image_data)
            
            # Filter for person detections
            person_detections = [
                det for det in detections 
                if det["class"] in ["person", "people"] and det["confidence"] > 0.7
            ]
            
            # Analyze for distress indicators
            distress_analysis = await self._analyze_distress_indicators(image_data, person_detections)
            
            return {
                "persons_detected": len(person_detections),
                "distress_indicators": distress_analysis,
                "detections": person_detections,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Person in distress detection failed: {e}")
            raise
    
    async def _analyze_distress_indicators(self, image_data: bytes, detections: List[Dict]) -> Dict[str, Any]:
        """Analyze image for distress indicators"""
        # This is a simplified analysis - in production, this would use
        # more sophisticated computer vision techniques
        
        indicators = {
            "motion_blur": False,
            "unusual_positioning": False,
            "environmental_hazards": False,
            "confidence_score": 0.0
        }
        
        if detections:
            # Simple heuristic: multiple people might indicate rescue situation
            if len(detections) > 1:
                indicators["unusual_positioning"] = True
                indicators["confidence_score"] += 0.3
            
            # High confidence detections
            high_conf_detections = [d for d in detections if d["confidence"] > 0.8]
            if high_conf_detections:
                indicators["confidence_score"] += 0.4
        
        return indicators
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_type": self.model_type,
            "device": self.device if self.model_type == "pytorch" else "cpu",
            "available_classes": len(self.detection_classes) if self.model_type == "pytorch" else "variable",
            "pytorch_available": PYTORCH_AVAILABLE,
            "yolo_available": YOLO_AVAILABLE,
            "opencv_available": OPENCV_AVAILABLE,
            "status": "ready" if self.model else "not_initialized"
        }

# Global instance
computer_vision = AdvancedComputerVision()