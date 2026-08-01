from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import datetime

class RealtimeEvent(BaseModel):
    event_id: str
    session_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    
class StreamPayload(BaseModel):
    chunk_index: int
    data: Any
    is_final: bool = False
