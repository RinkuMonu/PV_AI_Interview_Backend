from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.evaluation import EvaluationRecord

class InterviewResult(BaseModel):
    interview_id: str
    candidate_id: str
    evaluations: List[EvaluationRecord] = Field(default_factory=list)
    overall_score: float = 0.0
    passed: bool = False
    final_feedback: Optional[str] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)
