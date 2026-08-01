from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BudgetPolicy(BaseModel):
    max_prompt_tokens: int
    max_completion_tokens: int
    max_total_tokens: int
    max_cost: float
    warning_threshold: int = 80
    critical_threshold: int = 90
    grace_threshold: int = 100
    stop_threshold: int = 110

class CurrentUsage(BaseModel):
    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0

class BudgetStatusInfo(BaseModel):
    utilization_percentage: float = 0.0
    budget_level: str = "SAFE"

class OptimizationStats(BaseModel):
    summary_triggered: bool = False
    cache_hits: int = 0
    optimization_actions: List[str] = Field(default_factory=list)

class InterviewBudget(BaseModel):
    interview_id: str
    session_id: Optional[str] = None
    candidate_id: Optional[str] = None
    interview_type: Optional[str] = None
    subject: Optional[str] = None
    model: str
    
    budget: BudgetPolicy
    usage: CurrentUsage = Field(default_factory=CurrentUsage)
    status: BudgetStatusInfo = Field(default_factory=BudgetStatusInfo)
    optimization: OptimizationStats = Field(default_factory=OptimizationStats)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BudgetEvent(BaseModel):
    interview_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    budget_level: str
    action: str
    reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float
