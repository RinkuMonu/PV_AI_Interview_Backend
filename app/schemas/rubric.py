from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from app.models.evaluation_models import InterviewProfileType

class Rubric(BaseModel):
    rubric_id: str
    interview_type: InterviewProfileType
    subject: str
    difficulty: str
    criteria: List[str] = Field(default_factory=list)
    weightage: Dict[str, float] = Field(default_factory=dict)
    passing_score: float = 60.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EvaluationProfile(BaseModel):
    profile_id: str
    type: InterviewProfileType
    prompt_template_id: str
    rubric_id: str
    competencies: List[str] = Field(default_factory=list)
    scoring_weights: Dict[str, float] = Field(default_factory=dict)
    pass_criteria: str
