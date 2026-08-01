from enum import Enum

class EvaluationMode(str, Enum):
    AUTO = "auto"
    LLM_ONLY = "llm_only"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"

class EvaluationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"

class InterviewProfileType(str, Enum):
    GOVERNMENT = "government"
    HR = "hr"
    TECHNICAL = "technical"
    CODING = "coding"
    BEHAVIORAL = "behavioral"
    AI_ML = "ai_ml"
    DOMAIN_SPECIFIC = "domain_specific"
