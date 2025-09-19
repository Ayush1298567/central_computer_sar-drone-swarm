"""
AI Learning database models for storing learning data and insights.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base

class LearningCategory(enum.Enum):
    """Categories of learning data."""
    MISSION_OUTCOMES = "mission_outcomes"
    SEARCH_PATTERNS = "search_patterns"
    WEATHER_ADAPTATIONS = "weather_adaptations"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    SAFETY_INCIDENTS = "safety_incidents"
    OPERATOR_PREFERENCES = "operator_preferences"
    DETECTION_ACCURACY = "detection_accuracy"
    FLIGHT_PERFORMANCE = "flight_performance"

class LearningSource(enum.Enum):
    """Source of learning data."""
    MISSION_DATA = "mission_data"
    OPERATOR_FEEDBACK = "operator_feedback"
    AI_ANALYSIS = "ai_analysis"
    SENSOR_DATA = "sensor_data"
    EXTERNAL_DATA = "external_data"

class AILearningEntry(Base):
    """AI Learning entry for storing insights and patterns."""
    
    __tablename__ = "ai_learning_entries"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(String(50), unique=True, index=True, nullable=False)
    mission_id = Column(String(50), index=True)
    
    # Learning classification
    category = Column(SQLEnum(LearningCategory), nullable=False, index=True)
    source = Column(SQLEnum(LearningSource), nullable=False)
    
    # Context and input data
    context_data = Column(JSON, nullable=False)  # Input conditions/parameters
    outcome_data = Column(JSON, nullable=False)  # Results/outcomes
    
    # Success metrics
    success_metrics = Column(JSON)  # Quantitative success measures
    performance_score = Column(Float)  # Overall performance score (0.0-1.0)
    
    # Learning insights
    lessons_learned = Column(JSON)  # List of specific lessons
    patterns_identified = Column(JSON)  # Patterns discovered
    recommendations = Column(JSON)  # Actionable recommendations
    
    # Confidence and reliability
    confidence_score = Column(Float, nullable=False)  # AI confidence in learning (0.0-1.0)
    data_quality_score = Column(Float)  # Quality of input data (0.0-1.0)
    sample_size = Column(Integer, default=1)  # Number of data points
    
    # Validation
    validated = Column(Boolean, default=False)
    validation_method = Column(String(100))  # How it was validated
    validation_score = Column(Float)  # Validation accuracy
    
    # Impact tracking
    times_applied = Column(Integer, default=0)
    success_rate = Column(Float)  # Success rate when applied
    impact_score = Column(Float)  # Measured impact on performance
    
    # Environmental context
    environmental_conditions = Column(JSON)  # Weather, terrain, etc.
    mission_complexity = Column(String(20))  # simple, medium, complex
    
    # Temporal relevance
    relevance_decay_rate = Column(Float, default=0.1)  # How quickly this becomes outdated
    last_validated = Column(DateTime(timezone=True))
    next_validation_due = Column(DateTime(timezone=True))
    
    # Metadata
    tags = Column(JSON)  # Searchable tags
    notes = Column(Text)  # Human annotations
    related_entries = Column(JSON)  # Related learning entry IDs
    
    # Processing info
    processing_algorithm = Column(String(100))  # Algorithm that generated this
    processing_version = Column(String(20))  # Version of processing
    raw_analysis_data = Column(JSON)  # Raw analysis output
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert learning entry to dictionary."""
        return {
            "id": self.id,
            "entry_id": self.entry_id,
            "mission_id": self.mission_id,
            "classification": {
                "category": self.category.value if self.category else None,
                "source": self.source.value if self.source else None
            },
            "data": {
                "context": self.context_data or {},
                "outcome": self.outcome_data or {},
                "success_metrics": self.success_metrics or {}
            },
            "insights": {
                "lessons_learned": self.lessons_learned or [],
                "patterns_identified": self.patterns_identified or [],
                "recommendations": self.recommendations or []
            },
            "reliability": {
                "confidence_score": self.confidence_score,
                "data_quality_score": self.data_quality_score,
                "sample_size": self.sample_size,
                "performance_score": self.performance_score
            },
            "validation": {
                "validated": self.validated,
                "method": self.validation_method,
                "score": self.validation_score,
                "last_validated": self.last_validated.isoformat() if self.last_validated else None,
                "next_due": self.next_validation_due.isoformat() if self.next_validation_due else None
            },
            "impact": {
                "times_applied": self.times_applied,
                "success_rate": self.success_rate,
                "impact_score": self.impact_score
            },
            "context": {
                "environmental_conditions": self.environmental_conditions or {},
                "mission_complexity": self.mission_complexity,
                "relevance_decay_rate": self.relevance_decay_rate
            },
            "metadata": {
                "tags": self.tags or [],
                "notes": self.notes,
                "related_entries": self.related_entries or []
            },
            "processing": {
                "algorithm": self.processing_algorithm,
                "version": self.processing_version,
                "raw_data": self.raw_analysis_data or {}
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            }
        }
    
    def update_impact(self, applied: bool, successful: bool = None):
        """Update impact tracking when learning is applied."""
        self.times_applied += 1
        
        if successful is not None:
            if self.success_rate is None:
                self.success_rate = 1.0 if successful else 0.0
            else:
                # Running average
                total_successes = self.success_rate * (self.times_applied - 1)
                if successful:
                    total_successes += 1
                self.success_rate = total_successes / self.times_applied
        
        self.updated_at = datetime.utcnow()
    
    def add_validation(self, method: str, score: float):
        """Add validation results."""
        self.validated = True
        self.validation_method = method
        self.validation_score = score
        self.last_validated = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_related_entry(self, entry_id: str):
        """Add a related learning entry."""
        if not self.related_entries:
            self.related_entries = []
        if entry_id not in self.related_entries:
            self.related_entries.append(entry_id)
            self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str):
        """Add a searchable tag."""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def is_relevant(self, current_conditions: Dict[str, Any] = None) -> bool:
        """Check if this learning entry is still relevant."""
        # Check temporal relevance
        if self.created_at:
            age_days = (datetime.utcnow() - self.created_at).days
            relevance_threshold = 1.0 / (1.0 + self.relevance_decay_rate * age_days)
            if relevance_threshold < 0.3:  # Arbitrary threshold
                return False
        
        # Check confidence and validation
        if self.confidence_score < 0.5:
            return False
        
        if self.validated and self.validation_score and self.validation_score < 0.6:
            return False
        
        return True
    
    def get_applicability_score(self, context: Dict[str, Any]) -> float:
        """Calculate how applicable this learning is to a given context."""
        if not self.is_relevant():
            return 0.0
        
        # Simple similarity scoring
        score = self.confidence_score * 0.4  # Base confidence
        
        # Add validation bonus
        if self.validated and self.validation_score:
            score += self.validation_score * 0.3
        
        # Add impact bonus
        if self.impact_score:
            score += self.impact_score * 0.2
        
        # Add success rate bonus
        if self.success_rate:
            score += self.success_rate * 0.1
        
        return min(1.0, score)

