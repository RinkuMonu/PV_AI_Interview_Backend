from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class CompetencyProfile(BaseModel):
    candidate_id: str
    subject: str
    
    current_scores: Dict[str, float] = Field(default_factory=dict)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    rolling_average: Dict[str, float] = Field(default_factory=dict)
    
    improvement_rate: float = 0.0
    performance_trend: str = "neutral"
    overall_score: float = 0.0
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
