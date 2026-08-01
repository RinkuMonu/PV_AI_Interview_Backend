from abc import ABC, abstractmethod
from typing import Tuple, Optional
from app.schemas.interview_state import InterviewState
from app.models.question_models import DifficultyLevel

class QuestionSelectionStrategy(ABC):
    @abstractmethod
    def determine_policy(self, state: InterviewState) -> Tuple[Optional[str], DifficultyLevel]:
        """
        Returns (target_topic, target_difficulty).
        """
        pass

    @abstractmethod
    def should_stop(self, state: InterviewState) -> bool:
        """
        Determines if the interview should conclude based on this strategy.
        """
        pass
