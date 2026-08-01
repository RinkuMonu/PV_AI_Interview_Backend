from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class ConversationTurn(BaseModel):
    turn_id: str
    session_id: str
    speaker: str  # "avatar" or "candidate"
    content: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    interrupted: bool = False
