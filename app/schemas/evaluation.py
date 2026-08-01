from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.feedback import Feedback
from app.schemas.scorecard import Scorecard
from app.models.evaluation_models import EvaluationStatus, EvaluationMode

class EvaluationRecord(BaseModel):
    evaluation_id: str
    interview_id: str
    candidate_id: str
    question_id: str
    question: str
    candidate_answer: str
    expected_answer: Optional[str] = None
    
    scorecard: Scorecard
    feedback: Feedback
    
    evaluation_mode: EvaluationMode = EvaluationMode.HYBRID
    status: EvaluationStatus = EvaluationStatus.COMPLETED
    
    evaluation_version: str = "1.0"
    rubric_version: str = "1.0"
    prompt_version: str = "1.0"
    model_version: str = "1.0"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(protected_namespaces=())
