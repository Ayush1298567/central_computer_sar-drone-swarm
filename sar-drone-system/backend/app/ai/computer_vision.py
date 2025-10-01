"""
Computer Vision Engine for object detection and analysis
"""
import logging
import cv2
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from PIL import Image
import torch
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Object detection result"""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]  # center_x, center_y
    area: int


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    detections: List[DetectionResult]
    image_metadata: Dict[str, Any]
    analysis_summary: str
    risk_level: str
    recommendations: List[str]


class ComputerVisionEngine:
    """Computer vision engine for SAR object detection"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or "./yolov8n.pt"
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.confidence_threshold = 0.5
        self.class_names = self._load_class_names()
        
        # SAR-specific object classes
        self.sar_classes = {
            "person": ["person"],
            "vehicle": ["car", "truck", "motorcycle", "bicycle"],
            "equipment": ["backpack", "bag", "suitcase", "chair"],
            "structure": ["building", "house", "bridge", "tower"],
            "animal": ["dog", "cat", "horse", "cow", "sheep"]
        }
        
        self._load_model()
    
    def _load_class_names(self) -> List[str]:
        """Load COCO class names"""
        return [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
            'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
            'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
            'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
            'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
            'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
            'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            if Path(self.model_path).exists():
                self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path)
                logger.info(f"Loaded YOLO model from {self.model_path}")
            else:
                # Use pre-trained model if custom model not available
                self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
                logger.info("Loaded pre-trained YOLOv5s model")
            
            self.model.to(self.device)
            self.model.eval()
            
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
    
    async def analyze_image(self, image_path: str) -> AnalysisResult:
        """Analyze image for SAR-relevant objects"""
        try:
            if not self.model:
                return self._create_error_result("Model not loaded")
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_array = np.array(image)
            
            # Run detection
            results = self.model(image_array)
            
            # Parse results
            detections = []
            if len(results.pred) > 0:
                for pred in results.pred[0]:
                    x1, y1, x2, y2, confidence, class_id = pred.cpu().numpy()
                    
                    if confidence >= self.confidence_threshold:
                        class_name = self.class_names[int(class_id)]
                        
                        # Filter for SAR-relevant objects
                        if self._is_sar_relevant(class_name):
                            detection = DetectionResult(
                                class_name=class_name,
                                confidence=float(confidence),
                                bbox=(int(x1), int(y1), int(x2), int(y2)),
                                center=(int((x1 + x2) / 2), int((y1 + y2) / 2)),
                                area=int((x2 - x1) * (y2 - y1))
                            )
                            detections.append(detection)
            
            # Generate analysis
            analysis_summary = self._generate_analysis_summary(detections)
            risk_level = self._assess_risk_level(detections)
            recommendations = self._generate_recommendations(detections)
            
            # Image metadata
            image_metadata = {
                "file_path": image_path,
                "dimensions": image.size,
                "format": image.format,
                "mode": image.mode
            }
            
            return AnalysisResult(
                detections=detections,
                image_metadata=image_metadata,
                analysis_summary=analysis_summary,
                risk_level=risk_level,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return self._create_error_result(str(e))
    
    async def analyze_video_frame(self, frame: np.ndarray) -> AnalysisResult:
        """Analyze video frame for objects"""
        try:
            if not self.model:
                return self._create_error_result("Model not loaded")
            
            # Convert frame to PIL Image
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # Run detection
            results = self.model(image)
            
            # Parse results (similar to analyze_image)
            detections = []
            if len(results.pred) > 0:
                for pred in results.pred[0]:
                    x1, y1, x2, y2, confidence, class_id = pred.cpu().numpy()
                    
                    if confidence >= self.confidence_threshold:
                        class_name = self.class_names[int(class_id)]
                        
                        if self._is_sar_relevant(class_name):
                            detection = DetectionResult(
                                class_name=class_name,
                                confidence=float(confidence),
                                bbox=(int(x1), int(y1), int(x2), int(y2)),
                                center=(int((x1 + x2) / 2), int((y1 + y2) / 2)),
                                area=int((x2 - x1) * (y2 - y1))
                            )
                            detections.append(detection)
            
            # Generate analysis
            analysis_summary = self._generate_analysis_summary(detections)
            risk_level = self._assess_risk_level(detections)
            recommendations = self._generate_recommendations(detections)
            
            # Frame metadata
            image_metadata = {
                "frame_shape": frame.shape,
                "timestamp": "real_time"
            }
            
            return AnalysisResult(
                detections=detections,
                image_metadata=image_metadata,
                analysis_summary=analysis_summary,
                risk_level=risk_level,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Video frame analysis failed: {e}")
            return self._create_error_result(str(e))
    
    def _is_sar_relevant(self, class_name: str) -> bool:
        """Check if detected object is relevant for SAR operations"""
        for category, classes in self.sar_classes.items():
            if class_name in classes:
                return True
        return False
    
    def _generate_analysis_summary(self, detections: List[DetectionResult]) -> str:
        """Generate human-readable analysis summary"""
        if not detections:
            return "No SAR-relevant objects detected in this image."
        
        # Group detections by category
        categories = {}
        for detection in detections:
            category = self._get_detection_category(detection.class_name)
            if category not in categories:
                categories[category] = []
            categories[category].append(detection)
        
        summary_parts = []
        for category, items in categories.items():
            count = len(items)
            avg_confidence = sum(d.confidence for d in items) / count
            summary_parts.append(f"{count} {category}(s) detected with {avg_confidence:.1%} average confidence")
        
        return "Analysis complete. " + "; ".join(summary_parts) + "."
    
    def _get_detection_category(self, class_name: str) -> str:
        """Get SAR category for detected class"""
        for category, classes in self.sar_classes.items():
            if class_name in classes:
                return category
        return "unknown"
    
    def _assess_risk_level(self, detections: List[DetectionResult]) -> str:
        """Assess risk level based on detections"""
        if not detections:
            return "low"
        
        # Count high-confidence detections
        high_confidence_detections = [d for d in detections if d.confidence > 0.8]
        person_detections = [d for d in detections if d.class_name == "person"]
        
        if person_detections and any(d.confidence > 0.8 for d in person_detections):
            return "high"  # Person detected with high confidence
        elif high_confidence_detections:
            return "medium"  # Objects detected with high confidence
        else:
            return "low"  # Low confidence detections
    
    def _generate_recommendations(self, detections: List[DetectionResult]) -> List[str]:
        """Generate action recommendations based on detections"""
        recommendations = []
        
        if not detections:
            recommendations.append("Continue search in current area")
            recommendations.append("Adjust search pattern if no progress")
            return recommendations
        
        # High confidence person detection
        person_detections = [d for d in detections if d.class_name == "person" and d.confidence > 0.8]
        if person_detections:
            recommendations.append("IMMEDIATE: Person detected - send rescue team")
            recommendations.append("Mark location with GPS coordinates")
            recommendations.append("Capture additional images for confirmation")
        
        # Vehicle or equipment detection
        vehicle_equipment = [d for d in detections if d.class_name in ["car", "truck", "backpack", "bag"]]
        if vehicle_equipment:
            recommendations.append("Investigate detected vehicles/equipment")
            recommendations.append("Check if associated with missing person")
        
        # General recommendations
        if len(detections) > 3:
            recommendations.append("High activity area - focus search here")
        
        recommendations.append("Document all findings with GPS coordinates")
        recommendations.append("Continue monitoring this area")
        
        return recommendations
    
    def _create_error_result(self, error_message: str) -> AnalysisResult:
        """Create error result"""
        return AnalysisResult(
            detections=[],
            image_metadata={"error": error_message},
            analysis_summary=f"Analysis failed: {error_message}",
            risk_level="unknown",
            recommendations=["Manual review required", "Check system configuration"]
        )
    
    async def batch_analyze_images(self, image_paths: List[str]) -> List[AnalysisResult]:
        """Analyze multiple images in batch"""
        results = []
        for image_path in image_paths:
            result = await self.analyze_image(image_path)
            results.append(result)
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and status"""
        return {
            "model_loaded": self.model is not None,
            "model_path": self.model_path,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "sar_classes": list(self.sar_classes.keys()),
            "total_classes": len(self.class_names)
        }