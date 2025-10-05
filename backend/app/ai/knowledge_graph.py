"""
Knowledge Graph System for SAR Operations
Advanced graph-based learning and optimization for mission intelligence
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
import numpy as np
from neo4j import GraphDatabase
import networkx as nx
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class NodeType(Enum):
    MISSION = "mission"
    DRONE = "drone"
    TERRAIN = "terrain"
    WEATHER = "weather"
    PATTERN = "pattern"
    OUTCOME = "outcome"
    LESSON = "lesson"
    OPTIMIZATION = "optimization"
    CONSTRAINT = "constraint"
    RESOURCE = "resource"

class RelationshipType(Enum):
    CAUSES = "causes"
    IMPROVES = "improves"
    PREVENTS = "prevents"
    REQUIRES = "requires"
    INFLUENCES = "influences"
    CORRELATES_WITH = "correlates_with"
    LEADS_TO = "leads_to"
    OPTIMIZES = "optimizes"
    CONSTRAINS = "constrains"
    DEPENDS_ON = "depends_on"

@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    node_id: str
    node_type: NodeType
    properties: Dict[str, Any]
    confidence: float
    created_at: datetime
    last_updated: datetime
    usage_count: int = 0
    success_rate: float = 0.0

@dataclass
class GraphRelationship:
    """Represents a relationship in the knowledge graph"""
    relationship_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    strength: float
    confidence: float
    evidence: List[str]
    evidence_count: int
    created_at: datetime
    last_verified: datetime
    success_rate: float = 0.0

@dataclass
class GraphQuery:
    """Query structure for knowledge graph"""
    query_type: str
    source_node_types: List[NodeType]
    target_node_types: List[NodeType]
    relationship_types: List[RelationshipType]
    constraints: Dict[str, Any]
    max_depth: int = 3
    min_confidence: float = 0.3

class SARKnowledgeGraph:
    """Advanced knowledge graph for SAR mission intelligence"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", username: str = "neo4j", password: str = "password"):
        self.neo4j_uri = neo4j_uri
        self.username = username
        self.password = password
        self.driver = None
        
        # In-memory graph for fast queries
        self.memory_graph = nx.MultiDiGraph()
        self.node_cache = {}
        self.relationship_cache = {}
        
        # Initialize connection
        asyncio.create_task(self._initialize_connection())
    
    async def _initialize_connection(self):
        """Initialize Neo4j connection and load existing data"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.username, self.password)
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            
            # Load existing data into memory graph
            await self._load_graph_to_memory()
            
            logger.info("Knowledge graph initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge graph: {e}")
            # Fallback to in-memory only mode
            self.driver = None
    
    async def _load_graph_to_memory(self):
        """Load Neo4j graph data into memory for fast queries"""
        try:
            if not self.driver:
                return
            
            with self.driver.session() as session:
                # Load nodes
                node_query = """
                MATCH (n)
                RETURN n.id as node_id, labels(n)[0] as node_type, 
                       properties(n) as properties, n.confidence as confidence,
                       n.created_at as created_at, n.last_updated as last_updated,
                       n.usage_count as usage_count, n.success_rate as success_rate
                """
                
                for record in session.run(node_query):
                    node = GraphNode(
                        node_id=record["node_id"],
                        node_type=NodeType(record["node_type"]),
                        properties=dict(record["properties"]),
                        confidence=record["confidence"] or 0.5,
                        created_at=datetime.fromisoformat(record["created_at"]) if record["created_at"] else datetime.utcnow(),
                        last_updated=datetime.fromisoformat(record["last_updated"]) if record["last_updated"] else datetime.utcnow(),
                        usage_count=record["usage_count"] or 0,
                        success_rate=record["success_rate"] or 0.0
                    )
                    
                    self.node_cache[node.node_id] = node
                    self.memory_graph.add_node(
                        node.node_id,
                        node_type=node.node_type.value,
                        **node.properties
                    )
                
                # Load relationships
                relationship_query = """
                MATCH (s)-[r]->(t)
                RETURN s.id as source_id, t.id as target_id, type(r) as relationship_type,
                       r.strength as strength, r.confidence as confidence,
                       r.evidence as evidence, r.evidence_count as evidence_count,
                       r.created_at as created_at, r.last_verified as last_verified,
                       r.success_rate as success_rate
                """
                
                for record in session.run(relationship_query):
                    relationship = GraphRelationship(
                        relationship_id=f"{record['source_id']}_{record['relationship_type']}_{record['target_id']}",
                        source_node_id=record["source_id"],
                        target_node_id=record["target_id"],
                        relationship_type=RelationshipType(record["relationship_type"]),
                        strength=record["strength"] or 0.5,
                        confidence=record["confidence"] or 0.5,
                        evidence=record["evidence"] or [],
                        evidence_count=record["evidence_count"] or 1,
                        created_at=datetime.fromisoformat(record["created_at"]) if record["created_at"] else datetime.utcnow(),
                        last_verified=datetime.fromisoformat(record["last_verified"]) if record["last_verified"] else datetime.utcnow(),
                        success_rate=record["success_rate"] or 0.0
                    )
                    
                    self.relationship_cache[relationship.relationship_id] = relationship
                    self.memory_graph.add_edge(
                        relationship.source_node_id,
                        relationship.target_node_id,
                        relationship_type=relationship.relationship_type.value,
                        strength=relationship.strength,
                        confidence=relationship.confidence
                    )
            
            logger.info(f"Loaded {len(self.node_cache)} nodes and {len(self.relationship_cache)} relationships into memory")
            
        except Exception as e:
            logger.error(f"Failed to load graph to memory: {e}")
    
    async def add_mission_knowledge(
        self,
        mission_data: Dict[str, Any],
        outcomes: Dict[str, Any],
        lessons_learned: List[str]
    ) -> str:
        """Add mission knowledge to the graph"""
        try:
            mission_id = mission_data.get("mission_id", str(uuid.uuid4()))
            
            # Create mission node
            mission_node = GraphNode(
                node_id=f"mission_{mission_id}",
                node_type=NodeType.MISSION,
                properties={
                    "mission_id": mission_id,
                    "mission_type": mission_data.get("mission_type", "unknown"),
                    "terrain_type": mission_data.get("terrain_type", "unknown"),
                    "weather_conditions": mission_data.get("weather_conditions", {}),
                    "search_pattern": mission_data.get("search_pattern", "unknown"),
                    "drone_count": mission_data.get("drone_count", 1),
                    "duration_minutes": outcomes.get("duration_minutes", 0),
                    "success_rate": outcomes.get("success_rate", 0.0),
                    "discoveries_count": outcomes.get("discoveries_count", 0),
                    "area_covered": outcomes.get("area_covered", 0.0)
                },
                confidence=0.8,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            await self._add_node(mission_node)
            
            # Create terrain node if not exists
            terrain_type = mission_data.get("terrain_type", "unknown")
            terrain_node_id = f"terrain_{terrain_type}"
            if terrain_node_id not in self.node_cache:
                terrain_node = GraphNode(
                    node_id=terrain_node_id,
                    node_type=NodeType.TERRAIN,
                    properties={
                        "terrain_type": terrain_type,
                        "difficulty_score": self._calculate_terrain_difficulty(terrain_type),
                        "typical_challenges": self._get_terrain_challenges(terrain_type)
                    },
                    confidence=0.9,
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                await self._add_node(terrain_node)
            
            # Create pattern node if not exists
            search_pattern = mission_data.get("search_pattern", "unknown")
            pattern_node_id = f"pattern_{search_pattern}"
            if pattern_node_id not in self.node_cache:
                pattern_node = GraphNode(
                    node_id=pattern_node_id,
                    node_type=NodeType.PATTERN,
                    properties={
                        "pattern_type": search_pattern,
                        "efficiency_score": 0.5,
                        "typical_use_cases": self._get_pattern_use_cases(search_pattern)
                    },
                    confidence=0.7,
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                await self._add_node(pattern_node)
            
            # Create outcome node
            outcome_node = GraphNode(
                node_id=f"outcome_{mission_id}",
                node_type=NodeType.OUTCOME,
                properties={
                    "mission_id": mission_id,
                    "success_rate": outcomes.get("success_rate", 0.0),
                    "efficiency_score": outcomes.get("efficiency_score", 0.0),
                    "discoveries_made": outcomes.get("discoveries_count", 0),
                    "lessons_learned": lessons_learned
                },
                confidence=0.8,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            await self._add_node(outcome_node)
            
            # Create relationships
            relationships_to_create = [
                # Mission -> Terrain
                {
                    "source": mission_node.node_id,
                    "target": terrain_node_id,
                    "type": RelationshipType.REQUIRES,
                    "strength": 1.0,
                    "evidence": [f"Mission {mission_id} operated in {terrain_type} terrain"]
                },
                # Mission -> Pattern
                {
                    "source": mission_node.node_id,
                    "target": pattern_node_id,
                    "type": RelationshipType.REQUIRES,
                    "strength": 1.0,
                    "evidence": [f"Mission {mission_id} used {search_pattern} search pattern"]
                },
                # Mission -> Outcome
                {
                    "source": mission_node.node_id,
                    "target": outcome_node.node_id,
                    "type": RelationshipType.LEADS_TO,
                    "strength": 1.0,
                    "evidence": [f"Mission {mission_id} resulted in outcome with {outcomes.get('success_rate', 0):.1%} success"]
                },
                # Pattern -> Outcome (if successful)
                {
                    "source": pattern_node_id,
                    "target": outcome_node.node_id,
                    "type": RelationshipType.INFLUENCES,
                    "strength": outcomes.get("success_rate", 0.0),
                    "evidence": [f"Pattern {search_pattern} contributed to mission outcome"]
                },
                # Terrain -> Outcome
                {
                    "source": terrain_node_id,
                    "target": outcome_node.node_id,
                    "type": RelationshipType.INFLUENCES,
                    "strength": 0.5 + (outcomes.get("success_rate", 0.0) * 0.5),
                    "evidence": [f"Terrain {terrain_type} influenced mission outcome"]
                }
            ]
            
            for rel_data in relationships_to_create:
                relationship = GraphRelationship(
                    relationship_id=f"{rel_data['source']}_{rel_data['type'].value}_{rel_data['target']}",
                    source_node_id=rel_data["source"],
                    target_node_id=rel_data["target"],
                    relationship_type=rel_data["type"],
                    strength=rel_data["strength"],
                    confidence=0.8,
                    evidence=rel_data["evidence"],
                    evidence_count=1,
                    created_at=datetime.utcnow(),
                    last_verified=datetime.utcnow()
                )
                await self._add_relationship(relationship)
            
            # Process lessons learned
            for lesson in lessons_learned:
                await self._process_lesson_learned(lesson, mission_node.node_id, outcome_node.node_id)
            
            logger.info(f"Added mission knowledge for mission {mission_id}")
            return mission_id
            
        except Exception as e:
            logger.error(f"Failed to add mission knowledge: {e}")
            raise
    
    async def _add_node(self, node: GraphNode):
        """Add node to both Neo4j and memory graph"""
        try:
            # Add to memory graph
            self.node_cache[node.node_id] = node
            self.memory_graph.add_node(
                node.node_id,
                node_type=node.node_type.value,
                **node.properties
            )
            
            # Add to Neo4j if available
            if self.driver:
                with self.driver.session() as session:
                    query = """
                    MERGE (n:Node {id: $node_id})
                    SET n.type = $node_type,
                        n.properties = $properties,
                        n.confidence = $confidence,
                        n.created_at = $created_at,
                        n.last_updated = $last_updated,
                        n.usage_count = $usage_count,
                        n.success_rate = $success_rate
                    """
                    
                    session.run(query, {
                        "node_id": node.node_id,
                        "node_type": node.node_type.value,
                        "properties": node.properties,
                        "confidence": node.confidence,
                        "created_at": node.created_at.isoformat(),
                        "last_updated": node.last_updated.isoformat(),
                        "usage_count": node.usage_count,
                        "success_rate": node.success_rate
                    })
            
        except Exception as e:
            logger.error(f"Failed to add node {node.node_id}: {e}")
    
    async def _add_relationship(self, relationship: GraphRelationship):
        """Add relationship to both Neo4j and memory graph"""
        try:
            # Add to memory graph
            self.relationship_cache[relationship.relationship_id] = relationship
            self.memory_graph.add_edge(
                relationship.source_node_id,
                relationship.target_node_id,
                relationship_type=relationship.relationship_type.value,
                strength=relationship.strength,
                confidence=relationship.confidence
            )
            
            # Add to Neo4j if available
            if self.driver:
                with self.driver.session() as session:
                    query = """
                    MATCH (s:Node {id: $source_id}), (t:Node {id: $target_id})
                    MERGE (s)-[r:RELATIONSHIP {type: $relationship_type}]->(t)
                    SET r.strength = $strength,
                        r.confidence = $confidence,
                        r.evidence = $evidence,
                        r.evidence_count = $evidence_count,
                        r.created_at = $created_at,
                        r.last_verified = $last_verified,
                        r.success_rate = $success_rate
                    """
                    
                    session.run(query, {
                        "source_id": relationship.source_node_id,
                        "target_id": relationship.target_node_id,
                        "relationship_type": relationship.relationship_type.value,
                        "strength": relationship.strength,
                        "confidence": relationship.confidence,
                        "evidence": relationship.evidence,
                        "evidence_count": relationship.evidence_count,
                        "created_at": relationship.created_at.isoformat(),
                        "last_verified": relationship.last_verified.isoformat(),
                        "success_rate": relationship.success_rate
                    })
            
        except Exception as e:
            logger.error(f"Failed to add relationship {relationship.relationship_id}: {e}")
    
    async def query_knowledge(
        self,
        query: GraphQuery
    ) -> List[Dict[str, Any]]:
        """Query the knowledge graph for insights"""
        try:
            results = []
            
            # Use NetworkX for fast in-memory queries
            if query.query_type == "find_patterns":
                results = await self._find_successful_patterns(query)
            elif query.query_type == "find_optimizations":
                results = await self._find_optimization_opportunities(query)
            elif query.query_type == "predict_outcome":
                results = await self._predict_mission_outcome(query)
            elif query.query_type == "find_constraints":
                results = await self._find_constraints(query)
            elif query.query_type == "recommend_strategy":
                results = await self._recommend_strategy(query)
            else:
                results = await self._generic_graph_query(query)
            
            return results
            
        except Exception as e:
            logger.error(f"Knowledge query failed: {e}")
            return []
    
    async def _find_successful_patterns(self, query: GraphQuery) -> List[Dict[str, Any]]:
        """Find successful patterns for similar conditions"""
        try:
            results = []
            
            # Find missions with similar terrain/weather conditions
            for node_id, node_data in self.memory_graph.nodes(data=True):
                if node_data.get("node_type") == "mission":
                    # Check if mission matches query constraints
                    if self._matches_constraints(node_data, query.constraints):
                        # Find associated patterns and outcomes
                        pattern_nodes = []
                        outcome_nodes = []
                        
                        for neighbor in self.memory_graph.successors(node_id):
                            neighbor_data = self.memory_graph.nodes[neighbor]
                            if neighbor_data.get("node_type") == "pattern":
                                pattern_nodes.append(neighbor)
                            elif neighbor_data.get("node_type") == "outcome":
                                outcome_nodes.append(neighbor)
                        
                        # Calculate pattern effectiveness
                        for pattern_id in pattern_nodes:
                            pattern_data = self.memory_graph.nodes[pattern_id]
                            effectiveness = self._calculate_pattern_effectiveness(pattern_id, outcome_nodes)
                            
                            if effectiveness > 0.7:  # Only include highly effective patterns
                                results.append({
                                    "pattern_type": pattern_data.get("pattern_type"),
                                    "effectiveness": effectiveness,
                                    "use_cases": pattern_data.get("typical_use_cases", []),
                                    "evidence": self._get_pattern_evidence(pattern_id)
                                })
            
            # Sort by effectiveness
            results.sort(key=lambda x: x["effectiveness"], reverse=True)
            return results[:10]  # Top 10 patterns
            
        except Exception as e:
            logger.error(f"Failed to find successful patterns: {e}")
            return []
    
    async def _find_optimization_opportunities(self, query: GraphQuery) -> List[Dict[str, Any]]:
        """Find optimization opportunities based on historical data"""
        try:
            results = []
            
            # Analyze relationships between different factors and outcomes
            optimization_insights = defaultdict(list)
            
            for source_id, target_id, edge_data in self.memory_graph.edges(data=True):
                if edge_data.get("node_type") == "outcome":
                    # Find what influenced this outcome
                    for predecessor in self.memory_graph.predecessors(target_id):
                        predecessor_data = self.memory_graph.nodes[predecessor]
                        predecessor_type = predecessor_data.get("node_type")
                        
                        if predecessor_type in ["pattern", "terrain", "mission"]:
                            relationship_strength = edge_data.get("strength", 0.0)
                            outcome_success = predecessor_data.get("success_rate", 0.0)
                            
                            optimization_insights[predecessor_type].append({
                                "factor": predecessor,
                                "strength": relationship_strength,
                                "outcome": outcome_success,
                                "optimization_potential": relationship_strength * (1.0 - outcome_success)
                            })
            
            # Generate optimization recommendations
            for factor_type, insights in optimization_insights.items():
                # Sort by optimization potential
                insights.sort(key=lambda x: x["optimization_potential"], reverse=True)
                
                for insight in insights[:3]:  # Top 3 for each factor type
                    if insight["optimization_potential"] > 0.3:
                        results.append({
                            "factor_type": factor_type,
                            "factor": insight["factor"],
                            "optimization_potential": insight["optimization_potential"],
                            "current_performance": insight["outcome"],
                            "recommendation": self._generate_optimization_recommendation(
                                factor_type, insight["factor"], insight["optimization_potential"]
                            )
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to find optimization opportunities: {e}")
            return []
    
    async def _predict_mission_outcome(self, query: GraphQuery) -> Dict[str, Any]:
        """Predict mission outcome based on planned parameters"""
        try:
            constraints = query.constraints
            terrain_type = constraints.get("terrain_type", "unknown")
            search_pattern = constraints.get("search_pattern", "unknown")
            weather_conditions = constraints.get("weather_conditions", {})
            
            # Find similar missions
            similar_missions = []
            for node_id, node_data in self.memory_graph.nodes(data=True):
                if node_data.get("node_type") == "mission":
                    similarity_score = self._calculate_mission_similarity(
                        node_data, constraints
                    )
                    if similarity_score > 0.6:
                        similar_missions.append((node_id, similarity_score, node_data))
            
            if not similar_missions:
                return {
                    "prediction": "unknown",
                    "confidence": 0.0,
                    "reasoning": "No similar missions found for prediction"
                }
            
            # Sort by similarity
            similar_missions.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate weighted average outcome
            total_weight = 0.0
            weighted_success = 0.0
            weighted_efficiency = 0.0
            
            for mission_id, similarity, mission_data in similar_missions[:5]:  # Top 5 similar missions
                # Find outcome for this mission
                for outcome_id in self.memory_graph.successors(mission_id):
                    outcome_data = self.memory_graph.nodes[outcome_id]
                    if outcome_data.get("node_type") == "outcome":
                        weight = similarity
                        total_weight += weight
                        weighted_success += outcome_data.get("success_rate", 0.0) * weight
                        weighted_efficiency += outcome_data.get("efficiency_score", 0.0) * weight
                        break
            
            if total_weight > 0:
                predicted_success = weighted_success / total_weight
                predicted_efficiency = weighted_efficiency / total_weight
                confidence = min(total_weight / 5.0, 1.0)  # Normalize confidence
                
                return {
                    "prediction": "successful" if predicted_success > 0.7 else "challenging" if predicted_success > 0.4 else "difficult",
                    "success_probability": predicted_success,
                    "efficiency_score": predicted_efficiency,
                    "confidence": confidence,
                    "reasoning": f"Based on {len(similar_missions)} similar missions with {confidence:.1%} confidence",
                    "similar_missions_count": len(similar_missions)
                }
            
            return {
                "prediction": "unknown",
                "confidence": 0.0,
                "reasoning": "Insufficient data for prediction"
            }
            
        except Exception as e:
            logger.error(f"Failed to predict mission outcome: {e}")
            return {"prediction": "unknown", "confidence": 0.0, "error": str(e)}
    
    async def _recommend_strategy(self, query: GraphQuery) -> Dict[str, Any]:
        """Recommend optimal strategy based on conditions"""
        try:
            constraints = query.constraints
            
            # Find best patterns for the given conditions
            pattern_recommendations = await self._find_successful_patterns(query)
            
            # Find optimization opportunities
            optimization_opportunities = await self._find_optimization_opportunities(query)
            
            # Generate strategy recommendation
            strategy = {
                "recommended_patterns": [
                    {
                        "pattern": rec["pattern_type"],
                        "confidence": rec["effectiveness"],
                        "reasoning": f"Effective in similar conditions with {rec['effectiveness']:.1%} success rate"
                    }
                    for rec in pattern_recommendations[:3]
                ],
                "optimization_opportunities": [
                    {
                        "area": opp["factor_type"],
                        "potential": opp["optimization_potential"],
                        "recommendation": opp["recommendation"]
                    }
                    for opp in optimization_opportunities[:3]
                ],
                "risk_factors": self._identify_risk_factors(constraints),
                "success_factors": self._identify_success_factors(constraints),
                "overall_confidence": self._calculate_strategy_confidence(pattern_recommendations, optimization_opportunities)
            }
            
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to recommend strategy: {e}")
            return {"error": str(e)}
    
    def _calculate_terrain_difficulty(self, terrain_type: str) -> float:
        """Calculate difficulty score for terrain type"""
        difficulty_scores = {
            "mountain": 0.9,
            "forest": 0.7,
            "urban": 0.8,
            "water": 0.9,
            "desert": 0.6,
            "grassland": 0.3,
            "unknown": 0.5
        }
        return difficulty_scores.get(terrain_type, 0.5)
    
    def _get_terrain_challenges(self, terrain_type: str) -> List[str]:
        """Get typical challenges for terrain type"""
        challenges = {
            "mountain": ["high altitude", "wind", "limited landing sites", "GPS interference"],
            "forest": ["obstacles", "limited visibility", "GPS interference", "wildlife"],
            "urban": ["buildings", "people", "regulations", "interference"],
            "water": ["landing difficulty", "weather sensitivity", "equipment protection"],
            "desert": ["sand", "heat", "visibility", "water requirements"],
            "grassland": ["wind", "weather changes"]
        }
        return challenges.get(terrain_type, ["unknown conditions"])
    
    def _get_pattern_use_cases(self, pattern_type: str) -> List[str]:
        """Get typical use cases for search pattern"""
        use_cases = {
            "grid": ["systematic coverage", "large areas", "thorough search"],
            "spiral": ["focused search", "central point", "expanding search"],
            "sector": ["divided areas", "multiple teams", "parallel search"],
            "lawnmower": ["efficient coverage", "rectangular areas", "minimal overlap"]
        }
        return use_cases.get(pattern_type, ["general search"])
    
    async def _process_lesson_learned(self, lesson: str, mission_id: str, outcome_id: str):
        """Process a lesson learned and create appropriate nodes and relationships"""
        try:
            # Create lesson node
            lesson_node_id = f"lesson_{uuid.uuid4()}"
            lesson_node = GraphNode(
                node_id=lesson_node_id,
                node_type=NodeType.LESSON,
                properties={
                    "lesson_text": lesson,
                    "category": self._categorize_lesson(lesson),
                    "importance": self._assess_lesson_importance(lesson),
                    "applicability": self._assess_lesson_applicability(lesson)
                },
                confidence=0.8,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            await self._add_node(lesson_node)
            
            # Create relationships
            # Mission -> Lesson
            mission_lesson_rel = GraphRelationship(
                relationship_id=f"{mission_id}_generates_{lesson_node_id}",
                source_node_id=mission_id,
                target_node_id=lesson_node_id,
                relationship_type=RelationshipType.LEADS_TO,
                strength=1.0,
                confidence=0.9,
                evidence=[f"Mission generated lesson: {lesson}"],
                evidence_count=1,
                created_at=datetime.utcnow(),
                last_verified=datetime.utcnow()
            )
            await self._add_relationship(mission_lesson_rel)
            
            # Lesson -> Outcome
            lesson_outcome_rel = GraphRelationship(
                relationship_id=f"{lesson_node_id}_influences_{outcome_id}",
                source_node_id=lesson_node_id,
                target_node_id=outcome_id,
                relationship_type=RelationshipType.INFLUENCES,
                strength=lesson_node.properties["importance"],
                confidence=0.7,
                evidence=[f"Lesson influenced outcome: {lesson}"],
                evidence_count=1,
                created_at=datetime.utcnow(),
                last_verified=datetime.utcnow()
            )
            await self._add_relationship(lesson_outcome_rel)
            
        except Exception as e:
            logger.error(f"Failed to process lesson learned: {e}")
    
    def _categorize_lesson(self, lesson: str) -> str:
        """Categorize lesson based on content"""
        lesson_lower = lesson.lower()
        
        if any(word in lesson_lower for word in ["battery", "power", "energy"]):
            return "power_management"
        elif any(word in lesson_lower for word in ["weather", "wind", "rain"]):
            return "weather_conditions"
        elif any(word in lesson_lower for word in ["terrain", "landing", "obstacle"]):
            return "terrain_handling"
        elif any(word in lesson_lower for word in ["communication", "signal", "connection"]):
            return "communication"
        elif any(word in lesson_lower for word in ["pattern", "search", "coverage"]):
            return "search_strategy"
        else:
            return "general"
    
    def _assess_lesson_importance(self, lesson: str) -> float:
        """Assess importance of lesson (0.0 to 1.0)"""
        lesson_lower = lesson.lower()
        
        # High importance keywords
        high_importance = ["critical", "essential", "vital", "crucial", "must", "always", "never"]
        medium_importance = ["important", "recommended", "should", "consider"]
        low_importance = ["minor", "optional", "might", "could"]
        
        if any(word in lesson_lower for word in high_importance):
            return 0.9
        elif any(word in lesson_lower for word in medium_importance):
            return 0.6
        elif any(word in lesson_lower for word in low_importance):
            return 0.3
        else:
            return 0.5  # Default importance
    
    def _assess_lesson_applicability(self, lesson: str) -> List[str]:
        """Assess applicability of lesson to different scenarios"""
        lesson_lower = lesson.lower()
        applicability = []
        
        if any(word in lesson_lower for word in ["mountain", "high altitude"]):
            applicability.append("mountain")
        if any(word in lesson_lower for word in ["forest", "trees", "vegetation"]):
            applicability.append("forest")
        if any(word in lesson_lower for word in ["urban", "city", "buildings"]):
            applicability.append("urban")
        if any(word in lesson_lower for word in ["water", "lake", "river"]):
            applicability.append("water")
        if any(word in lesson_lower for word in ["desert", "sand", "arid"]):
            applicability.append("desert")
        
        return applicability if applicability else ["general"]
    
    def _matches_constraints(self, node_data: Dict[str, Any], constraints: Dict[str, Any]) -> bool:
        """Check if node data matches query constraints"""
        for key, value in constraints.items():
            if key in node_data:
                if isinstance(value, dict) and isinstance(node_data[key], dict):
                    # For nested dictionaries (like weather_conditions)
                    if not self._matches_constraints(node_data[key], value):
                        return False
                elif node_data[key] != value:
                    return False
        return True
    
    def _calculate_pattern_effectiveness(self, pattern_id: str, outcome_nodes: List[str]) -> float:
        """Calculate effectiveness of a pattern based on outcomes"""
        if not outcome_nodes:
            return 0.0
        
        total_success = 0.0
        for outcome_id in outcome_nodes:
            outcome_data = self.memory_graph.nodes[outcome_id]
            success_rate = outcome_data.get("success_rate", 0.0)
            total_success += success_rate
        
        return total_success / len(outcome_nodes)
    
    def _get_pattern_evidence(self, pattern_id: str) -> List[str]:
        """Get evidence supporting pattern effectiveness"""
        evidence = []
        pattern_data = self.memory_graph.nodes[pattern_id]
        
        # Find missions that used this pattern
        for mission_id in self.memory_graph.predecessors(pattern_id):
            mission_data = self.memory_graph.nodes[mission_id]
            if mission_data.get("node_type") == "mission":
                evidence.append(f"Used in mission {mission_data.get('mission_id', 'unknown')}")
        
        return evidence[:5]  # Limit to 5 pieces of evidence
    
    def _generate_optimization_recommendation(self, factor_type: str, factor: str, potential: float) -> str:
        """Generate optimization recommendation based on factor analysis"""
        if factor_type == "pattern":
            return f"Consider alternative search patterns. Current pattern shows {potential:.1%} optimization potential."
        elif factor_type == "terrain":
            return f"Optimize terrain-specific strategies. Current approach has {potential:.1%} improvement potential."
        elif factor_type == "mission":
            return f"Review mission parameters. Current configuration has {potential:.1%} optimization potential."
        else:
            return f"Optimize {factor_type} approach. Potential improvement: {potential:.1%}"
    
    def _calculate_mission_similarity(self, mission_data: Dict[str, Any], constraints: Dict[str, Any]) -> float:
        """Calculate similarity between mission data and query constraints"""
        similarity_score = 0.0
        total_factors = 0
        
        # Terrain similarity
        if "terrain_type" in constraints:
            total_factors += 1
            if mission_data.get("terrain_type") == constraints["terrain_type"]:
                similarity_score += 1.0
            else:
                similarity_score += 0.0
        
        # Pattern similarity
        if "search_pattern" in constraints:
            total_factors += 1
            if mission_data.get("search_pattern") == constraints["search_pattern"]:
                similarity_score += 1.0
            else:
                similarity_score += 0.0
        
        # Weather similarity (simplified)
        if "weather_conditions" in constraints:
            total_factors += 1
            mission_weather = mission_data.get("weather_conditions", {})
            query_weather = constraints["weather_conditions"]
            
            weather_similarity = 0.0
            weather_factors = 0
            
            for key in ["wind_speed", "visibility", "precipitation"]:
                if key in query_weather and key in mission_weather:
                    weather_factors += 1
                    # Simple similarity based on value proximity
                    query_val = query_weather[key]
                    mission_val = mission_weather[key]
                    if isinstance(query_val, (int, float)) and isinstance(mission_val, (int, float)):
                        diff = abs(query_val - mission_val)
                        max_val = max(query_val, mission_val, 1)
                        weather_similarity += max(0, 1 - (diff / max_val))
            
            if weather_factors > 0:
                similarity_score += weather_similarity / weather_factors
        
        return similarity_score / total_factors if total_factors > 0 else 0.0
    
    def _identify_risk_factors(self, constraints: Dict[str, Any]) -> List[str]:
        """Identify risk factors based on constraints"""
        risks = []
        
        terrain_type = constraints.get("terrain_type", "unknown")
        if terrain_type in ["mountain", "water"]:
            risks.append("High difficulty terrain")
        
        weather = constraints.get("weather_conditions", {})
        if weather.get("wind_speed", 0) > 10:
            risks.append("High wind conditions")
        if weather.get("visibility", 10) < 3:
            risks.append("Poor visibility")
        
        return risks
    
    def _identify_success_factors(self, constraints: Dict[str, Any]) -> List[str]:
        """Identify success factors based on constraints"""
        factors = []
        
        terrain_type = constraints.get("terrain_type", "unknown")
        if terrain_type in ["grassland", "desert"]:
            factors.append("Favorable terrain conditions")
        
        pattern = constraints.get("search_pattern", "unknown")
        if pattern in ["grid", "lawnmower"]:
            factors.append("Systematic search pattern")
        
        return factors
    
    def _calculate_strategy_confidence(self, pattern_recs: List[Dict], optimization_opps: List[Dict]) -> float:
        """Calculate overall confidence in strategy recommendation"""
        if not pattern_recs and not optimization_opps:
            return 0.0
        
        confidence = 0.0
        
        if pattern_recs:
            pattern_confidence = sum(rec["effectiveness"] for rec in pattern_recs) / len(pattern_recs)
            confidence += pattern_confidence * 0.6
        
        if optimization_opps:
            opt_confidence = sum(opp["optimization_potential"] for opp in optimization_opps) / len(optimization_opps)
            confidence += opt_confidence * 0.4
        
        return min(confidence, 1.0)
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        try:
            stats = {
                "total_nodes": len(self.node_cache),
                "total_relationships": len(self.relationship_cache),
                "node_types": {},
                "relationship_types": {},
                "average_confidence": 0.0,
                "graph_density": 0.0
            }
            
            # Node type distribution
            for node in self.node_cache.values():
                node_type = node.node_type.value
                stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1
            
            # Relationship type distribution
            for rel in self.relationship_cache.values():
                rel_type = rel.relationship_type.value
                stats["relationship_types"][rel_type] = stats["relationship_types"].get(rel_type, 0) + 1
            
            # Average confidence
            if self.node_cache:
                total_confidence = sum(node.confidence for node in self.node_cache.values())
                stats["average_confidence"] = total_confidence / len(self.node_cache)
            
            # Graph density
            if len(self.node_cache) > 1:
                max_possible_edges = len(self.node_cache) * (len(self.node_cache) - 1)
                stats["graph_density"] = len(self.relationship_cache) / max_possible_edges
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {"error": str(e)}

# Global knowledge graph instance
knowledge_graph = SARKnowledgeGraph()
