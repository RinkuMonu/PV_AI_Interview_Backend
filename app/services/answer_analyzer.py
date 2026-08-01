from typing import Dict, Any

class AnswerAnalyzer:
    def validate_and_enrich(self, raw_json: Dict[str, Any]) -> float:
        # Validates and normalizes technical accuracy from AI JSON
        raw_score = raw_json.get("technical_score", 0.0)
        return max(0.0, min(100.0, float(raw_score)))
