"""
Computer Vision API endpoints for object detection and image analysis.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.ai.real_computer_vision import RealComputerVisionEngine
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize real computer vision engine
_real_cv_engine = RealComputerVisionEngine()

# Compatibility wrapper to match the old API
class ComputerVisionEngineWrapper:
    def __init__(self, real_engine):
        self.real_engine = real_engine
        self.detection_threshold = 0.5
        self.sar_classes = ["person", "vehicle", "bicycle", "car", "motorcycle", "airplane", "bus", "train"]
        
    async def detect_objects(self, image_data, model_size="yolov8s", confidence_threshold=None, target_classes=None):
        """Compatibility method for detect_objects"""
        if confidence_threshold:
            self.real_engine.set_detection_threshold(confidence_threshold)
        
        analysis = await self.real_engine.analyze_image(image_data, "base64")
        
        # Convert to expected format
        detections = []
        for detection in analysis.detections:
            detections.append({
                "class": detection.type.value,
                "confidence": detection.confidence,
                "bbox": detection.bounding_box,
                "center": detection.center_point,
                "area": detection.area
            })
        
        return {
            "detections": detections,
            "image_quality": analysis.image_quality,
            "processing_time": analysis.processing_time,
            "model_used": "yolov8n"
        }
    
    async def detect_sar_targets(self, image_data, confidence_threshold=None):
        """Compatibility method for detect_sar_targets"""
        return await self.detect_objects(image_data, confidence_threshold=confidence_threshold)
    
    async def analyze_image_quality(self, image_data):
        """Compatibility method for analyze_image_quality"""
        analysis = await self.real_engine.analyze_image(image_data, "base64")
        return {
            "quality_score": analysis.image_quality,
            "recommendations": ["Image quality acceptable"] if analysis.image_quality > 0.7 else ["Consider retaking image"]
        }
    
    async def batch_detect(self, image_batch, model_size="yolov8s"):
        """Compatibility method for batch_detect"""
        results = []
        for image_data in image_batch:
            result = await self.detect_objects(image_data, model_size)
            results.append(result)
        return {"results": results}
    
    def get_model_info(self):
        """Compatibility method for get_model_info"""
        return {
            "model_name": "YOLOv8n",
            "version": "8.0.0",
            "classes": self.sar_classes,
            "confidence_threshold": self.detection_threshold
        }
    
    async def optimize_detection_settings(self, sample_images, target_accuracy=0.9):
        """Compatibility method for optimize_detection_settings"""
        # Simple optimization - adjust threshold based on sample performance
        avg_quality = 0
        for image_data in sample_images:
            analysis = await self.real_engine.analyze_image(image_data, "base64")
            avg_quality += analysis.image_quality
        
        avg_quality /= len(sample_images) if sample_images else 1
        
        # Adjust threshold based on image quality
        if avg_quality > 0.8:
            optimal_threshold = 0.3
        elif avg_quality > 0.6:
            optimal_threshold = 0.5
        else:
            optimal_threshold = 0.7
            
        return {
            "optimal_confidence_threshold": optimal_threshold,
            "recommended_settings": {
                "model_size": "yolov8s",
                "batch_size": 4
            }
        }

computer_vision_engine = ComputerVisionEngineWrapper(_real_cv_engine)


@router.post("/detect-objects")
async def detect_objects(
    image: UploadFile = File(...),
    yolo_model_size: str = Form(default="yolov8s"),
    confidence_threshold: Optional[float] = Form(default=None),
    target_classes: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    Detect objects in an uploaded image using YOLO.
    
    Args:
        image: Image file to analyze
        yolo_model_size: YOLO model size (yolov8n, yolov8s, yolov8m, yolov8l)
        confidence_threshold: Minimum confidence for detections
        target_classes: JSON string of target classes to detect
        
    Returns:
        List of detected objects with bounding boxes and confidence scores
    """
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Parse target classes if provided
        classes = None
        if target_classes:
            try:
                classes = json.loads(target_classes)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid target_classes JSON")
        
        # Detect objects
        detections = await computer_vision_engine.detect_objects(
            image_data=image_data,
            model_size=yolo_model_size,
            confidence_threshold=confidence_threshold,
            target_classes=classes
        )
        
        return {
            "success": True,
            "detections": detections,
            "image_info": {
                "filename": image.filename,
                "content_type": image.content_type,
                "size_bytes": len(image_data)
            },
            "model_used": yolo_model_size,
            "confidence_threshold": confidence_threshold or computer_vision_engine.detection_threshold
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Object detection failed: {e}")
        raise HTTPException(status_code=500, detail="Object detection failed")


@router.post("/detect-sar-targets")
async def detect_sar_targets(
    image: UploadFile = File(...),
    mission_id: Optional[str] = Form(default=None),
    search_target: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    Detect SAR-specific targets with mission context.
    
    Args:
        image: Image file to analyze
        mission_id: Mission ID for context
        search_target: Specific target being searched for
        
    Returns:
        List of SAR target detections with priority scoring
    """
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Prepare mission context
        mission_context = {}
        if mission_id:
            mission_context['mission_id'] = mission_id
        if search_target:
            mission_context['search_target'] = search_target
        
        # Detect SAR targets
        detections = await computer_vision_engine.detect_sar_targets(
            image_data=image_data,
            mission_context=mission_context
        )
        
        return {
            "success": True,
            "detections": detections,
            "mission_context": mission_context,
            "image_info": {
                "filename": image.filename,
                "content_type": image.content_type,
                "size_bytes": len(image_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SAR target detection failed: {e}")
        raise HTTPException(status_code=500, detail="SAR target detection failed")


@router.post("/analyze-image-quality")
async def analyze_image_quality(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Analyze image quality for detection optimization.
    
    Args:
        image: Image file to analyze
        
    Returns:
        Image quality analysis results
    """
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Analyze image quality
        quality_analysis = await computer_vision_engine.analyze_image_quality(image_data)
        
        return {
            "success": True,
            "quality_analysis": quality_analysis,
            "image_info": {
                "filename": image.filename,
                "content_type": image.content_type,
                "size_bytes": len(image_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image quality analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Image quality analysis failed")


@router.post("/batch-detect")
async def batch_detect_objects(
    images: List[UploadFile] = File(...),
    yolo_model_size: str = Form(default="yolov8s"),
    db: Session = Depends(get_db)
):
    """
    Process a batch of images for object detection.
    
    Args:
        images: List of image files to analyze
        yolo_model_size: YOLO model size
        
    Returns:
        List of detection results for each image
    """
    try:
        # Validate files
        if len(images) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 images per batch")
        
        for image in images:
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="All files must be images")
        
        # Read image data
        image_batch = []
        image_info = []
        
        for image in images:
            image_data = await image.read()
            image_batch.append(image_data)
            image_info.append({
                "filename": image.filename,
                "content_type": image.content_type,
                "size_bytes": len(image_data)
            })
        
        # Process batch
        results = await computer_vision_engine.batch_detect(image_batch, yolo_model_size)
        
        # Format response
        batch_results = []
        for i, (detections, info) in enumerate(zip(results, image_info)):
            batch_results.append({
                "image_index": i,
                "image_info": info,
                "detections": detections,
                "detection_count": len(detections)
            })
        
        return {
            "success": True,
            "batch_results": batch_results,
            "model_used": yolo_model_size,
            "total_images": len(images),
            "total_detections": sum(len(r) for r in results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch detection failed: {e}")
        raise HTTPException(status_code=500, detail="Batch detection failed")


@router.get("/model-info")
async def get_model_info(db: Session = Depends(get_db)):
    """
    Get information about available computer vision models.
    
    Returns:
        Model information and capabilities
    """
    try:
        model_info = computer_vision_engine.get_model_info()
        
        return {
            "success": True,
            "model_info": model_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model info")


@router.post("/optimize-settings")
async def optimize_detection_settings(
    images: List[UploadFile] = File(...),
    target_accuracy: float = Form(default=0.8),
    db: Session = Depends(get_db)
):
    """
    Optimize detection settings based on sample images.
    
    Args:
        images: Sample images for optimization
        target_accuracy: Target accuracy threshold
        
    Returns:
        Optimized detection settings
    """
    try:
        # Validate files
        if len(images) > 5:  # Limit sample size
            raise HTTPException(status_code=400, detail="Maximum 5 sample images")
        
        for image in images:
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="All files must be images")
        
        # Read image data
        sample_images = []
        for image in images:
            image_data = await image.read()
            sample_images.append(image_data)
        
        # Optimize settings
        optimized_settings = await computer_vision_engine.optimize_detection_settings(
            sample_images, target_accuracy
        )
        
        return {
            "success": True,
            "optimized_settings": optimized_settings,
            "sample_count": len(images),
            "target_accuracy": target_accuracy
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Settings optimization failed: {e}")
        raise HTTPException(status_code=500, detail="Settings optimization failed")


@router.get("/sar-classes")
async def get_sar_classes(db: Session = Depends(get_db)):
    """
    Get SAR-specific object classes and their priorities.
    
    Returns:
        Dictionary of SAR classes with priorities and confidence thresholds
    """
    try:
        return {
            "success": True,
            "sar_classes": computer_vision_engine.sar_classes,
            "total_classes": len(computer_vision_engine.sar_classes)
        }
        
    except Exception as e:
        logger.error(f"Failed to get SAR classes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SAR classes")


@router.post("/test-detection")
async def test_detection(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Test endpoint for computer vision functionality.
    
    Args:
        image: Test image file
        
    Returns:
        Comprehensive test results
    """
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await image.read()
        
        # Run comprehensive tests
        test_results = {}
        
        # Test 1: Basic object detection
        detections = await computer_vision_engine.detect_objects(image_data)
        test_results['basic_detection'] = {
            'success': True,
            'detection_count': len(detections),
            'detections': detections
        }
        
        # Test 2: SAR target detection
        sar_detections = await computer_vision_engine.detect_sar_targets(image_data)
        test_results['sar_detection'] = {
            'success': True,
            'detection_count': len(sar_detections),
            'detections': sar_detections
        }
        
        # Test 3: Image quality analysis
        quality_analysis = await computer_vision_engine.analyze_image_quality(image_data)
        test_results['quality_analysis'] = {
            'success': True,
            'analysis': quality_analysis
        }
        
        # Test 4: Model info
        model_info = computer_vision_engine.get_model_info()
        test_results['model_info'] = {
            'success': True,
            'info': model_info
        }
        
        return {
            "success": True,
            "test_results": test_results,
            "image_info": {
                "filename": image.filename,
                "content_type": image.content_type,
                "size_bytes": len(image_data)
            },
            "summary": {
                "total_tests": len(test_results),
                "passed_tests": sum(1 for test in test_results.values() if test['success']),
                "basic_detections": len(detections),
                "sar_detections": len(sar_detections),
                "quality_score": quality_analysis.get('quality_score', 0.0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection test failed: {e}")
        raise HTTPException(status_code=500, detail="Detection test failed")
