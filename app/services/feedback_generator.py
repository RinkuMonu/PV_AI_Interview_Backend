from typing import Dict, Any
from app.schemas.feedback import Feedback

class FeedbackGenerator:
    def generate(self, raw_json: Dict[str, Any]) -> Feedback:
        return Feedback(
            strengths=raw_json.get("strengths", []),
            weaknesses=raw_json.get("weaknesses", []),
            improvement_suggestions=raw_json.get("improvement_suggestions", []),
            learning_resources=[],
            topic_recommendations=[],
            next_practice_questions=[]
        )
