from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.schemas.scorecard import Scorecard
from app.schemas.feedback import Feedback

class Report(BaseModel):
    candidate_id: str
    interview_id: str
    executive_summary: str
    question_wise_evaluation: List[Dict[str, Any]] = Field(default_factory=list)
    competency_radar: Dict[str, float] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    final_verdict: str
