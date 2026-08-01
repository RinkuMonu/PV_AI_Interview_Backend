from pydantic import BaseModel, Field
from typing import Optional

class FollowupQuestion(BaseModel):
    followup_id: str
    parent_question_id: str
    candidate_id: str
    followup_type: str # e.g. conceptual, scenario, why-based
    question: str
    reasoning: Optional[str] = None
