from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CandidateKnowledgeGraph(BaseModel):
    candidate_id: str
    subject: str
    topic: str
    subtopic: Optional[str] = None
    mastery_score: float = 0.0
    confidence: float = 0.0
    attempt_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
