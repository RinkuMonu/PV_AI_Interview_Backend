from pydantic import BaseModel

class Scorecard(BaseModel):
    technical_score: float = 0.0
    technical_reason: str = ""
    reasoning_score: float = 0.0
    reasoning_reason: str = ""
    communication_score: float = 0.0
    communication_reason: str = ""
    confidence_score: float = 0.0
    confidence_reason: str = ""
    accuracy_score: float = 0.0
    completeness_score: float = 0.0
    time_score: float = 0.0
    
    overall_score: float = 0.0
    passed: bool = False
    evaluation_confidence: float = 100.0
