"""
Mission service layer for business logic and database operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from ..models.mission import Mission, MissionStatus, MissionPriority
from ..models.discovery import Discovery
from ..ai.learning import LearningSystem
from ..core.config import settings

class MissionService:
    """Service for mission management operations."""
    
    def __init__(self):
        self.learning_system = None  # Will be injected
    
    async def get_missions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Mission]:
        """Get list of missions with optional filtering."""
        query = db.query(Mission)
        
        if status:
            try:
                status_enum = MissionStatus(status)
                query = query.filter(Mission.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        if priority:
            try:
                priority_enum = MissionPriority(priority)
                query = query.filter(Mission.priority == priority_enum)
            except ValueError:
                pass  # Invalid priority, ignore filter
        
        return query.order_by(Mission.created_at.desc()).offset(skip).limit(limit).all()
    
    async def get_mission_by_id(self, db: Session, mission_id: str) -> Optional[Mission]:
        """Get a mission by its ID."""
        return db.query(Mission).filter(Mission.mission_id == mission_id).first()
    
    async def create_mission(self, db: Session, mission_data: Dict[str, Any]) -> Mission:
        """Create a new mission."""
        # Generate mission ID if not provided
        if "mission_id" not in mission_data:
            mission_data["mission_id"] = f"SAR_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Extract parameters for database fields
        parameters = mission_data.get("parameters", {})
        
        mission = Mission(
            mission_id=mission_data["mission_id"],
            name=mission_data["name"],
            description=mission_data.get("description", ""),
            status=MissionStatus.PLANNING,
            priority=MissionPriority(mission_data.get("priority", "medium")),
            parameters=parameters,
            
            # Extract search area information
            search_area_name=parameters.get("search_area_name"),
            center_latitude=parameters.get("center_latitude"),
            center_longitude=parameters.get("center_longitude"),
            area_size_km2=parameters.get("area_size_km2"),
            boundary_coordinates=parameters.get("boundary_coordinates"),
            
            # Extract target information
            target_description=parameters.get("target_description"),
            target_type=parameters.get("target_type"),
            last_known_latitude=parameters.get("last_known_latitude"),
            last_known_longitude=parameters.get("last_known_longitude"),
            
            # Extract resource allocation
            num_drones=parameters.get("num_drones", 1),
            search_altitude=parameters.get("search_altitude", settings.default_search_altitude),
            
            # Extract environmental conditions
            weather_conditions=parameters.get("weather_conditions"),
            terrain_type=parameters.get("terrain_type"),
            visibility_km=parameters.get("visibility_km"),
            wind_speed_ms=parameters.get("wind_speed_ms"),
            
            # Extract constraints
            max_duration_hours=parameters.get("max_duration_hours", settings.max_mission_duration / 3600),
            battery_reserve_percentage=parameters.get("battery_reserve_percentage", settings.min_battery_level),
            max_wind_speed_ms=parameters.get("max_wind_speed_ms", settings.max_wind_speed),
            
            # Extract contact information
            operator_name=mission_data.get("operator_name"),
            operator_contact=mission_data.get("operator_contact"),
            emergency_contact=mission_data.get("emergency_contact"),
            
            # AI data
            ai_recommendations=mission_data.get("ai_recommendations"),
            conversation_history=mission_data.get("conversation_history")
        )
        
        db.add(mission)
        db.commit()
        db.refresh(mission)
        
        return mission
    
    async def update_mission(self, db: Session, mission_id: str, update_data: Dict[str, Any]) -> Optional[Mission]:
        """Update mission parameters and status."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(mission, field):
                if field == "status" and isinstance(value, str):
                    try:
                        setattr(mission, field, MissionStatus(value))
                    except ValueError:
                        continue
                elif field == "priority" and isinstance(value, str):
                    try:
                        setattr(mission, field, MissionPriority(value))
                    except ValueError:
                        continue
                else:
                    setattr(mission, field, value)
        
        mission.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(mission)
        
        return mission
    
    async def start_mission(self, db: Session, mission_id: str) -> Optional[Mission]:
        """Start a mission."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission or mission.status != MissionStatus.READY:
            return None
        
        mission.status = MissionStatus.ACTIVE
        mission.started_at = datetime.utcnow()
        mission.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(mission)
        
        return mission
    
    async def pause_mission(self, db: Session, mission_id: str) -> Optional[Mission]:
        """Pause an active mission."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission or mission.status != MissionStatus.ACTIVE:
            return None
        
        mission.status = MissionStatus.PAUSED
        mission.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(mission)
        
        return mission
    
    async def resume_mission(self, db: Session, mission_id: str) -> Optional[Mission]:
        """Resume a paused mission."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission or mission.status != MissionStatus.PAUSED:
            return None
        
        mission.status = MissionStatus.ACTIVE
        mission.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(mission)
        
        return mission
    
    async def abort_mission(self, db: Session, mission_id: str, reason: str) -> Optional[Mission]:
        """Abort a mission."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission:
            return None
        
        mission.status = MissionStatus.ABORTED
        mission.completed_at = datetime.utcnow()
        mission.updated_at = datetime.utcnow()
        
        # Store abort reason in parameters
        if not mission.parameters:
            mission.parameters = {}
        mission.parameters["abort_reason"] = reason
        mission.parameters["aborted_at"] = datetime.utcnow().isoformat()
        
        db.commit()
        db.refresh(mission)
        
        return mission
    
    async def complete_mission(self, db: Session, mission_id: str, completion_data: Dict[str, Any]) -> Optional[Mission]:
        """Mark a mission as completed."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission:
            return None
        
        mission.status = MissionStatus.COMPLETED
        mission.completed_at = datetime.utcnow()
        mission.updated_at = datetime.utcnow()
        
        # Update success metrics
        mission.success_rating = completion_data.get("success_rating", 0.5)
        mission.lessons_learned = completion_data.get("lessons_learned", [])
        
        # Update final progress
        mission.progress_percentage = 100.0
        
        db.commit()
        db.refresh(mission)
        
        # Record learning data
        if self.learning_system:
            await self._record_mission_learning(mission, completion_data)
        
        return mission
    
    async def get_mission_status(self, db: Session, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time mission status."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission:
            return None
        
        # Get assigned drones status
        assigned_drones = mission.assigned_drones or []
        drone_statuses = []
        
        # This would typically query drone service for current status
        for drone_id in assigned_drones:
            drone_statuses.append({
                "drone_id": drone_id,
                "status": "active",  # Placeholder
                "battery": 75.0,     # Placeholder
                "location": {"lat": 0.0, "lon": 0.0}  # Placeholder
            })
        
        return {
            "mission_id": mission.mission_id,
            "status": mission.status.value,
            "progress_percentage": mission.progress_percentage,
            "area_covered_km2": mission.area_covered_km2,
            "flight_time_minutes": mission.flight_time_minutes,
            "discoveries_count": mission.discoveries_count,
            "assigned_drones": drone_statuses,
            "weather_conditions": mission.weather_conditions or {},
            "started_at": mission.started_at.isoformat() if mission.started_at else None,
            "duration_minutes": self._calculate_duration_minutes(mission),
            "estimated_completion": self._estimate_completion_time(mission)
        }
    
    async def get_mission_progress(self, db: Session, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed mission progress."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission:
            return None
        
        # Calculate progress metrics
        total_area = mission.area_size_km2 or 1.0
        coverage_percentage = (mission.area_covered_km2 or 0.0) / total_area * 100
        
        return {
            "mission_id": mission.mission_id,
            "overall_progress": mission.progress_percentage,
            "area_coverage": {
                "total_area_km2": total_area,
                "covered_area_km2": mission.area_covered_km2 or 0.0,
                "coverage_percentage": min(100.0, coverage_percentage)
            },
            "time_metrics": {
                "flight_time_minutes": mission.flight_time_minutes or 0.0,
                "duration_minutes": self._calculate_duration_minutes(mission),
                "estimated_remaining_minutes": self._estimate_remaining_time(mission)
            },
            "discoveries": {
                "total_count": mission.discoveries_count,
                "high_confidence_count": 0,  # Would query discovery service
                "confirmed_count": 0         # Would query discovery service
            },
            "efficiency_metrics": {
                "area_per_hour": self._calculate_area_efficiency(mission),
                "battery_usage_rate": self._calculate_battery_usage(mission),
                "success_probability": self._estimate_success_probability(mission)
            }
        }
    
    async def get_mission_discoveries(
        self,
        db: Session,
        mission_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get discoveries made during the mission."""
        discoveries = db.query(Discovery).filter(
            Discovery.mission_id == mission_id
        ).order_by(Discovery.detected_at.desc()).offset(skip).limit(limit).all()
        
        return [discovery.to_dict() for discovery in discoveries]
    
    async def add_discovery(self, db: Session, mission_id: str, discovery_data: Dict[str, Any]) -> Discovery:
        """Add a new discovery to the mission."""
        from ..models.discovery import DiscoveryType, DiscoveryStatus, ConfidenceLevel
        
        # Generate discovery ID
        discovery_id = f"DISC_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        discovery = Discovery(
            discovery_id=discovery_id,
            mission_id=mission_id,
            drone_id=discovery_data.get("drone_id"),
            discovery_type=DiscoveryType(discovery_data.get("type", "unknown")),
            status=DiscoveryStatus.DETECTED,
            confidence_level=Discovery.get_confidence_level_from_score(
                discovery_data.get("confidence", 0.5)
            ),
            ai_confidence_score=discovery_data.get("confidence", 0.5),
            latitude=discovery_data["latitude"],
            longitude=discovery_data["longitude"],
            altitude=discovery_data.get("altitude", 0.0),
            detected_at=datetime.utcnow(),
            detection_method=discovery_data.get("detection_method", "ai"),
            description=discovery_data.get("description"),
            ai_description=discovery_data.get("ai_description")
        )
        
        db.add(discovery)
        
        # Update mission discovery count
        mission = await self.get_mission_by_id(db, mission_id)
        if mission:
            mission.add_discovery()
        
        db.commit()
        db.refresh(discovery)
        
        return discovery
    
    async def update_progress(self, db: Session, mission_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update mission progress."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission:
            return False
        
        # Update progress fields
        if "progress_percentage" in progress_data:
            mission.update_progress(
                progress_data["progress_percentage"],
                progress_data.get("area_covered_km2"),
                progress_data.get("flight_time_minutes")
            )
        
        db.commit()
        return True
    
    async def get_mission_analytics(self, db: Session, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get mission analytics and performance metrics."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission:
            return None
        
        return {
            "mission_id": mission.mission_id,
            "performance": {
                "efficiency_score": mission.get_efficiency_score(),
                "success_rating": mission.success_rating,
                "duration_hours": mission.get_duration_hours(),
                "area_coverage_rate": self._calculate_area_efficiency(mission)
            },
            "resource_utilization": {
                "drones_deployed": len(mission.assigned_drones or []),
                "flight_hours": (mission.flight_time_minutes or 0) / 60,
                "cost_estimate": self._estimate_mission_cost(mission)
            },
            "outcomes": {
                "discoveries_made": mission.discoveries_count,
                "targets_found": 0,  # Would need to analyze discoveries
                "false_positives": 0,  # Would need to analyze discoveries
                "mission_success": mission.status == MissionStatus.COMPLETED
            },
            "lessons_learned": mission.lessons_learned or []
        }
    
    async def get_ai_recommendations(
        self,
        db: Session,
        mission_id: str,
        current_situation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI recommendations for mission optimization."""
        mission = await self.get_mission_by_id(db, mission_id)
        if not mission:
            return {"recommendations": [], "confidence": 0.0}
        
        if not self.learning_system:
            return {"recommendations": ["AI learning system not available"], "confidence": 0.0}
        
        # Combine mission parameters with current situation
        context = {
            **mission.to_dict(),
            **current_situation
        }
        
        return await self.learning_system.get_mission_recommendations(context)
    
    def _calculate_duration_minutes(self, mission: Mission) -> Optional[float]:
        """Calculate mission duration in minutes."""
        if not mission.started_at:
            return None
        
        end_time = mission.completed_at or datetime.utcnow()
        duration = end_time - mission.started_at
        return duration.total_seconds() / 60
    
    def _estimate_completion_time(self, mission: Mission) -> Optional[str]:
        """Estimate mission completion time."""
        if mission.is_completed() or not mission.started_at:
            return None
        
        progress = mission.progress_percentage or 0.0
        if progress <= 0:
            return None
        
        duration_minutes = self._calculate_duration_minutes(mission)
        if not duration_minutes:
            return None
        
        estimated_total_minutes = duration_minutes * (100.0 / progress)
        estimated_completion = mission.started_at + timedelta(minutes=estimated_total_minutes)
        
        return estimated_completion.isoformat()
    
    def _estimate_remaining_time(self, mission: Mission) -> Optional[float]:
        """Estimate remaining mission time in minutes."""
        if mission.is_completed():
            return 0.0
        
        completion_time_str = self._estimate_completion_time(mission)
        if not completion_time_str:
            return None
        
        completion_time = datetime.fromisoformat(completion_time_str.replace('Z', '+00:00'))
        remaining = completion_time - datetime.utcnow()
        
        return max(0.0, remaining.total_seconds() / 60)
    
    def _calculate_area_efficiency(self, mission: Mission) -> Optional[float]:
        """Calculate area coverage efficiency (km²/hour)."""
        duration_hours = mission.get_duration_hours()
        if not duration_hours or duration_hours <= 0:
            return None
        
        area_covered = mission.area_covered_km2 or 0.0
        return area_covered / duration_hours
    
    def _calculate_battery_usage(self, mission: Mission) -> Optional[float]:
        """Calculate battery usage rate."""
        # This would typically integrate with drone service
        # Placeholder implementation
        return 0.5  # 50% per hour
    
    def _estimate_success_probability(self, mission: Mission) -> float:
        """Estimate mission success probability."""
        # Simple heuristic based on progress and discoveries
        progress_factor = (mission.progress_percentage or 0.0) / 100.0
        discovery_factor = min(1.0, (mission.discoveries_count or 0) / 5.0)
        
        return (progress_factor * 0.7) + (discovery_factor * 0.3)
    
    def _estimate_mission_cost(self, mission: Mission) -> float:
        """Estimate mission cost."""
        # Simple cost estimation
        base_cost = 100.0  # Base mission cost
        drone_cost = len(mission.assigned_drones or []) * 50.0  # Per drone cost
        flight_time_cost = (mission.flight_time_minutes or 0) * 2.0  # Per minute cost
        
        return base_cost + drone_cost + flight_time_cost
    
    async def _record_mission_learning(self, mission: Mission, completion_data: Dict[str, Any]):
        """Record mission data for AI learning."""
        if not self.learning_system:
            return
        
        # Prepare mission parameters
        mission_parameters = mission.to_dict()
        
        # Prepare outcome data
        outcome_data = {
            "status": mission.status.value,
            "success_rating": mission.success_rating,
            "discoveries_count": mission.discoveries_count,
            "area_covered_km2": mission.area_covered_km2,
            "duration_hours": mission.get_duration_hours(),
            "completion_data": completion_data
        }
        
        # Prepare performance metrics
        performance_metrics = {
            "efficiency_score": mission.get_efficiency_score() or 0.0,
            "area_efficiency": self._calculate_area_efficiency(mission) or 0.0,
            "success_probability": self._estimate_success_probability(mission),
            "cost_effectiveness": (mission.discoveries_count or 0) / max(1.0, self._estimate_mission_cost(mission))
        }
        
        # Record learning
        await self.learning_system.record_mission_outcome(
            mission.mission_id,
            mission_parameters,
            outcome_data,
            performance_metrics
        )