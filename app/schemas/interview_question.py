from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.models.question_models import DifficultyLevel, BloomLevel

class InterviewQuestion(BaseModel):
    question_id: str
    subject: str
    topic: str
    subtopic: Optional[str] = None
    interview_type: Optional[str] = None
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    bloom_level: Optional[BloomLevel] = None
    question: str
    answer: str
    explanation: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    embeddings: Optional[List[float]] = None
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
