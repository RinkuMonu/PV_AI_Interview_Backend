from typing import Tuple, Optional
from app.services.strategies.base_strategy import QuestionSelectionStrategy
from app.schemas.interview_state import InterviewState
from app.models.question_models import DifficultyLevel, InterviewStage

class AdaptiveStrategy(QuestionSelectionStrategy):
    def determine_policy(self, state: InterviewState) -> Tuple[Optional[str], DifficultyLevel]:
        # Simple adaptive logic based on current difficulty
        next_diff = state.current_difficulty
        
        # In a real app, this would read from the knowledge graph or weak topics
        # Here we mock a generic adaptive shift
        if state.questions_asked > 3 and next_diff == DifficultyLevel.MEDIUM:
            next_diff = DifficultyLevel.HARD
            
        topic = state.current_topic
        if state.remaining_topics and (state.questions_asked % 3 == 0):
            topic = state.remaining_topics.pop(0)
            
        return topic, next_diff

    def should_stop(self, state: InterviewState) -> bool:
        return state.questions_asked >= 10 or state.current_stage == InterviewStage.WRAP_UP
