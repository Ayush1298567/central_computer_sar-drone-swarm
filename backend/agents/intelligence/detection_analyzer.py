"""
Detection Analyzer Agent
Analyzes drone detection data and findings
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from ..base_agent import BaseAgent
from ...services.ollama_service import ollama_service
from ...services.database import db_service

logger = logging.getLogger(__name__)

class DetectionAnalyzerAgent(BaseAgent):
    """Analyzes detection data from drones"""
    
    def __init__(self, redis_service, websocket_manager):
        super().__init__("detection_analyzer", redis_service, websocket_manager)
        self.detection_history: List[Dict[str, Any]] = []
        self.analysis_patterns: Dict[str, Any] = {}
    
    async def start_agent(self) -> None:
        """Start the detection analyzer"""
        await self.subscribe_to_channel("drone.detection")
        await self.subscribe_to_channel("drone.thermal_data")
        await self.subscribe_to_channel("drone.visual_data")
        await self.subscribe_to_channel("mission.analysis_request")
        logger.info("Detection Analyzer Agent started")
    
    async def stop_agent(self) -> None:
        """Stop the detection analyzer"""
        logger.info("Detection Analyzer Agent stopped")
    
    async def process_message(self, channel: str, message: Any) -> None:
        """Process incoming messages"""
        try:
            if channel == "drone.detection":
                await self._handle_detection_data(message)
            elif channel == "drone.thermal_data":
                await self._handle_thermal_data(message)
            elif channel == "drone.visual_data":
                await self._handle_visual_data(message)
            elif channel == "mission.analysis_request":
                await self._handle_analysis_request(message)
        except Exception as e:
            logger.error(f"Error processing message in {channel}: {e}")
    
    async def _handle_detection_data(self, message: Dict[str, Any]) -> None:
        """Handle detection data from drone"""
        detection = message.get("detection", {})
        drone_id = message.get("drone_id")
        mission_id = message.get("mission_id")
        
        logger.info(f"Analyzing detection from drone {drone_id}")
        
        # Analyze the detection
        analysis = await self._analyze_detection(detection, drone_id, mission_id)
        
        if analysis:
            # Store detection and analysis
            detection_record = {
                "detection": detection,
                "analysis": analysis,
                "drone_id": drone_id,
                "mission_id": mission_id,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            self.detection_history.append(detection_record)
            
            # Save to database
            await self._save_detection_to_db(detection_record)
            
            # Publish analysis result
            await self.publish_message("detection.analysis_complete", {
                "drone_id": drone_id,
                "mission_id": mission_id,
                "detection": detection,
                "analysis": analysis
            })
            
            # Send to WebSocket
            await self.send_websocket_message("detection_analysis", {
                "drone_id": drone_id,
                "mission_id": mission_id,
                "detection": detection,
                "analysis": analysis
            })
            
            # Check if this is a significant finding
            if analysis.get("significance", "low") in ["high", "critical"]:
                await self._handle_significant_finding(detection_record)
    
    async def _handle_thermal_data(self, message: Dict[str, Any]) -> None:
        """Handle thermal imaging data"""
        thermal_data = message.get("thermal_data", {})
        drone_id = message.get("drone_id")
        mission_id = message.get("mission_id")
        
        logger.info(f"Analyzing thermal data from drone {drone_id}")
        
        # Analyze thermal data for heat signatures
        analysis = await self._analyze_thermal_data(thermal_data, drone_id, mission_id)
        
        if analysis and analysis.get("heat_signatures"):
            # Create detection record
            detection = {
                "type": "thermal",
                "data": thermal_data,
                "analysis": analysis,
                "confidence": analysis.get("confidence", 0)
            }
            
            await self._handle_detection_data({
                "detection": detection,
                "drone_id": drone_id,
                "mission_id": mission_id
            })
    
    async def _handle_visual_data(self, message: Dict[str, Any]) -> None:
        """Handle visual imaging data"""
        visual_data = message.get("visual_data", {})
        drone_id = message.get("drone_id")
        mission_id = message.get("mission_id")
        
        logger.info(f"Analyzing visual data from drone {drone_id}")
        
        # Analyze visual data for objects/people
        analysis = await self._analyze_visual_data(visual_data, drone_id, mission_id)
        
        if analysis and analysis.get("objects_detected"):
            # Create detection record
            detection = {
                "type": "visual",
                "data": visual_data,
                "analysis": analysis,
                "confidence": analysis.get("confidence", 0)
            }
            
            await self._handle_detection_data({
                "detection": detection,
                "drone_id": drone_id,
                "mission_id": mission_id
            })
    
    async def _handle_analysis_request(self, message: Dict[str, Any]) -> None:
        """Handle analysis request for mission data"""
        mission_id = message.get("mission_id")
        analysis_type = message.get("analysis_type", "general")
        
        logger.info(f"Performing {analysis_type} analysis for mission {mission_id}")
        
        # Get all detections for this mission
        mission_detections = [
            d for d in self.detection_history 
            if d.get("mission_id") == mission_id
        ]
        
        if not mission_detections:
            logger.warning(f"No detections found for mission {mission_id}")
            return
        
        # Perform analysis based on type
        if analysis_type == "pattern_analysis":
            analysis_result = await self._perform_pattern_analysis(mission_detections)
        elif analysis_type == "coverage_analysis":
            analysis_result = await self._perform_coverage_analysis(mission_detections)
        elif analysis_type == "significance_analysis":
            analysis_result = await self._perform_significance_analysis(mission_detections)
        else:
            analysis_result = await self._perform_general_analysis(mission_detections)
        
        # Publish analysis result
        await self.publish_message("mission.analysis_complete", {
            "mission_id": mission_id,
            "analysis_type": analysis_type,
            "result": analysis_result
        })
    
    async def _analyze_detection(self, detection: Dict[str, Any], drone_id: int, mission_id: int) -> Optional[Dict[str, Any]]:
        """Analyze a detection using LLM"""
        try:
            detection_type = detection.get("type", "unknown")
            confidence = detection.get("confidence", 0)
            data = detection.get("data", {})
            
            # Use Ollama to analyze the detection
            analysis = await ollama_service.analyze_discovery({
                "type": detection_type,
                "confidence": confidence,
                "data": data,
                "location": data.get("location", "Unknown")
            })
            
            # Enhance analysis with additional processing
            enhanced_analysis = await self._enhance_analysis(analysis, detection, drone_id, mission_id)
            
            return enhanced_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing detection: {e}")
            return self._create_fallback_analysis(detection)
    
    async def _analyze_thermal_data(self, thermal_data: Dict[str, Any], drone_id: int, mission_id: int) -> Optional[Dict[str, Any]]:
        """Analyze thermal imaging data"""
        try:
            # Extract temperature data
            temperature_map = thermal_data.get("temperature_map", [])
            ambient_temp = thermal_data.get("ambient_temperature", 20)
            
            # Find heat signatures above ambient
            heat_signatures = []
            for i, row in enumerate(temperature_map):
                for j, temp in enumerate(row):
                    if temp > ambient_temp + 5:  # 5°C above ambient
                        heat_signatures.append({
                            "x": j,
                            "y": i,
                            "temperature": temp,
                            "difference": temp - ambient_temp
                        })
            
            if heat_signatures:
                # Calculate confidence based on temperature difference
                max_diff = max(sig["difference"] for sig in heat_signatures)
                confidence = min(100, int((max_diff / 20) * 100))  # Scale to 0-100
                
                return {
                    "heat_signatures": heat_signatures,
                    "confidence": confidence,
                    "analysis_type": "thermal",
                    "significance": "high" if confidence > 70 else "medium" if confidence > 40 else "low"
                }
        
        except Exception as e:
            logger.error(f"Error analyzing thermal data: {e}")
        
        return None
    
    async def _analyze_visual_data(self, visual_data: Dict[str, Any], drone_id: int, mission_id: int) -> Optional[Dict[str, Any]]:
        """Analyze visual imaging data"""
        try:
            # Simulate object detection analysis
            # In a real system, this would use computer vision models
            
            image_quality = visual_data.get("quality", "unknown")
            resolution = visual_data.get("resolution", "unknown")
            
            # Simulate detection based on image quality
            objects_detected = []
            confidence = 0
            
            if image_quality == "high":
                # Simulate high-quality detection
                objects_detected = [
                    {"type": "person", "confidence": 85, "bbox": [100, 100, 200, 300]},
                    {"type": "structure", "confidence": 90, "bbox": [300, 200, 400, 400]}
                ]
                confidence = 85
            elif image_quality == "medium":
                # Simulate medium-quality detection
                objects_detected = [
                    {"type": "person", "confidence": 60, "bbox": [150, 120, 180, 280]}
                ]
                confidence = 60
            else:
                # Low quality or unknown
                confidence = 30
            
            if objects_detected:
                return {
                    "objects_detected": objects_detected,
                    "confidence": confidence,
                    "analysis_type": "visual",
                    "significance": "high" if confidence > 70 else "medium" if confidence > 40 else "low"
                }
        
        except Exception as e:
            logger.error(f"Error analyzing visual data: {e}")
        
        return None
    
    async def _enhance_analysis(self, base_analysis: Dict[str, Any], detection: Dict[str, Any], 
                               drone_id: int, mission_id: int) -> Dict[str, Any]:
        """Enhance analysis with additional processing"""
        enhanced = base_analysis.copy()
        
        # Add metadata
        enhanced["drone_id"] = drone_id
        enhanced["mission_id"] = mission_id
        enhanced["timestamp"] = asyncio.get_event_loop().time()
        enhanced["detection_id"] = f"det_{drone_id}_{asyncio.get_event_loop().time()}"
        
        # Calculate significance score
        confidence = enhanced.get("confidence", 0)
        likelihood = enhanced.get("likelihood", "medium")
        
        significance_score = 0
        if likelihood == "high":
            significance_score = confidence
        elif likelihood == "medium":
            significance_score = confidence * 0.7
        else:
            significance_score = confidence * 0.4
        
        enhanced["significance_score"] = significance_score
        enhanced["significance"] = "critical" if significance_score > 80 else "high" if significance_score > 60 else "medium" if significance_score > 30 else "low"
        
        # Add recommended actions
        enhanced["recommended_actions"] = await self._generate_recommended_actions(enhanced)
        
        return enhanced
    
    async def _generate_recommended_actions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on analysis"""
        actions = []
        
        significance = analysis.get("significance", "low")
        detection_type = analysis.get("analysis_type", "unknown")
        
        if significance in ["critical", "high"]:
            actions.append("Immediate human verification required")
            actions.append("Alert rescue teams")
            actions.append("Mark location for priority investigation")
        
        if detection_type == "thermal" and analysis.get("heat_signatures"):
            actions.append("Investigate heat signatures with visual confirmation")
            actions.append("Check for survivors in thermal hotspots")
        
        if detection_type == "visual" and analysis.get("objects_detected"):
            actions.append("Analyze detected objects for survivor identification")
            actions.append("Take additional high-resolution images")
        
        if analysis.get("confidence", 0) < 50:
            actions.append("Gather additional data for confirmation")
            actions.append("Request manual verification")
        
        return actions
    
    def _create_fallback_analysis(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis if LLM fails"""
        return {
            "analysis_type": detection.get("type", "unknown"),
            "confidence": detection.get("confidence", 0),
            "likelihood": "medium",
            "significance": "low",
            "significance_score": detection.get("confidence", 0) * 0.5,
            "recommended_actions": ["Manual verification required"],
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def _perform_pattern_analysis(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform pattern analysis on detections"""
        if not detections:
            return {"patterns": [], "insights": []}
        
        # Analyze detection patterns
        detection_types = [d["detection"]["type"] for d in detections]
        confidence_scores = [d["analysis"]["confidence"] for d in detections]
        
        # Find patterns
        patterns = {
            "most_common_type": max(set(detection_types), key=detection_types.count),
            "average_confidence": sum(confidence_scores) / len(confidence_scores),
            "high_confidence_detections": len([c for c in confidence_scores if c > 70]),
            "detection_frequency": len(detections)
        }
        
        return {
            "analysis_type": "pattern",
            "patterns": patterns,
            "insights": [
                f"Most common detection type: {patterns['most_common_type']}",
                f"Average confidence: {patterns['average_confidence']:.1f}%",
                f"High confidence detections: {patterns['high_confidence_detections']}"
            ]
        }
    
    async def _perform_coverage_analysis(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform coverage analysis on detections"""
        if not detections:
            return {"coverage": 0, "gaps": []}
        
        # Analyze spatial distribution
        locations = []
        for detection in detections:
            data = detection["detection"].get("data", {})
            if "location" in data:
                locations.append(data["location"])
        
        # Calculate coverage metrics
        coverage_analysis = {
            "total_detections": len(detections),
            "unique_locations": len(set(str(loc) for loc in locations)),
            "coverage_density": len(detections) / max(1, len(set(str(loc) for loc in locations))),
            "spatial_distribution": "clustered" if len(set(str(loc) for loc in locations)) < len(detections) * 0.8 else "distributed"
        }
        
        return {
            "analysis_type": "coverage",
            "coverage": coverage_analysis
        }
    
    async def _perform_significance_analysis(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform significance analysis on detections"""
        if not detections:
            return {"significance": "none", "critical_findings": 0}
        
        # Analyze significance levels
        significance_levels = [d["analysis"]["significance"] for d in detections]
        critical_count = significance_levels.count("critical")
        high_count = significance_levels.count("high")
        
        overall_significance = "low"
        if critical_count > 0:
            overall_significance = "critical"
        elif high_count > len(detections) * 0.3:
            overall_significance = "high"
        elif high_count > 0:
            overall_significance = "medium"
        
        return {
            "analysis_type": "significance",
            "significance": overall_significance,
            "critical_findings": critical_count,
            "high_significance_findings": high_count,
            "total_findings": len(detections)
        }
    
    async def _perform_general_analysis(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform general analysis on detections"""
        if not detections:
            return {"summary": "No detections found"}
        
        # General statistics
        total_detections = len(detections)
        avg_confidence = sum(d["analysis"]["confidence"] for d in detections) / total_detections
        high_confidence = len([d for d in detections if d["analysis"]["confidence"] > 70])
        
        return {
            "analysis_type": "general",
            "summary": f"Analyzed {total_detections} detections",
            "statistics": {
                "total_detections": total_detections,
                "average_confidence": avg_confidence,
                "high_confidence_detections": high_confidence,
                "confidence_rate": (high_confidence / total_detections) * 100
            }
        }
    
    async def _handle_significant_finding(self, detection_record: Dict[str, Any]) -> None:
        """Handle significant finding"""
        analysis = detection_record["analysis"]
        drone_id = detection_record["drone_id"]
        mission_id = detection_record["mission_id"]
        
        logger.warning(f"Significant finding from drone {drone_id}: {analysis.get('significance', 'unknown')}")
        
        # Create discovery record in database
        await self._create_discovery_record(detection_record)
        
        # Send alert
        await self.publish_message("discovery.significant_finding", {
            "drone_id": drone_id,
            "mission_id": mission_id,
            "detection": detection_record["detection"],
            "analysis": analysis
        })
        
        # Send to WebSocket
        await self.send_websocket_message("significant_finding", {
            "drone_id": drone_id,
            "mission_id": mission_id,
            "detection": detection_record["detection"],
            "analysis": analysis
        })
    
    async def _save_detection_to_db(self, detection_record: Dict[str, Any]) -> None:
        """Save detection record to database"""
        try:
            detection = detection_record["detection"]
            analysis = detection_record["analysis"]
            
            # Extract location
            location = detection.get("data", {}).get("location", {})
            lat = location.get("lat", 0)
            lng = location.get("lng", 0)
            
            # Create discovery record
            await db_service.create_discovery(
                mission_id=detection_record["mission_id"],
                drone_id=detection_record["drone_id"],
                lat=lat,
                lng=lng,
                discovery_type=detection.get("type", "unknown"),
                confidence=analysis.get("confidence", 0),
                description=json.dumps(analysis)
            )
        
        except Exception as e:
            logger.error(f"Error saving detection to database: {e}")
    
    async def _create_discovery_record(self, detection_record: Dict[str, Any]) -> None:
        """Create discovery record for significant finding"""
        await self._save_detection_to_db(detection_record)