from pydantic import BaseModel, Field
from typing import List

class Feedback(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    learning_resources: List[str] = Field(default_factory=list)
    topic_recommendations: List[str] = Field(default_factory=list)
    next_practice_questions: List[str] = Field(default_factory=list)
