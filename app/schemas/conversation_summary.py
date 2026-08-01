from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ConversationSummary(BaseModel):
    interview_id: str
    session_id: Optional[str] = None
    candidate_id: Optional[str] = None
    subject: Optional[str] = None
    interview_stage: Optional[str] = None
    
    summary_text: str
    candidate_strengths: Optional[str] = None
    candidate_weaknesses: Optional[str] = None
    covered_topics: Optional[str] = None
    pending_topics: Optional[str] = None
    evaluation_notes: Optional[str] = None
    confidence_score: Optional[int] = None
    
    summarized_turns: int = 0
    summary_version: int = 1
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
