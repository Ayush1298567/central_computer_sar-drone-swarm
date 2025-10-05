"""
Production-grade RAG (Retrieval-Augmented Generation) system for SAR operations
Provides semantic search, knowledge retrieval, and contextual AI responses
"""
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, SearchRequest
from sentence_transformers import SentenceTransformer
import logging
from datetime import datetime, timedelta
import json
import uuid
from dataclasses import dataclass
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    MISSION_PATTERN = "mission_pattern"
    TERRAIN_KNOWLEDGE = "terrain_knowledge"
    WEATHER_IMPACT = "weather_impact"
    DRONE_PERFORMANCE = "drone_performance"
    EMERGENCY_PROCEDURES = "emergency_procedures"
    LESSONS_LEARNED = "lessons_learned"
    OPTIMIZATION_TIPS = "optimization_tips"
    REGULATORY_INFO = "regulatory_info"

@dataclass
class KnowledgeDocument:
    """Represents a knowledge document in the RAG system"""
    id: str
    content_type: KnowledgeType
    title: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]
    confidence_score: float = 1.0
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class SearchResult:
    """Search result with relevance scoring"""
    document: KnowledgeDocument
    similarity_score: float
    relevance_score: float
    explanation: str

class SARKnowledgeRAG:
    """Production-grade RAG system for SAR operations with advanced semantic search"""
    
    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        
        # Collection names for different knowledge types
        self.collections = {
            KnowledgeType.MISSION_PATTERN: "sar_mission_patterns",
            KnowledgeType.TERRAIN_KNOWLEDGE: "sar_terrain_knowledge", 
            KnowledgeType.WEATHER_IMPACT: "sar_weather_impact",
            KnowledgeType.DRONE_PERFORMANCE: "sar_drone_performance",
            KnowledgeType.EMERGENCY_PROCEDURES: "sar_emergency_procedures",
            KnowledgeType.LESSONS_LEARNED: "sar_lessons_learned",
            KnowledgeType.OPTIMIZATION_TIPS: "sar_optimization_tips",
            KnowledgeType.REGULATORY_INFO: "sar_regulatory_info"
        }
        
        # Initialize collections
        asyncio.create_task(self._initialize_collections())
    
    async def _initialize_collections(self):
        """Initialize all Qdrant collections with optimized configuration"""
        try:
            for collection_name in self.collections.values():
                await self._create_collection(collection_name)
            
            # Create unified search collection
            await self._create_collection("sar_unified_knowledge")
            
            logger.info("RAG collections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG collections: {e}")
            raise
    
    async def _create_collection(self, collection_name: str):
        """Create a Qdrant collection with production-optimized configuration"""
        try:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                ),
                hnsw_config={
                    "m": 16,  # Number of bi-directional links for each node
                    "ef_construct": 200,  # Size of dynamic candidate list during construction
                    "full_scan_threshold": 10000,
                    "max_indexing_threads": 4
                },
                optimizers_config={
                    "default_segment_number": 2,
                    "max_segment_size": 20000,
                    "memmap_threshold": 50000,
                    "indexing_threshold": 10000
                },
                quantization_config=None  # Use default quantization
            )
            logger.info(f"Created collection: {collection_name}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"Collection {collection_name} already exists")
            else:
                raise
    
    async def store_mission_knowledge(
        self, 
        mission_data: Dict[str, Any],
        outcomes: Dict[str, Any],
        lessons_learned: str,
        knowledge_type: KnowledgeType = KnowledgeType.LESSONS_LEARNED
    ) -> str:
        """Store mission knowledge in vector database with comprehensive metadata"""
        try:
            # Create comprehensive knowledge document
            doc_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            knowledge_doc = {
                "id": doc_id,
                "mission_id": mission_data.get("mission_id"),
                "mission_type": mission_data.get("mission_type"),
                "terrain_type": mission_data.get("terrain_type"),
                "weather_conditions": mission_data.get("weather_conditions"),
                "search_pattern": mission_data.get("search_pattern"),
                "drone_count": mission_data.get("drone_count"),
                "search_area_size": mission_data.get("search_area_size"),
                "duration_hours": mission_data.get("duration_hours"),
                
                # Outcomes and performance
                "success_rate": outcomes.get("success_rate", 0.0),
                "discoveries_made": outcomes.get("discoveries_count", 0),
                "mission_duration": outcomes.get("duration_minutes", 0),
                "area_covered": outcomes.get("area_covered", 0.0),
                "efficiency_score": outcomes.get("efficiency_score", 0.0),
                "battery_usage": outcomes.get("avg_battery_usage", 0.0),
                
                # Knowledge content
                "lessons_learned": lessons_learned,
                "optimal_parameters": outcomes.get("optimal_parameters", {}),
                "failure_points": outcomes.get("failure_points", []),
                "success_factors": outcomes.get("success_factors", []),
                "recommendations": outcomes.get("recommendations", []),
                
                # Metadata
                "knowledge_type": knowledge_type.value,
                "confidence_score": self._calculate_knowledge_confidence(outcomes),
                "sample_size": outcomes.get("sample_size", 1),
                "created_at": timestamp.isoformat(),
                "updated_at": timestamp.isoformat(),
                
                # Searchable text
                "searchable_text": self._generate_searchable_text(mission_data, outcomes, lessons_learned)
            }
            
            # Generate embedding from comprehensive text
            embedding_text = self._generate_embedding_text(mission_data, outcomes, lessons_learned)
            embedding = self.embedding_model.encode(embedding_text).tolist()
            
            # Store in specific collection
            collection_name = self.collections[knowledge_type]
            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload=knowledge_doc
            )
            
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            # Also store in unified collection for cross-type search
            unified_point = PointStruct(
                id=f"{knowledge_type.value}_{doc_id}",
                vector=embedding,
                payload={**knowledge_doc, "primary_collection": collection_name}
            )
            
            self.qdrant_client.upsert(
                collection_name="sar_unified_knowledge",
                points=[unified_point]
            )
            
            logger.info(f"Stored mission knowledge: {doc_id} in {collection_name}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to store mission knowledge: {e}")
            raise
    
    async def retrieve_relevant_context(
        self, 
        query: str, 
        knowledge_types: List[KnowledgeType] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        context_window: int = 3
    ) -> List[SearchResult]:
        """Advanced context retrieval with multi-type search and relevance scoring"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            all_results = []
            
            # Search in specific collections if types specified
            if knowledge_types:
                for knowledge_type in knowledge_types:
                    collection_name = self.collections[knowledge_type]
                    results = await self._search_collection(
                        collection_name, query_embedding, limit, similarity_threshold
                    )
                    all_results.extend(results)
            else:
                # Search in unified collection for cross-type relevance
                results = await self._search_collection(
                    "sar_unified_knowledge", query_embedding, limit * 2, similarity_threshold
                )
                all_results.extend(results)
            
            # Advanced relevance scoring and ranking
            scored_results = []
            for result in all_results:
                relevance_score = self._calculate_relevance_score(query, result.payload)
                explanation = self._generate_relevance_explanation(query, result.payload, result.score)
                
                search_result = SearchResult(
                    document=self._payload_to_document(result.payload),
                    similarity_score=result.score,
                    relevance_score=relevance_score,
                    explanation=explanation
                )
                scored_results.append(search_result)
            
            # Sort by combined score and apply context window
            scored_results.sort(key=lambda x: x.similarity_score * x.relevance_score, reverse=True)
            
            # Apply diversity filtering to avoid redundant results
            diversified_results = self._apply_diversity_filtering(scored_results, context_window)
            
            logger.info(f"Retrieved {len(diversified_results)} relevant contexts for query")
            return diversified_results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant context: {e}")
            return []
    
    async def _search_collection(
        self, 
        collection_name: str, 
        query_embedding: List[float], 
        limit: int, 
        threshold: float
    ) -> List:
        """Search a specific collection with advanced filtering"""
        try:
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=threshold,
                with_payload=True,
                with_vectors=False
            )
            return search_results
        except Exception as e:
            logger.error(f"Search failed for collection {collection_name}: {e}")
            return []
    
    async def generate_contextual_response(
        self, 
        user_query: str, 
        mission_context: Dict[str, Any],
        llm_client,
        include_explanations: bool = True
    ) -> Dict[str, Any]:
        """Generate AI response augmented with relevant knowledge and explanations"""
        try:
            # Retrieve relevant context with diverse knowledge types
            relevant_contexts = await self.retrieve_relevant_context(
                query=user_query,
                knowledge_types=None,  # Search all types
                limit=5,
                similarity_threshold=0.6
            )
            
            if not relevant_contexts:
                logger.warning("No relevant context found for query")
                return await self._generate_fallback_response(user_query, mission_context, llm_client)
            
            # Build context-augmented prompt
            context_text = self._build_context_text(relevant_contexts, include_explanations)
            
            augmented_prompt = f"""
            You are an expert SAR mission commander with access to comprehensive historical mission data and domain knowledge.

            CURRENT MISSION CONTEXT:
            {json.dumps(mission_context, indent=2)}

            RELEVANT HISTORICAL KNOWLEDGE:
            {context_text}

            USER QUERY: {user_query}

            Based on the current context and historical knowledge above, provide:
            1. Specific, actionable recommendations
            2. Risk assessment and mitigation strategies
            3. Optimal parameters and configurations
            4. Contingency plans and alternatives
            5. Expected outcomes and success metrics

            Reference specific historical patterns and lessons learned where applicable.
            Provide confidence levels for your recommendations.
            """
            
            # Generate response using LLM
            response = await llm_client.generate(
                prompt=augmented_prompt,
                system="You are an expert SAR mission commander with access to historical mission data and proven strategies."
            )
            
            # Calculate response confidence based on context quality
            response_confidence = self._calculate_response_confidence(relevant_contexts)
            
            # Generate explanations for transparency
            explanations = []
            if include_explanations:
                explanations = [
                    {
                        "source": ctx.document.title,
                        "relevance": ctx.relevance_score,
                        "explanation": ctx.explanation,
                        "knowledge_type": ctx.document.content_type.value
                    }
                    for ctx in relevant_contexts[:3]
                ]
            
            return {
                "response": response,
                "confidence": response_confidence,
                "context_sources": len(relevant_contexts),
                "explanations": explanations,
                "knowledge_types_used": list(set(ctx.document.content_type.value for ctx in relevant_contexts)),
                "response_metadata": {
                    "generation_time": datetime.utcnow().isoformat(),
                    "query_complexity": self._assess_query_complexity(user_query),
                    "context_quality": np.mean([ctx.relevance_score for ctx in relevant_contexts])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate contextual response: {e}")
            raise
    
    async def _generate_fallback_response(
        self, 
        user_query: str, 
        mission_context: Dict[str, Any], 
        llm_client
    ) -> Dict[str, Any]:
        """Generate fallback response when no relevant context is found"""
        fallback_prompt = f"""
        You are an expert SAR mission commander providing guidance based on general best practices.

        MISSION CONTEXT:
        {json.dumps(mission_context, indent=2)}

        USER QUERY: {user_query}

        Provide recommendations based on SAR best practices and general operational knowledge.
        Note that specific historical data is not available for this query.
        """
        
        response = await llm_client.generate(
            prompt=fallback_prompt,
            system="You are an expert SAR mission commander with extensive SAR operational knowledge."
        )
        
        return {
            "response": response,
            "confidence": 0.3,  # Lower confidence for fallback
            "context_sources": 0,
            "explanations": [],
            "knowledge_types_used": [],
            "fallback": True,
            "response_metadata": {
                "generation_time": datetime.utcnow().isoformat(),
                "fallback_reason": "No relevant historical context found"
            }
        }
    
    def _calculate_knowledge_confidence(self, outcomes: Dict[str, Any]) -> float:
        """Calculate confidence score for stored knowledge"""
        confidence_factors = []
        
        # Sample size factor
        sample_size = outcomes.get("sample_size", 1)
        sample_confidence = min(sample_size / 10, 1.0)  # Max confidence at 10+ samples
        confidence_factors.append(sample_confidence)
        
        # Success rate factor
        success_rate = outcomes.get("success_rate", 0.0)
        confidence_factors.append(success_rate)
        
        # Data completeness factor
        required_fields = ["success_rate", "discoveries_count", "duration_minutes", "area_covered"]
        completeness = sum(1 for field in required_fields if field in outcomes) / len(required_fields)
        confidence_factors.append(completeness)
        
        # Consistency factor (if multiple missions)
        if sample_size > 1:
            consistency = 1.0 - outcomes.get("variance_score", 0.3)  # Lower variance = higher consistency
            confidence_factors.append(max(consistency, 0.0))
        
        return np.mean(confidence_factors)
    
    def _generate_searchable_text(
        self, 
        mission_data: Dict[str, Any], 
        outcomes: Dict[str, Any], 
        lessons_learned: str
    ) -> str:
        """Generate comprehensive searchable text for the knowledge document"""
        text_parts = [
            f"Mission Type: {mission_data.get('mission_type', 'unknown')}",
            f"Terrain: {mission_data.get('terrain_type', 'unknown')}",
            f"Search Pattern: {mission_data.get('search_pattern', 'unknown')}",
            f"Drones Used: {mission_data.get('drone_count', 'unknown')}",
            f"Success Rate: {outcomes.get('success_rate', 0):.2%}",
            f"Discoveries: {outcomes.get('discoveries_count', 0)}",
            f"Duration: {outcomes.get('duration_minutes', 0)} minutes",
            f"Area Covered: {outcomes.get('area_covered', 0):.2f} km²",
            f"Lessons Learned: {lessons_learned}"
        ]
        
        # Add weather information
        if mission_data.get("weather_conditions"):
            weather = mission_data["weather_conditions"]
            text_parts.append(f"Weather: {weather.get('condition', 'unknown')}")
            if weather.get("wind_speed"):
                text_parts.append(f"Wind Speed: {weather['wind_speed']} m/s")
        
        # Add optimization tips
        if outcomes.get("optimal_parameters"):
            text_parts.append(f"Optimal Parameters: {json.dumps(outcomes['optimal_parameters'])}")
        
        return " | ".join(text_parts)
    
    def _generate_embedding_text(
        self, 
        mission_data: Dict[str, Any], 
        outcomes: Dict[str, Any], 
        lessons_learned: str
    ) -> str:
        """Generate text optimized for embedding generation"""
        return f"""
        {mission_data.get('mission_type', '')} mission in {mission_data.get('terrain_type', '')} terrain.
        Used {mission_data.get('search_pattern', '')} search pattern with {mission_data.get('drone_count', 0)} drones.
        Achieved {outcomes.get('success_rate', 0):.1%} success rate with {outcomes.get('discoveries_count', 0)} discoveries.
        Mission duration: {outcomes.get('duration_minutes', 0)} minutes.
        Area covered: {outcomes.get('area_covered', 0):.1f} km².
        {lessons_learned}
        """
    
    def _calculate_relevance_score(self, query: str, document_payload: Dict[str, Any]) -> float:
        """Calculate relevance score between query and document"""
        query_terms = set(query.lower().split())
        document_text = str(document_payload).lower()
        
        # Term frequency scoring
        term_matches = sum(1 for term in query_terms if term in document_text)
        term_score = term_matches / len(query_terms) if query_terms else 0.0
        
        # Semantic similarity (already calculated by Qdrant)
        semantic_score = 1.0  # Placeholder - would use actual similarity score
        
        # Knowledge quality scoring
        confidence = document_payload.get("confidence_score", 0.5)
        sample_size = document_payload.get("sample_size", 1)
        quality_score = confidence * (1 + 0.1 * min(sample_size, 10))
        
        # Combine scores
        relevance_score = (0.4 * term_score + 0.4 * semantic_score + 0.2 * quality_score)
        
        return min(relevance_score, 1.0)
    
    def _generate_relevance_explanation(
        self, 
        query: str, 
        document_payload: Dict[str, Any], 
        similarity_score: float
    ) -> str:
        """Generate human-readable explanation of why this document is relevant"""
        explanations = []
        
        # Mission type match
        if "mission" in query.lower() and document_payload.get("mission_type"):
            explanations.append(f"Matches mission type: {document_payload['mission_type']}")
        
        # Terrain match
        if any(terrain in query.lower() for terrain in ["forest", "mountain", "urban", "water", "desert"]):
            terrain = document_payload.get("terrain_type")
            if terrain and terrain.lower() in query.lower():
                explanations.append(f"Matches terrain type: {terrain}")
        
        # Success rate relevance
        if "success" in query.lower() and document_payload.get("success_rate"):
            success_rate = document_payload["success_rate"]
            explanations.append(f"Shows {success_rate:.1%} success rate")
        
        # Pattern relevance
        if "pattern" in query.lower() and document_payload.get("search_pattern"):
            pattern = document_payload["search_pattern"]
            explanations.append(f"Uses {pattern} search pattern")
        
        # Lessons learned relevance
        if "lesson" in query.lower() and document_payload.get("lessons_learned"):
            explanations.append("Contains lessons learned")
        
        # Default explanation
        if not explanations:
            explanations.append(f"Semantic similarity: {similarity_score:.2f}")
        
        return "; ".join(explanations)
    
    def _apply_diversity_filtering(self, results: List[SearchResult], max_similar: int) -> List[SearchResult]:
        """Apply diversity filtering to avoid redundant results"""
        if len(results) <= max_similar:
            return results
        
        diversified = []
        seen_patterns = set()
        
        for result in results:
            # Check for pattern diversity
            pattern = result.document.metadata.get("search_pattern", "unknown")
            mission_type = result.document.metadata.get("mission_type", "unknown")
            terrain_type = result.document.metadata.get("terrain_type", "unknown")
            
            pattern_key = f"{mission_type}_{terrain_type}_{pattern}"
            
            if pattern_key not in seen_patterns or len(diversified) < max_similar:
                diversified.append(result)
                seen_patterns.add(pattern_key)
            
            if len(diversified) >= max_similar:
                break
        
        return diversified
    
    def _build_context_text(self, contexts: List[SearchResult], include_explanations: bool) -> str:
        """Build formatted context text for the LLM prompt"""
        context_parts = []
        
        for i, ctx in enumerate(contexts, 1):
            doc = ctx.document
            context_text = f"""
            {i}. {doc.title} (Relevance: {ctx.relevance_score:.2f})
               Mission Type: {doc.metadata.get('mission_type', 'Unknown')}
               Terrain: {doc.metadata.get('terrain_type', 'Unknown')}
               Success Rate: {doc.metadata.get('success_rate', 0):.1%}
               Key Insights: {doc.content[:200]}...
            """
            
            if include_explanations:
                context_text += f"   Why Relevant: {ctx.explanation}\n"
            
            context_parts.append(context_text)
        
        return "\n".join(context_parts)
    
    def _calculate_response_confidence(self, contexts: List[SearchResult]) -> float:
        """Calculate confidence in AI response based on context quality"""
        if not contexts:
            return 0.0
        
        # Average relevance score
        avg_relevance = np.mean([ctx.relevance_score for ctx in contexts])
        
        # Context diversity (more diverse = higher confidence)
        knowledge_types = set(ctx.document.content_type.value for ctx in contexts)
        diversity_score = len(knowledge_types) / len(KnowledgeType)
        
        # Knowledge quality
        avg_confidence = np.mean([ctx.document.confidence_score for ctx in contexts])
        
        # Combined confidence
        response_confidence = (0.5 * avg_relevance + 0.3 * diversity_score + 0.2 * avg_confidence)
        
        return min(response_confidence, 1.0)
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess the complexity of the user query"""
        query_length = len(query.split())
        
        if query_length < 5:
            return "simple"
        elif query_length < 15:
            return "moderate"
        else:
            return "complex"
    
    def _payload_to_document(self, payload: Dict[str, Any]) -> KnowledgeDocument:
        """Convert Qdrant payload to KnowledgeDocument"""
        return KnowledgeDocument(
            id=payload.get("id", ""),
            content_type=KnowledgeType(payload.get("knowledge_type", "lessons_learned")),
            title=f"{payload.get('mission_type', 'Mission')} - {payload.get('terrain_type', 'Unknown Terrain')}",
            content=payload.get("lessons_learned", ""),
            metadata=payload,
            embedding=[],  # Not needed for search results
            confidence_score=payload.get("confidence_score", 0.5),
            created_at=datetime.fromisoformat(payload.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(payload.get("updated_at", datetime.utcnow().isoformat()))
        )
    
    async def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            stats = {}
            
            for knowledge_type, collection_name in self.collections.items():
                collection_info = self.qdrant_client.get_collection(collection_name)
                stats[knowledge_type.value] = {
                    "points_count": collection_info.points_count,
                    "indexed_vectors_count": collection_info.indexed_vectors_count,
                    "status": collection_info.status
                }
            
            # Unified collection stats
            unified_info = self.qdrant_client.get_collection("sar_unified_knowledge")
            stats["unified"] = {
                "points_count": unified_info.points_count,
                "indexed_vectors_count": unified_info.indexed_vectors_count,
                "status": unified_info.status
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get knowledge statistics: {e}")
            return {}

# Global RAG instance
sar_rag = SARKnowledgeRAG()
