from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List

class RoutingRequest(BaseModel):
    task_type: str # e.g., "evaluation", "followup", "summary"
    messages: List[Dict[str, Any]]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    require_streaming: bool = False
    require_json: bool = False
    desired_latency_ms: Optional[int] = None
    budget_level: str = "SAFE"
    user_preference_provider: Optional[str] = None

class RoutingResponse(BaseModel):
    provider_name: str
    model_name: str
    content: Optional[str] = None
    usage: Dict[str, int] = Field(default_factory=dict)
    latency_ms: int = 0
    cached: bool = False
    error: Optional[str] = None
    
    model_config = ConfigDict(protected_namespaces=())
