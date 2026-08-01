from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime

class SessionState(str, Enum):
    CREATED = "created"
    WAITING = "waiting"
    GREETING = "greeting"
    QUESTIONING = "questioning"
    CANDIDATE_SPEAKING = "candidate_speaking"
    EVALUATION = "evaluation"
    FOLLOW_UP = "follow_up"
    THINKING = "thinking"
    AVATAR_SPEAKING = "avatar_speaking"
    COMPLETED = "completed"
    PAUSED = "paused"
    DISCONNECTED = "disconnected"
    RECOVERED = "recovered"
    CANCELLED = "cancelled"

class InterviewSession(BaseModel):
    session_id: str
    interview_id: str
    candidate_id: str
    state: SessionState = SessionState.CREATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
