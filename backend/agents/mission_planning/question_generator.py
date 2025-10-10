"""
Question Generator for AI Mission Planning
Generates intelligent questions to extract mission requirements from natural language.
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.ai.ollama_client import ollama_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """Real AI-driven question generation using Ollama"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.question_templates = self._load_question_templates()
        self.context_memory = {}
        
    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question templates for different mission aspects"""
        return {
            'location': [
                "What is the specific search area or location?",
                "Can you provide coordinates or a landmark for the search area?",
                "What are the boundaries of the area that needs to be searched?",
                "Is this a specific address, park, wilderness area, or other location?",
                "What city, state, or region is the search area in?"
            ],
            'urgency': [
                "How urgent is this search mission?",
                "Is this a life-threatening emergency or a routine search?",
                "What is the time sensitivity of this mission?",
                "Are there any time constraints or deadlines?",
                "How quickly does this need to be completed?"
            ],
            'target': [
                "What or who are we searching for?",
                "Can you describe the person, object, or target of the search?",
                "What are the distinguishing characteristics of what we're looking for?",
                "Are there any specific features or details that would help identify the target?",
                "What size, color, or other attributes should we look for?"
            ],
            'environment': [
                "What type of terrain or environment is the search area?",
                "Are there any obstacles, hazards, or difficult terrain?",
                "What is the weather condition in the search area?",
                "Is this an urban, rural, forest, water, or other type of environment?",
                "Are there any access restrictions or special considerations?"
            ],
            'resources': [
                "How many drones should be used for this mission?",
                "What is the preferred search pattern or approach?",
                "Are there any specific equipment or sensor requirements?",
                "What altitude should the drones fly at?",
                "How long should the search operation last?"
            ],
            'constraints': [
                "Are there any legal or regulatory restrictions?",
                "What are the safety requirements for this mission?",
                "Are there any privacy concerns or restricted areas?",
                "What is the budget or resource limit for this operation?",
                "Are there any specific protocols or procedures to follow?"
            ]
        }
    
    async def generate_initial_questions(self, user_input: str) -> List[Dict[str, Any]]:
        """
        Generate initial questions based on user input using AI analysis.
        
        Args:
            user_input: The user's initial message or request
            
        Returns:
            List of question dictionaries with AI-generated questions
        """
        try:
            # Analyze user input to determine what information is missing
            analysis_prompt = f"""
            Analyze this search and rescue mission request and determine what critical information is missing.
            The user said: "{user_input}"
            
            Consider these aspects:
            - Location details (coordinates, boundaries, landmarks)
            - Urgency level (emergency, routine, time-sensitive)
            - Target description (person, object, characteristics)
            - Environment (terrain, weather, obstacles)
            - Resource requirements (drones, equipment, duration)
            - Constraints (legal, safety, privacy, budget)
            
            Return a JSON response with:
            {{
                "missing_aspects": ["list", "of", "missing", "aspects"],
                "urgency_score": 0.0-1.0,
                "complexity_score": 0.0-1.0,
                "confidence": 0.0-1.0
            }}
            """
            
            # Get AI analysis
            analysis_response = await ollama_client.generate(
                analysis_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.3
            )
            
            # Parse AI response
            try:
                analysis = json.loads(analysis_response)
            except json.JSONDecodeError:
                # Fallback analysis if JSON parsing fails
                analysis = {
                    "missing_aspects": ["location", "target", "urgency"],
                    "urgency_score": 0.5,
                    "complexity_score": 0.5,
                    "confidence": 0.3
                }
            
            # Generate questions based on missing aspects
            questions = []
            missing_aspects = analysis.get("missing_aspects", [])
            
            for aspect in missing_aspects[:3]:  # Limit to 3 most important aspects
                if aspect in self.question_templates:
                    # Use AI to generate a specific question for this aspect
                    question_prompt = f"""
                    Generate a specific, clear question to ask the user about {aspect} for their search and rescue mission.
                    The user's request was: "{user_input}"
                    
                    The question should:
                    - Be conversational and easy to understand
                    - Be specific to their situation
                    - Help gather the missing {aspect} information
                    - Be professional but friendly
                    
                    Return only the question text, no additional formatting.
                    """
                    
                    ai_question = await ollama_client.generate(
                        question_prompt,
                        model=settings.DEFAULT_MODEL,
                        temperature=0.7
                    )
                    
                    # Clean up the response
                    ai_question = ai_question.strip().strip('"').strip("'")
                    
                    questions.append({
                        'id': f"q_{len(questions)}",
                        'aspect': aspect,
                        'question': ai_question,
                        'priority': self._calculate_question_priority(aspect, analysis),
                        'context': user_input,
                        'generated_at': datetime.utcnow().isoformat()
                    })
            
            # Add fallback questions if AI didn't generate enough
            if len(questions) < 2:
                questions.extend(self._generate_fallback_questions(user_input, missing_aspects))
            
            self.logger.info(f"Generated {len(questions)} initial questions for user input")
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generating initial questions: {e}", exc_info=True)
            return self._generate_fallback_questions(user_input, ["location", "target", "urgency"])
    
    async def generate_follow_up_questions(self, conversation_history: List[Dict[str, Any]], 
                                         current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate follow-up questions based on conversation history and current context.
        
        Args:
            conversation_history: List of previous messages in the conversation
            current_context: Current mission context and extracted information
            
        Returns:
            List of follow-up question dictionaries
        """
        try:
            # Analyze conversation to find gaps
            conversation_text = self._format_conversation_history(conversation_history)
            
            analysis_prompt = f"""
            Analyze this search and rescue mission conversation and identify what information is still missing.
            
            Conversation:
            {conversation_text}
            
            Current context:
            {json.dumps(current_context, indent=2)}
            
            Determine what additional information is needed to create a complete mission plan.
            Focus on:
            - Specific details that are still vague
            - Technical requirements that haven't been specified
            - Safety considerations that need clarification
            - Operational parameters that are missing
            
            Return a JSON response with:
            {{
                "missing_details": ["list", "of", "specific", "missing", "details"],
                "priority_areas": ["list", "of", "high", "priority", "areas"],
                "suggested_questions": ["list", "of", "suggested", "question", "topics"]
            }}
            """
            
            # Get AI analysis
            analysis_response = await ollama_client.generate(
                analysis_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.3
            )
            
            try:
                analysis = json.loads(analysis_response)
            except json.JSONDecodeError:
                analysis = {
                    "missing_details": ["specific location coordinates", "target description"],
                    "priority_areas": ["location", "target"],
                    "suggested_questions": ["location", "target"]
                }
            
            # Generate specific follow-up questions
            questions = []
            missing_details = analysis.get("missing_details", [])
            priority_areas = analysis.get("priority_areas", [])
            
            for i, detail in enumerate(missing_details[:2]):  # Limit to 2 follow-up questions
                question_prompt = f"""
                Generate a specific follow-up question to clarify: {detail}
                
                Based on this conversation context:
                {conversation_text}
                
                The question should:
                - Be specific and direct
                - Build on what's already been discussed
                - Help clarify the missing detail
                - Be conversational and not repetitive
                
                Return only the question text.
                """
                
                ai_question = await ollama_client.generate(
                    question_prompt,
                    model=settings.DEFAULT_MODEL,
                    temperature=0.6
                )
                
                ai_question = ai_question.strip().strip('"').strip("'")
                
                questions.append({
                    'id': f"followup_{len(questions)}",
                    'aspect': detail,
                    'question': ai_question,
                    'priority': 0.8,  # High priority for follow-ups
                    'context': current_context,
                    'conversation_id': len(conversation_history),
                    'generated_at': datetime.utcnow().isoformat()
                })
            
            self.logger.info(f"Generated {len(questions)} follow-up questions")
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generating follow-up questions: {e}", exc_info=True)
            return []
    
    async def generate_clarification_questions(self, extracted_info: Dict[str, Any], 
                                             confidence_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Generate clarification questions for low-confidence extracted information.
        
        Args:
            extracted_info: Information extracted from conversation
            confidence_threshold: Minimum confidence score for information
            
        Returns:
            List of clarification question dictionaries
        """
        try:
            questions = []
            
            for key, value in extracted_info.items():
                if isinstance(value, dict) and value.get('confidence', 1.0) < confidence_threshold:
                    # Generate clarification question for low-confidence information
                    clarification_prompt = f"""
                    Generate a clarification question for this uncertain information:
                    Field: {key}
                    Value: {value.get('value', 'unknown')}
                    Confidence: {value.get('confidence', 0.0)}
                    
                    The question should:
                    - Ask for confirmation or clarification
                    - Be specific to the field and value
                    - Help improve the confidence of the information
                    
                    Return only the question text.
                    """
                    
                    ai_question = await ollama_client.generate(
                        clarification_prompt,
                        model=settings.DEFAULT_MODEL,
                        temperature=0.5
                    )
                    
                    ai_question = ai_question.strip().strip('"').strip("'")
                    
                    questions.append({
                        'id': f"clarify_{key}",
                        'aspect': key,
                        'question': ai_question,
                        'priority': 0.9,  # High priority for clarifications
                        'field': key,
                        'current_value': value.get('value'),
                        'confidence': value.get('confidence', 0.0),
                        'generated_at': datetime.utcnow().isoformat()
                    })
            
            self.logger.info(f"Generated {len(questions)} clarification questions")
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generating clarification questions: {e}", exc_info=True)
            return []
    
    def _calculate_question_priority(self, aspect: str, analysis: Dict[str, Any]) -> float:
        """Calculate priority score for a question aspect"""
        try:
            urgency_score = analysis.get('urgency_score', 0.5)
            complexity_score = analysis.get('complexity_score', 0.5)
            
            # Priority weights for different aspects
            aspect_weights = {
                'location': 1.0,      # Always high priority
                'urgency': 0.9,       # Very high priority
                'target': 0.8,        # High priority
                'environment': 0.6,   # Medium priority
                'resources': 0.5,     # Medium priority
                'constraints': 0.4    # Lower priority
            }
            
            base_priority = aspect_weights.get(aspect, 0.5)
            
            # Adjust based on urgency and complexity
            adjusted_priority = base_priority * (0.5 + urgency_score * 0.3 + complexity_score * 0.2)
            
            return max(0.1, min(1.0, adjusted_priority))
            
        except Exception as e:
            self.logger.error(f"Error calculating question priority: {e}")
            return 0.5
    
    def _format_conversation_history(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Format conversation history for AI analysis"""
        try:
            formatted = []
            for msg in conversation_history[-10:]:  # Last 10 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                formatted.append(f"{role}: {content}")
            
            return "\n".join(formatted)
            
        except Exception as e:
            self.logger.error(f"Error formatting conversation history: {e}")
            return ""
    
    def _generate_fallback_questions(self, user_input: str, missing_aspects: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback questions when AI fails"""
        try:
            questions = []
            
            for i, aspect in enumerate(missing_aspects[:3]):
                if aspect in self.question_templates:
                    template_questions = self.question_templates[aspect]
                    question = template_questions[0]  # Use first template
                    
                    questions.append({
                        'id': f"fallback_{i}",
                        'aspect': aspect,
                        'question': question,
                        'priority': 0.6,
                        'context': user_input,
                        'is_fallback': True,
                        'generated_at': datetime.utcnow().isoformat()
                    })
            
            return questions
            
        except Exception as e:
            self.logger.error(f"Error generating fallback questions: {e}")
            return []
    
    async def evaluate_question_effectiveness(self, question_id: str, 
                                            user_response: str, 
                                            extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate how effective a question was at gathering information.
        
        Args:
            question_id: ID of the question being evaluated
            user_response: User's response to the question
            extracted_info: Information extracted from the response
            
        Returns:
            Evaluation results dictionary
        """
        try:
            # Analyze response quality
            analysis_prompt = f"""
            Evaluate the quality and usefulness of this user response to a search and rescue mission question.
            
            User response: "{user_response}"
            Extracted information: {json.dumps(extracted_info, indent=2)}
            
            Rate the response on:
            1. Completeness (0-1): How complete is the information provided?
            2. Clarity (0-1): How clear and specific is the response?
            3. Usefulness (0-1): How useful is this information for mission planning?
            4. Actionability (0-1): Can we act on this information?
            
            Return JSON:
            {{
                "completeness": 0.0-1.0,
                "clarity": 0.0-1.0,
                "usefulness": 0.0-1.0,
                "actionability": 0.0-1.0,
                "overall_score": 0.0-1.0,
                "suggestions": ["list", "of", "improvement", "suggestions"]
            }}
            """
            
            analysis_response = await ollama_client.generate(
                analysis_prompt,
                model=settings.DEFAULT_MODEL,
                temperature=0.3
            )
            
            try:
                evaluation = json.loads(analysis_response)
            except json.JSONDecodeError:
                evaluation = {
                    "completeness": 0.5,
                    "clarity": 0.5,
                    "usefulness": 0.5,
                    "actionability": 0.5,
                    "overall_score": 0.5,
                    "suggestions": ["Response could be more specific"]
                }
            
            # Calculate overall score
            scores = [
                evaluation.get('completeness', 0.5),
                evaluation.get('clarity', 0.5),
                evaluation.get('usefulness', 0.5),
                evaluation.get('actionability', 0.5)
            ]
            evaluation['overall_score'] = sum(scores) / len(scores)
            
            # Store evaluation for learning
            self.context_memory[question_id] = {
                'evaluation': evaluation,
                'timestamp': datetime.utcnow().isoformat(),
                'user_response': user_response
            }
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating question effectiveness: {e}", exc_info=True)
            return {
                "completeness": 0.5,
                "clarity": 0.5,
                "usefulness": 0.5,
                "actionability": 0.5,
                "overall_score": 0.5,
                "suggestions": ["Unable to evaluate response"]
            }

# Global instance
question_generator = QuestionGenerator()

# Convenience functions
async def generate_initial_questions(user_input: str) -> List[Dict[str, Any]]:
    """Generate initial questions for a mission request"""
    return await question_generator.generate_initial_questions(user_input)

async def generate_follow_up_questions(conversation_history: List[Dict[str, Any]], 
                                     current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate follow-up questions based on conversation"""
    return await question_generator.generate_follow_up_questions(conversation_history, current_context)

async def generate_clarification_questions(extracted_info: Dict[str, Any], 
                                         confidence_threshold: float = 0.7) -> List[Dict[str, Any]]:
    """Generate clarification questions for low-confidence information"""
    return await question_generator.generate_clarification_questions(extracted_info, confidence_threshold)