class LearningPattern(Base):
    """Identified patterns from multiple learning entries."""
    
    __tablename__ = "learning_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Pattern description
    pattern_name = Column(String(200), nullable=False)
    pattern_description = Column(Text)
    pattern_type = Column(String(50))  # correlation, causation, trend, anomaly
    
    # Pattern data
    pattern_conditions = Column(JSON)  # Conditions where pattern applies
    pattern_outcomes = Column(JSON)  # Expected outcomes
    confidence_level = Column(Float, nullable=False)  # 0.0-1.0
    
    # Supporting evidence
    supporting_entries = Column(JSON)  # List of learning entry IDs
    sample_size = Column(Integer, default=0)
    statistical_significance = Column(Float)  # p-value or similar
    
    # Pattern strength
    correlation_strength = Column(Float)  # -1.0 to 1.0
    effect_size = Column(Float)  # Magnitude of effect
    consistency_score = Column(Float)  # How consistent across data
    
    # Applicability
    applicable_categories = Column(JSON)  # Which learning categories
    environmental_constraints = Column(JSON)  # When pattern applies
    
    # Validation and testing
    validated = Column(Boolean, default=False)
    validation_results = Column(JSON)
    last_tested = Column(DateTime(timezone=True))
    
    # Usage tracking
    times_referenced = Column(Integer, default=0)
    successful_applications = Column(Integer, default=0)
    
    # Metadata
    discovered_by = Column(String(100))  # Algorithm or analyst
    discovery_method = Column(String(100))
    tags = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "id": self.id,
            "pattern_id": self.pattern_id,
            "description": {
                "name": self.pattern_name,
                "description": self.pattern_description,
                "type": self.pattern_type
            },
            "pattern": {
                "conditions": self.pattern_conditions or {},
                "outcomes": self.pattern_outcomes or {},
                "confidence_level": self.confidence_level
            },
            "evidence": {
                "supporting_entries": self.supporting_entries or [],
                "sample_size": self.sample_size,
                "statistical_significance": self.statistical_significance
            },
            "strength": {
                "correlation": self.correlation_strength,
                "effect_size": self.effect_size,
                "consistency": self.consistency_score
            },
            "applicability": {
                "categories": self.applicable_categories or [],
                "constraints": self.environmental_constraints or {}
            },
            "validation": {
                "validated": self.validated,
                "results": self.validation_results or {},
                "last_tested": self.last_tested.isoformat() if self.last_tested else None
            },
            "usage": {
                "references": self.times_referenced,
                "successful_applications": self.successful_applications,
                "success_rate": self.successful_applications / max(1, self.times_referenced)
            },
            "metadata": {
                "discovered_by": self.discovered_by,
                "discovery_method": self.discovery_method,
                "tags": self.tags or []
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            }
        }
    
    def add_supporting_entry(self, entry_id: str):
        """Add a supporting learning entry."""
        if not self.supporting_entries:
            self.supporting_entries = []
        if entry_id not in self.supporting_entries:
            self.supporting_entries.append(entry_id)
            self.sample_size = len(self.supporting_entries)
            self.updated_at = datetime.utcnow()
    
    def record_usage(self, successful: bool = True):
        """Record usage of this pattern."""
        self.times_referenced += 1
        if successful:
            self.successful_applications += 1
        self.updated_at = datetime.utcnow()
    
    def get_reliability_score(self) -> float:
        """Calculate overall reliability score."""
        score = self.confidence_level * 0.4
        
        if self.validated:
            score += 0.2
        
        if self.sample_size > 10:
            score += 0.2
        elif self.sample_size > 5:
            score += 0.1
        
        if self.times_referenced > 0:
            success_rate = self.successful_applications / self.times_referenced
            score += success_rate * 0.2
        
        return min(1.0, score)