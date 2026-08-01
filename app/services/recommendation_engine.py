from typing import Dict, Any
from app.schemas.feedback import Feedback

class RecommendationEngine:
    def recommend(self, raw_json: Dict[str, Any], feedback: Feedback) -> Feedback:
        feedback.learning_resources = raw_json.get("recommendations", [])
        return feedback
