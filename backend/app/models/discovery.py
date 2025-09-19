"""
Discovery database models for tracking search findings.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base

class DiscoveryType(enum.Enum):
    """Types of discoveries that can be made during SAR missions."""
    PERSON = "person"
    VEHICLE = "vehicle"
    AIRCRAFT = "aircraft"
    DEBRIS = "debris"
    EQUIPMENT = "equipment"
    STRUCTURE = "structure"
    LANDMARK = "landmark"
    HAZARD = "hazard"
    WILDLIFE = "wildlife"
    UNKNOWN = "unknown"

class DiscoveryStatus(enum.Enum):
    """Status of discovery processing and verification."""
    DETECTED = "detected"           # AI/system detected something
    PENDING_REVIEW = "pending_review"  # Awaiting human review
    CONFIRMED = "confirmed"         # Human confirmed as valid discovery
    FALSE_POSITIVE = "false_positive"  # Determined to be false alarm
    INVESTIGATED = "investigated"   # Ground team investigated
    RESOLVED = "resolved"           # Discovery fully resolved

class ConfidenceLevel(enum.Enum):
    """Confidence levels for AI detections."""
    VERY_LOW = "very_low"      # 0.0 - 0.2
    LOW = "low"                # 0.2 - 0.4
    MEDIUM = "medium"          # 0.4 - 0.6
    HIGH = "high"              # 0.6 - 0.8
    VERY_HIGH = "very_high"    # 0.8 - 1.0

class Discovery(Base):
    """Discovery model representing findings during SAR missions."""
    
    __tablename__ = "discoveries"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    discovery_id = Column(String(50), unique=True, index=True, nullable=False)
    mission_id = Column(String(50), index=True, nullable=False)
    drone_id = Column(String(50), index=True, nullable=False)
    
    # Discovery classification
    discovery_type = Column(SQLEnum(DiscoveryType), nullable=False)
    status = Column(SQLEnum(DiscoveryStatus), default=DiscoveryStatus.DETECTED, nullable=False)
    confidence_level = Column(SQLEnum(ConfidenceLevel), nullable=False)
    ai_confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Location information
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    gps_accuracy_m = Column(Float)
    
    # Detection details
    detected_at = Column(DateTime(timezone=True), nullable=False)
    detection_method = Column(String(50))  # "visual", "thermal", "ai", "manual"
    detection_algorithm = Column(String(100))  # Specific AI algorithm used
    
    # Visual information
    image_path = Column(String(500))  # Path to discovery image
    video_path = Column(String(500))  # Path to discovery video
    thumbnail_path = Column(String(500))  # Path to thumbnail image
    
    # Bounding box coordinates (normalized 0-1)
    bbox_x = Column(Float)
    bbox_y = Column(Float)
    bbox_width = Column(Float)
    bbox_height = Column(Float)
    
    # Physical characteristics
    estimated_size_m = Column(Float)  # Estimated size in meters
    estimated_distance_m = Column(Float)  # Distance from drone
    object_color = Column(String(50))
    object_shape = Column(String(50))
    
    # Description and notes
    description = Column(Text)
    ai_description = Column(Text)  # AI-generated description
    human_notes = Column(Text)  # Human operator notes
    
    # Verification and review
    reviewed_by = Column(String(200))  # Name of reviewer
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    
    # Investigation details
    investigated = Column(Boolean, default=False)
    investigation_team = Column(String(200))
    investigation_date = Column(DateTime(timezone=True))
    investigation_result = Column(Text)
    
    # Priority and urgency
    priority_score = Column(Float, default=0.5)  # 0.0 to 1.0
    requires_immediate_attention = Column(Boolean, default=False)
    
    # Environmental context
    weather_conditions = Column(JSON)
    lighting_conditions = Column(String(50))  # "daylight", "twilight", "night"
    visibility_km = Column(Float)
    
    # Related discoveries
    related_discoveries = Column(JSON)  # List of related discovery IDs
    cluster_id = Column(String(50))  # For grouping related discoveries
    
    # Metadata
    raw_detection_data = Column(JSON)  # Raw AI detection output
    processing_metadata = Column(JSON)  # Processing pipeline info
    tags = Column(JSON)  # Searchable tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert discovery to dictionary."""
        return {
            "id": self.id,
            "discovery_id": self.discovery_id,
            "mission_id": self.mission_id,
            "drone_id": self.drone_id,
            "classification": {
                "type": self.discovery_type.value if self.discovery_type else None,
                "status": self.status.value if self.status else None,
                "confidence_level": self.confidence_level.value if self.confidence_level else None,
                "ai_confidence_score": self.ai_confidence_score
            },
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "altitude": self.altitude,
                "gps_accuracy_m": self.gps_accuracy_m
            },
            "detection": {
                "detected_at": self.detected_at.isoformat() if self.detected_at else None,
                "method": self.detection_method,
                "algorithm": self.detection_algorithm
            },
            "media": {
                "image_path": self.image_path,
                "video_path": self.video_path,
                "thumbnail_path": self.thumbnail_path
            },
            "bounding_box": {
                "x": self.bbox_x,
                "y": self.bbox_y,
                "width": self.bbox_width,
                "height": self.bbox_height
            } if self.bbox_x is not None else None,
            "physical": {
                "estimated_size_m": self.estimated_size_m,
                "estimated_distance_m": self.estimated_distance_m,
                "color": self.object_color,
                "shape": self.object_shape
            },
            "descriptions": {
                "description": self.description,
                "ai_description": self.ai_description,
                "human_notes": self.human_notes
            },
            "review": {
                "reviewed_by": self.reviewed_by,
                "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
                "review_notes": self.review_notes
            },
            "investigation": {
                "investigated": self.investigated,
                "team": self.investigation_team,
                "date": self.investigation_date.isoformat() if self.investigation_date else None,
                "result": self.investigation_result
            },
            "priority": {
                "score": self.priority_score,
                "immediate_attention": self.requires_immediate_attention
            },
            "environment": {
                "weather_conditions": self.weather_conditions or {},
                "lighting": self.lighting_conditions,
                "visibility_km": self.visibility_km
            },
            "relationships": {
                "related_discoveries": self.related_discoveries or [],
                "cluster_id": self.cluster_id
            },
            "metadata": {
                "raw_detection_data": self.raw_detection_data or {},
                "processing_metadata": self.processing_metadata or {},
                "tags": self.tags or []
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            }
        }
    
    def update_status(self, new_status: DiscoveryStatus, reviewer: str = None, notes: str = None):
        """Update discovery status with review information."""
        self.status = new_status
        if reviewer:
            self.reviewed_by = reviewer
            self.reviewed_at = datetime.utcnow()
        if notes:
            self.review_notes = notes
        self.updated_at = datetime.utcnow()
    
    def mark_investigated(self, team: str, result: str):
        """Mark discovery as investigated."""
        self.investigated = True
        self.investigation_team = team
        self.investigation_date = datetime.utcnow()
        self.investigation_result = result
        self.status = DiscoveryStatus.INVESTIGATED
        self.updated_at = datetime.utcnow()
    
    def set_priority(self, score: float, immediate: bool = False):
        """Set discovery priority."""
        self.priority_score = max(0.0, min(1.0, score))
        self.requires_immediate_attention = immediate
        self.updated_at = datetime.utcnow()
    
    def add_related_discovery(self, discovery_id: str):
        """Add a related discovery."""
        if not self.related_discoveries:
            self.related_discoveries = []
        if discovery_id not in self.related_discoveries:
            self.related_discoveries.append(discovery_id)
            self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str):
        """Add a searchable tag."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def is_confirmed(self) -> bool:
        """Check if discovery is confirmed as valid."""
        return self.status == DiscoveryStatus.CONFIRMED
    
    def is_false_positive(self) -> bool:
        """Check if discovery is marked as false positive."""
        return self.status == DiscoveryStatus.FALSE_POSITIVE
    
    def needs_review(self) -> bool:
        """Check if discovery needs human review."""
        return self.status in [DiscoveryStatus.DETECTED, DiscoveryStatus.PENDING_REVIEW]
    
    def is_high_priority(self) -> bool:
        """Check if discovery is high priority."""
        return self.priority_score > 0.7 or self.requires_immediate_attention
    
    def get_distance_from_point(self, lat: float, lon: float) -> float:
        """Calculate distance from a given point in meters."""
        import math
        
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(lat), math.radians(lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in meters
        r = 6371000
        
        return c * r
    
    @classmethod
    def get_confidence_level_from_score(cls, score: float) -> ConfidenceLevel:
        """Convert confidence score to confidence level enum."""
        if score < 0.2:
            return ConfidenceLevel.VERY_LOW
        elif score < 0.4:
            return ConfidenceLevel.LOW
        elif score < 0.6:
            return ConfidenceLevel.MEDIUM
        elif score < 0.8:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

class DiscoveryCluster(Base):
    """Model for grouping related discoveries together."""
    
    __tablename__ = "discovery_clusters"
    
    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String(50), unique=True, index=True, nullable=False)
    mission_id = Column(String(50), index=True, nullable=False)
    
    # Cluster properties
    cluster_type = Column(String(50))  # "spatial", "temporal", "visual_similarity"
    discovery_count = Column(Integer, default=0)
    
    # Spatial clustering
    center_latitude = Column(Float)
    center_longitude = Column(Float)
    radius_m = Column(Float)  # Cluster radius in meters
    
    # Temporal clustering
    time_span_minutes = Column(Float)  # Time span of discoveries in cluster
    first_discovery_at = Column(DateTime(timezone=True))
    last_discovery_at = Column(DateTime(timezone=True))
    
    # Cluster analysis
    primary_discovery_type = Column(SQLEnum(DiscoveryType))
    confidence_average = Column(Float)
    priority_max = Column(Float)
    
    # Status
    status = Column(String(50), default="active")  # active, resolved, false_positive
    reviewed = Column(Boolean, default=False)
    
    # Analysis results
    analysis_summary = Column(Text)
    recommended_action = Column(String(200))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cluster to dictionary."""
        return {
            "id": self.id,
            "cluster_id": self.cluster_id,
            "mission_id": self.mission_id,
            "properties": {
                "type": self.cluster_type,
                "discovery_count": self.discovery_count
            },
            "spatial": {
                "center": {
                    "latitude": self.center_latitude,
                    "longitude": self.center_longitude
                } if self.center_latitude and self.center_longitude else None,
                "radius_m": self.radius_m
            },
            "temporal": {
                "span_minutes": self.time_span_minutes,
                "first_discovery": self.first_discovery_at.isoformat() if self.first_discovery_at else None,
                "last_discovery": self.last_discovery_at.isoformat() if self.last_discovery_at else None
            },
            "analysis": {
                "primary_type": self.primary_discovery_type.value if self.primary_discovery_type else None,
                "confidence_average": self.confidence_average,
                "priority_max": self.priority_max,
                "summary": self.analysis_summary,
                "recommended_action": self.recommended_action
            },
            "status": {
                "current": self.status,
                "reviewed": self.reviewed
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            }
        }
    
    def add_discovery(self, discovery: Discovery):
        """Add a discovery to this cluster."""
        self.discovery_count += 1
        
        # Update spatial bounds
        if not self.center_latitude:
            self.center_latitude = discovery.latitude
            self.center_longitude = discovery.longitude
        else:
            # Simple centroid update (could be improved with proper clustering)
            self.center_latitude = (self.center_latitude + discovery.latitude) / 2
            self.center_longitude = (self.center_longitude + discovery.longitude) / 2
        
        # Update temporal bounds
        if not self.first_discovery_at or discovery.detected_at < self.first_discovery_at:
            self.first_discovery_at = discovery.detected_at
        if not self.last_discovery_at or discovery.detected_at > self.last_discovery_at:
            self.last_discovery_at = discovery.detected_at
        
        # Update time span
        if self.first_discovery_at and self.last_discovery_at:
            time_diff = self.last_discovery_at - self.first_discovery_at
            self.time_span_minutes = time_diff.total_seconds() / 60
        
        self.updated_at = datetime.utcnow()