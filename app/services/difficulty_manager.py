from app.schemas.interview_state import InterviewState
from app.models.question_models import DifficultyLevel

class DifficultyManager:
    def validate_difficulty(self, state: InterviewState, proposed_difficulty: DifficultyLevel) -> bool:
        # A simple validator. Could enforce rules like "cannot jump from EASY to HARD directly"
        if state.current_difficulty == DifficultyLevel.EASY and proposed_difficulty == DifficultyLevel.HARD:
            return False
        return True
