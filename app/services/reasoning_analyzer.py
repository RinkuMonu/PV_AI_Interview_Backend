from typing import Dict, Any

class ReasoningAnalyzer:
    def validate_and_enrich(self, raw_json: Dict[str, Any]) -> float:
        raw_score = raw_json.get("reasoning_score", 0.0)
        return max(0.0, min(100.0, float(raw_score)))
