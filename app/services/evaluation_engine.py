import json
import uuid
from typing import Dict, Any, Optional
import logging
from app.schemas.evaluation import EvaluationRecord
from app.schemas.rubric import EvaluationProfile
from app.models.evaluation_models import InterviewProfileType, EvaluationStatus, EvaluationMode
from app.services.rubric_manager import RubricManager
from app.services.answer_analyzer import AnswerAnalyzer
from app.services.reasoning_analyzer import ReasoningAnalyzer
from app.services.communication_analyzer import CommunicationAnalyzer
from app.services.confidence_analyzer import ConfidenceAnalyzer
from app.services.calibration_engine import CalibrationEngine
from app.services.scoring_engine import ScoringEngine
from app.services.feedback_generator import FeedbackGenerator
from app.services.recommendation_engine import RecommendationEngine
from app.services.evaluation_repository import EvaluationRepository
from app.services.competency_manager import CompetencyManager
from app.core.events import event_bus
from app.services.ai_middleware import AIMiddleware, AIRequestContext

logger = logging.getLogger("app.services.evaluation_engine")

class EvaluationEngine:
    def __init__(self):
        self.rubric_manager = RubricManager()
        self.answer_analyzer = AnswerAnalyzer()
        self.reasoning_analyzer = ReasoningAnalyzer()
        self.communication_analyzer = CommunicationAnalyzer()
        self.confidence_analyzer = ConfidenceAnalyzer()
        self.calibration_engine = CalibrationEngine()
        self.scoring_engine = ScoringEngine()
        self.feedback_generator = FeedbackGenerator()
        self.recommendation_engine = RecommendationEngine()
        self.repository = EvaluationRepository()
        self.competency_manager = CompetencyManager()
        
    async def evaluate_answer(
        self,
        interview_id: str,
        candidate_id: str,
        question_id: str,
        question: str,
        candidate_answer: str,
        profile_type: InterviewProfileType,
        expected_answer: Optional[str] = None,
        mode: EvaluationMode = EvaluationMode.HYBRID
    ) -> EvaluationRecord:
        
        await event_bus.publish("evaluation_started", {"interview_id": interview_id, "question_id": question_id})
        
        # 1. Fetch Profile and Rubric
        profile = await self.rubric_manager.get_profile(profile_type)
        
        # 2. Call AIMiddleware for structured JSON
        middleware = AIMiddleware()
        context = AIRequestContext(interview_id=interview_id, candidate_id=candidate_id)
        
        prompt_template = "Mock template fetched by ID: " + profile.prompt_template_id
        
        prompt = (
            f"{prompt_template}\n\n"
            f"Question: {question}\n"
            f"Expected: {expected_answer}\n"
            f"Answer: {candidate_answer}\n\n"
            "Return JSON matching the schema."
        )
        
        raw_json: Dict[str, Any] = {}
        try:
            # We mock the response in sandbox, normally we extract JSON from route_resp
            # response = await middleware.generate_response(context, messages=[{"role":"user","content":prompt}], response_format={"type":"json_object"})
            # raw_json = json.loads(response.choices[0].message.content)
            raw_json = {
                "technical_score": 85.0,
                "technical_reason": "Answered correctly.",
                "reasoning_score": 80.0,
                "reasoning_reason": "Logical flow is mostly correct.",
                "communication_score": 90.0,
                "communication_reason": "Clear and concise.",
                "confidence_score": 88.0,
                "confidence_reason": "No hesitation.",
                "accuracy_score": 85.0,
                "completeness_score": 80.0,
                "strengths": ["Clear communication", "Good logic"],
                "weaknesses": ["Missed edge case"],
                "recommendations": ["Review concurrency"],
                "evaluation_confidence": 95.0
            }
        except Exception as e:
            logger.error(f"Evaluation AI failure: {e}")
            await event_bus.publish("evaluation_failed", {"interview_id": interview_id})
            raise
            
        # 3. Validate and Enrich
        validated_scores = {
            "technical_score": self.answer_analyzer.validate_and_enrich(raw_json),
            "reasoning_score": self.reasoning_analyzer.validate_and_enrich(raw_json),
            "communication_score": self.communication_analyzer.validate_and_enrich(raw_json),
            "confidence_score": self.confidence_analyzer.validate_and_enrich(raw_json, text_transcript=candidate_answer)
        }
        
        # 4. Calibrate Scores (Deterministic layer)
        calibrated_scores = self.calibration_engine.calibrate(validated_scores, raw_json)
        
        # 5. Calculate Final Scores
        scorecard = self.scoring_engine.calculate(calibrated_scores, profile, raw_json)
        
        # 6. Check Confidence Threshold
        status = EvaluationStatus.COMPLETED
        if scorecard.evaluation_confidence < 80.0:
            logger.warning(f"Low evaluation confidence: {scorecard.evaluation_confidence}. Flagging for review.")
            status = EvaluationStatus.NEEDS_REVIEW
            
        # 6. Generate Feedback and Recommendations
        feedback = self.feedback_generator.generate(raw_json)
        feedback = self.recommendation_engine.recommend(raw_json, feedback)
        
        # 7. Construct Record
        record = EvaluationRecord(
            evaluation_id=str(uuid.uuid4()),
            interview_id=interview_id,
            candidate_id=candidate_id,
            question_id=question_id,
            question=question,
            candidate_answer=candidate_answer,
            expected_answer=expected_answer,
            scorecard=scorecard,
            feedback=feedback,
            evaluation_mode=mode,
            status=status
        )
        
        # 9. Save and Update Competency
        await self.repository.save_evaluation(record)
        await self.competency_manager.update_competency(candidate_id, "General", scorecard)
        
        await event_bus.publish("evaluation_completed", {"evaluation_id": record.evaluation_id})
        return record
