import logging
import uuid
from typing import Optional, Any
from app.schemas.interview_state import InterviewState
from app.schemas.interview_question import InterviewQuestion
from app.schemas.question_ranking import QuestionRankingScore
from app.services.semantic_search import SemanticSearch
from app.services.duplicate_detector import DuplicateDetector
from app.services.difficulty_manager import DifficultyManager
from app.services.strategies.base_strategy import QuestionSelectionStrategy
from app.core.events import event_bus

logger = logging.getLogger("app.services.question_engine")

class QuestionEngine:
    def __init__(
        self,
        strategy: QuestionSelectionStrategy,
        semantic_search: SemanticSearch,
        duplicate_detector: DuplicateDetector,
        difficulty_manager: DifficultyManager,
        ai_middleware: Any = None
    ):
        self.strategy = strategy
        self.semantic_search = semantic_search
        self.duplicate_detector = duplicate_detector
        self.difficulty_manager = difficulty_manager
        self.ai_middleware = ai_middleware

    def _rank_candidates(self, candidates: list[InterviewQuestion]) -> list[InterviewQuestion]:
        # Simple mocked ranking. In production, computes QuestionRankingScore for each.
        return sorted(candidates, key=lambda q: QuestionRankingScore().final_score, reverse=True)

    async def get_next_question(self, state: InterviewState) -> Optional[InterviewQuestion]:
        if self.strategy.should_stop(state):
            logger.info(f"Interview {state.interview_id} should stop based on strategy.")
            return None

        # Determine Target Topic and Difficulty via Strategy
        target_topic, target_difficulty = self.strategy.determine_policy(state)
        if not target_topic:
            target_topic = "general"

        # Semantic Search for Recommendations
        candidates = await self.semantic_search.recommend_questions(topic=target_topic, limit=10)
        
        # Filter Duplicates
        valid_candidates = []
        for q in candidates:
            if not await self.duplicate_detector.is_duplicate(state.interview_id, q):
                # Difficulty Validation
                if self.difficulty_manager.validate_difficulty(state, q.difficulty):
                    valid_candidates.append(q)

        # Rank
        ranked = self._rank_candidates(valid_candidates)

        if ranked:
            selected = ranked[0]
            await event_bus.publish("question_retrieved", {"question_id": selected.question_id})
            return selected
            
        # Fallback to AI Generation
        logger.warning(f"No valid candidates found for {target_topic}. Falling back to AI Generation.")
        # Mocking generation
        generated = InterviewQuestion(
            question_id=str(uuid.uuid4()),
            subject="Fallback",
            topic=target_topic,
            question=f"Generated fallback question for {target_topic}",
            answer="Generated expected answer"
        )
        await event_bus.publish("question_generated", {"question_id": generated.question_id})
        return generated
