from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class AICache(BaseModel):
    cache_key: str
    prompt_hash: str
    model: str
    provider: str
    system_prompt_hash: str
    prompt_version: str
    cache_version: int = 1
    response: Any
    embedding_hash: Optional[str] = None
    endpoint_name: str
    interview_type: Optional[str] = None
    subject: Optional[str] = None
    hit_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
