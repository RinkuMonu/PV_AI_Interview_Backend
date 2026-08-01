from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ProviderStatus(BaseModel):
    name: str
    is_active: bool = True
    health_score: float = 100.0
    average_latency_ms: float = 0.0
    success_rate: float = 1.0
    failure_rate: float = 0.0
    last_heartbeat: Optional[str] = None
    rate_limits: Dict[str, Any] = {}

class ProviderConfig(BaseModel):
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_ms: int = 30000
    priority: int = 1
