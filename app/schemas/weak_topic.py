from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class WeakTopic(BaseModel):
    candidate_id: str
    subject: str
    topic: str
    confidence: float = 0.0
    mistake_count: int = 1
    last_seen: datetime = Field(default_factory=datetime.utcnow)
