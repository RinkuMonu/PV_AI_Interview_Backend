from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AIRequestContext(BaseModel):
    interview_id: Optional[str] = None
    candidate_id: Optional[str] = None
    interview_type: Optional[str] = None
    subject: Optional[str] = None
    interview_stage: Optional[str] = None
    endpoint_name: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Distributed Tracing
    request_id: Optional[str] = None
    trace_id: Optional[str] = None

    # Store removed history for future Summary Manager
    removed_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Caching metadata
    cache_hit: bool = False
    cached_response: Optional[Any] = None
    cache_key: Optional[str] = None
    
    # Budget Manager Optimization Flags
    force_summary: bool = False
    aggressive_compression: bool = False
    grace_mode: bool = False
    is_essential: bool = True
