from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LatencyMetrics(BaseModel):
    queue_time_ms: int = 0
    middleware_time_ms: int = 0
    llm_time_ms: int = 0
    db_time_ms: int = 0
    total_request_time_ms: int = 0

class ErrorDetails(BaseModel):
    error_type: str
    error_source: str
    provider: str
    retry_count: int = 0
    recoverable: bool = False
    stack_trace_hash: Optional[str] = None

class AnalyticsEvent(BaseModel):
    request_id: str
    trace_id: str
    interview_id: Optional[str] = None
    session_id: Optional[str] = None
    candidate_id: Optional[str] = None
    endpoint: str
    provider: str
    model: str
    
    latency_metrics: LatencyMetrics
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    request_cost: float = 0.0
    
    cache_hit: bool = False
    cache_key: Optional[str] = None
    
    summary_generated: bool = False
    compression_ratio: float = 0.0
    
    budget_level: str = "SAFE"
    optimization_actions: List[str] = Field(default_factory=list)
    
    error_details: Optional[ErrorDetails] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ActiveInterview(BaseModel):
    interview_id: str
    session_id: Optional[str] = None
    candidate_id: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    request_count: int = 0

class SystemHealth(BaseModel):
    provider: str
    model: str
    success_rate: float = 100.0
    error_rate: float = 0.0
    average_latency: float = 0.0
    uptime: float = 100.0
    status: str = "HEALTHY"
    last_check: datetime = Field(default_factory=datetime.utcnow)
