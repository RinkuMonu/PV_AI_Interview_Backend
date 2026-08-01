from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.question_models import InterviewStage, DifficultyLevel

class InterviewState(BaseModel):
    interview_id: str
    candidate_id: str
    current_stage: InterviewStage = InterviewStage.INTRODUCTION
    questions_asked: int = 0
    current_topic: Optional[str] = None
    current_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    weak_topics: List[str] = Field(default_factory=list)
    covered_topics: List[str] = Field(default_factory=list)
    remaining_topics: List[str] = Field(default_factory=list)
    followups_used: int = 0
    time_elapsed_seconds: int = 0
