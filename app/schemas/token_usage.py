from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TokenUsageCreate(BaseModel):
    interview_id: str
    candidate_id: Optional[str] = None
    subject: Optional[str] = None
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    request_time: datetime = Field(default_factory=datetime.utcnow)
    response_time: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: int
    endpoint_name: str

class TokenUsageDB(TokenUsageCreate):
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
