"""
Learning System - AI learning and adaptation for mission optimization.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from collections import defaultdict

from .ollama_client import OllamaClient
from ..core.config import settings

logger = logging.getLogger(__name__)

class LearningCategory(Enum):
    """Categories of learning data."""
    MISSION_OUTCOMES = "mission_outcomes"
    SEARCH_PATTERNS = "search_patterns"
    WEATHER_ADAPTATIONS = "weather_adaptations"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    SAFETY_INCIDENTS = "safety_incidents"
    OPERATOR_PREFERENCES = "operator_preferences"

@dataclass
class LearningEntry:
    """A single learning entry."""
    category: LearningCategory
    mission_id: str
    timestamp: datetime
    context: Dict[str, Any]
    outcome: Dict[str, Any]
    success_metrics: Dict[str, float]
    lessons_learned: List[str]
    confidence_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["category"] = self.category.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningEntry":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["category"] = LearningCategory(data["category"])
        return cls(**data)

class LearningSystem:
    """AI learning system for mission optimization and adaptation."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
        
        # Learning data storage (in production, this would be a database)
        self.learning_entries: List[LearningEntry] = []
        
        # Pattern recognition cache
        self.pattern_cache: Dict[str, Any] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        
        # Success metrics tracking
        self.success_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Learning statistics
        self.learning_stats = {
            "total_missions_analyzed": 0,
            "patterns_discovered": 0,
            "recommendations_generated": 0,
            "accuracy_improvements": 0.0
        }
    
    async def record_mission_outcome(
        self,
        mission_id: str,
        mission_parameters: Dict[str, Any],
        outcome_data: Dict[str, Any],
        performance_metrics: Dict[str, float]
    ) -> bool:
        """Record a mission outcome for learning."""
        try:
            # Analyze the mission outcome
            analysis = await self._analyze_mission_outcome(
                mission_parameters, outcome_data, performance_metrics
            )
            
            # Create learning entry
            entry = LearningEntry(
                category=LearningCategory.MISSION_OUTCOMES,
                mission_id=mission_id,
                timestamp=datetime.utcnow(),
                context=mission_parameters,
                outcome=outcome_data,
                success_metrics=performance_metrics,
                lessons_learned=analysis.get("lessons_learned", []),
                confidence_score=analysis.get("confidence", 0.7)
            )
            
            # Store the entry
            self.learning_entries.append(entry)
            self.learning_stats["total_missions_analyzed"] += 1
            
            # Update success metrics
            for metric, value in performance_metrics.items():
                self.success_metrics[metric].append(value)
            
            # Trigger pattern analysis if we have enough data
            if len(self.learning_entries) % 10 == 0:
                await self._update_patterns()
            
            logger.info(f"Recorded learning entry for mission {mission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record mission outcome: {e}")
            return False
    
    async def _analyze_mission_outcome(
        self,
        parameters: Dict[str, Any],
        outcome: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze mission outcome to extract lessons."""
        system_prompt = """You are an AI learning system analyzing SAR mission outcomes.
        Extract key lessons learned, patterns, and insights that can improve future missions.
        Focus on what worked well and what could be improved."""
        
        prompt = f"""
        Mission Parameters: {json.dumps(parameters, indent=2)}
        Mission Outcome: {json.dumps(outcome, indent=2)}
        Performance Metrics: {json.dumps(metrics, indent=2)}
        
        Analyze this mission and provide:
        1. Key lessons learned (list of specific insights)
        2. Success factors (what contributed to good performance)
        3. Areas for improvement
        4. Confidence level in the analysis (0.0-1.0)
        
        Return as JSON with fields: lessons_learned, success_factors, improvements, confidence
        """
        
        try:
            response = await self.ollama_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Mission outcome analysis failed: {e}")
            return {
                "lessons_learned": ["Analysis failed - manual review needed"],
                "success_factors": [],
                "improvements": [],
                "confidence": 0.1
            }
    
    async def get_mission_recommendations(
        self,
        proposed_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI recommendations for mission parameters based on learning."""
        try:
            # Find similar historical missions
            similar_missions = await self._find_similar_missions(proposed_parameters)
            
            # Generate recommendations based on learning
            recommendations = await self._generate_recommendations(
                proposed_parameters, similar_missions
            )
            
            self.learning_stats["recommendations_generated"] += 1
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return {
                "recommendations": [],
                "confidence": 0.0,
                "similar_missions_count": 0
            }
    
    async def _find_similar_missions(
        self,
        parameters: Dict[str, Any]
    ) -> List[LearningEntry]:
        """Find similar historical missions for comparison."""
        similar_missions = []
        
        # Simple similarity scoring based on key parameters
        for entry in self.learning_entries:
            if entry.category == LearningCategory.MISSION_OUTCOMES:
                similarity_score = self._calculate_similarity(
                    parameters, entry.context
                )
                
                if similarity_score > 0.6:  # Similarity threshold
                    similar_missions.append((entry, similarity_score))
        
        # Sort by similarity and return top matches
        similar_missions.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in similar_missions[:10]]
    
    def _calculate_similarity(
        self,
        params1: Dict[str, Any],
        params2: Dict[str, Any]
    ) -> float:
        """Calculate similarity score between two parameter sets."""
        # Key parameters for comparison
        key_params = [
            "area_size_km2", "terrain_type", "urgency_level",
            "weather_conditions", "num_drones_requested", "search_altitude"
        ]
        
        matches = 0
        total_comparisons = 0
        
        for param in key_params:
            if param in params1 and param in params2:
                total_comparisons += 1
                
                val1 = params1[param]
                val2 = params2[param]
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # Numeric comparison - consider similar if within 20%
                    if val1 != 0:
                        diff_ratio = abs(val1 - val2) / val1
                        if diff_ratio <= 0.2:
                            matches += 1
                elif val1 == val2:
                    # Exact match for strings/categories
                    matches += 1
        
        return matches / total_comparisons if total_comparisons > 0 else 0.0
    
    async def _generate_recommendations(
        self,
        parameters: Dict[str, Any],
        similar_missions: List[LearningEntry]
    ) -> Dict[str, Any]:
        """Generate recommendations based on similar missions."""
        if not similar_missions:
            return {
                "recommendations": ["No similar missions found for comparison"],
                "confidence": 0.1,
                "similar_missions_count": 0
            }
        
        # Prepare context for AI recommendation generation
        similar_contexts = []
        for mission in similar_missions:
            similar_contexts.append({
                "parameters": mission.context,
                "outcome": mission.outcome,
                "success_metrics": mission.success_metrics,
                "lessons_learned": mission.lessons_learned
            })
        
        system_prompt = """You are an AI system providing mission planning recommendations
        based on historical SAR mission data. Analyze similar past missions and provide
        specific, actionable recommendations for the proposed mission parameters."""
        
        prompt = f"""
        Proposed Mission Parameters: {json.dumps(parameters, indent=2)}
        
        Similar Historical Missions: {json.dumps(similar_contexts, indent=2)}
        
        Based on the analysis of {len(similar_missions)} similar missions, provide:
        1. Specific parameter recommendations (with reasoning)
        2. Potential risks to consider
        3. Success optimization strategies
        4. Confidence level in recommendations (0.0-1.0)
        
        Return as JSON with fields: recommendations, risks, strategies, confidence
        """
        
        try:
            response = await self.ollama_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            result = json.loads(response)
            result["similar_missions_count"] = len(similar_missions)
            return result
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return {
                "recommendations": [f"Recommendation generation failed: {str(e)}"],
                "risks": [],
                "strategies": [],
                "confidence": 0.1,
                "similar_missions_count": len(similar_missions)
            }
    
    async def learn_search_patterns(
        self,
        mission_id: str,
        search_pattern_data: Dict[str, Any],
        effectiveness_metrics: Dict[str, float]
    ) -> bool:
        """Learn from search pattern effectiveness."""
        try:
            # Analyze search pattern effectiveness
            analysis = await self._analyze_search_patterns(
                search_pattern_data, effectiveness_metrics
            )
            
            entry = LearningEntry(
                category=LearningCategory.SEARCH_PATTERNS,
                mission_id=mission_id,
                timestamp=datetime.utcnow(),
                context=search_pattern_data,
                outcome={"effectiveness_analysis": analysis},
                success_metrics=effectiveness_metrics,
                lessons_learned=analysis.get("pattern_insights", []),
                confidence_score=analysis.get("confidence", 0.6)
            )
            
            self.learning_entries.append(entry)
            logger.info(f"Learned search pattern data for mission {mission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to learn search patterns: {e}")
            return False
    
    async def _analyze_search_patterns(
        self,
        pattern_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze search pattern effectiveness."""
        system_prompt = """Analyze SAR search pattern effectiveness and provide insights
        for optimizing future search patterns. Focus on coverage efficiency, target
        detection rates, and resource utilization."""
        
        prompt = f"""
        Search Pattern Data: {json.dumps(pattern_data, indent=2)}
        Effectiveness Metrics: {json.dumps(metrics, indent=2)}
        
        Analyze the search pattern effectiveness and provide:
        1. Pattern insights (what worked well/poorly)
        2. Optimization suggestions
        3. Terrain-specific adaptations needed
        4. Confidence in the analysis
        
        Return as JSON with fields: pattern_insights, optimizations, adaptations, confidence
        """
        
        try:
            response = await self.ollama_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Search pattern analysis failed: {e}")
            return {
                "pattern_insights": ["Analysis failed"],
                "optimizations": [],
                "adaptations": [],
                "confidence": 0.1
            }
    
    async def adapt_to_conditions(
        self,
        current_conditions: Dict[str, Any],
        mission_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt mission parameters based on current conditions and learning."""
        try:
            # Find relevant learning entries for similar conditions
            relevant_entries = await self._find_condition_adaptations(current_conditions)
            
            # Generate adaptive recommendations
            adaptations = await self._generate_adaptations(
                current_conditions, mission_parameters, relevant_entries
            )
            
            return adaptations
            
        except Exception as e:
            logger.error(f"Failed to generate adaptations: {e}")
            return {
                "adaptations": [],
                "confidence": 0.0,
                "reasoning": f"Adaptation failed: {str(e)}"
            }
    
    async def _find_condition_adaptations(
        self,
        conditions: Dict[str, Any]
    ) -> List[LearningEntry]:
        """Find learning entries relevant to current conditions."""
        relevant_entries = []
        
        for entry in self.learning_entries:
            if entry.category in [
                LearningCategory.WEATHER_ADAPTATIONS,
                LearningCategory.MISSION_OUTCOMES
            ]:
                # Check if conditions are similar
                if self._conditions_similar(conditions, entry.context):
                    relevant_entries.append(entry)
        
        return relevant_entries
    
    def _conditions_similar(
        self,
        conditions1: Dict[str, Any],
        conditions2: Dict[str, Any]
    ) -> bool:
        """Check if environmental conditions are similar."""
        # Simple condition similarity check
        condition_keys = ["weather_conditions", "terrain_type", "time_of_day"]
        
        for key in condition_keys:
            if key in conditions1 and key in conditions2:
                if conditions1[key] != conditions2[key]:
                    return False
        
        return True
    
    async def _generate_adaptations(
        self,
        conditions: Dict[str, Any],
        parameters: Dict[str, Any],
        relevant_entries: List[LearningEntry]
    ) -> Dict[str, Any]:
        """Generate adaptive recommendations for current conditions."""
        system_prompt = """Generate adaptive mission parameter recommendations based
        on current environmental conditions and historical learning data. Focus on
        safety and mission effectiveness."""
        
        historical_data = [entry.to_dict() for entry in relevant_entries]
        
        prompt = f"""
        Current Conditions: {json.dumps(conditions, indent=2)}
        Mission Parameters: {json.dumps(parameters, indent=2)}
        Historical Learning Data: {json.dumps(historical_data, indent=2)}
        
        Based on {len(relevant_entries)} relevant historical experiences, provide:
        1. Parameter adaptations needed for current conditions
        2. Safety adjustments required
        3. Performance optimization suggestions
        4. Confidence in recommendations
        
        Return as JSON with fields: adaptations, safety_adjustments, optimizations, confidence
        """
        
        try:
            response = await self.ollama_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Adaptation generation failed: {e}")
            return {
                "adaptations": [],
                "safety_adjustments": [],
                "optimizations": [],
                "confidence": 0.1
            }
    
    async def _update_patterns(self):
        """Update cached patterns based on new learning data."""
        try:
            # Analyze recent entries for new patterns
            recent_entries = [
                entry for entry in self.learning_entries
                if entry.timestamp > datetime.utcnow() - timedelta(days=30)
            ]
            
            if len(recent_entries) < 5:
                return  # Not enough data for pattern analysis
            
            # Generate pattern analysis
            patterns = await self._analyze_patterns(recent_entries)
            
            # Update pattern cache
            cache_key = f"patterns_{datetime.utcnow().strftime('%Y%m')}"
            self.pattern_cache[cache_key] = patterns
            self.cache_expiry[cache_key] = datetime.utcnow() + timedelta(days=30)
            
            self.learning_stats["patterns_discovered"] += len(patterns.get("new_patterns", []))
            
            logger.info(f"Updated patterns cache with {len(recent_entries)} recent entries")
            
        except Exception as e:
            logger.error(f"Pattern update failed: {e}")
    
    async def _analyze_patterns(self, entries: List[LearningEntry]) -> Dict[str, Any]:
        """Analyze learning entries to discover patterns."""
        system_prompt = """Analyze SAR mission learning data to discover patterns
        and trends that can improve future mission planning and execution."""
        
        entries_data = [entry.to_dict() for entry in entries]
        
        prompt = f"""
        Learning Entries Data: {json.dumps(entries_data, indent=2)}
        
        Analyze this learning data to identify:
        1. Success patterns (what combinations lead to better outcomes)
        2. Failure patterns (what to avoid)
        3. Emerging trends
        4. Optimization opportunities
        
        Return as JSON with fields: success_patterns, failure_patterns, trends, opportunities
        """
        
        try:
            response = await self.ollama_client.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.4
            )
            
            return json.loads(response)
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {
                "success_patterns": [],
                "failure_patterns": [],
                "trends": [],
                "opportunities": []
            }
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        # Calculate average success metrics
        avg_metrics = {}
        for metric, values in self.success_metrics.items():
            if values:
                avg_metrics[metric] = sum(values) / len(values)
        
        return {
            "statistics": self.learning_stats,
            "total_entries": len(self.learning_entries),
            "categories": {
                category.value: len([
                    e for e in self.learning_entries
                    if e.category == category
                ])
                for category in LearningCategory
            },
            "average_success_metrics": avg_metrics,
            "cached_patterns": len(self.pattern_cache),
            "data_freshness": {
                "latest_entry": max([
                    e.timestamp for e in self.learning_entries
                ]).isoformat() if self.learning_entries else None,
                "entries_last_30_days": len([
                    e for e in self.learning_entries
                    if e.timestamp > datetime.utcnow() - timedelta(days=30)
                ])
            }
        }
    
    async def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for backup or analysis."""
        return {
            "entries": [entry.to_dict() for entry in self.learning_entries],
            "patterns": self.pattern_cache,
            "statistics": self.learning_stats,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    async def import_learning_data(self, data: Dict[str, Any]) -> bool:
        """Import learning data from backup."""
        try:
            # Import entries
            imported_entries = []
            for entry_data in data.get("entries", []):
                entry = LearningEntry.from_dict(entry_data)
                imported_entries.append(entry)
            
            self.learning_entries.extend(imported_entries)
            
            # Import patterns
            if "patterns" in data:
                self.pattern_cache.update(data["patterns"])
            
            # Update statistics
            if "statistics" in data:
                for key, value in data["statistics"].items():
                    if key in self.learning_stats:
                        self.learning_stats[key] += value
            
            logger.info(f"Imported {len(imported_entries)} learning entries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import learning data: {e}")
            return False