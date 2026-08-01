from typing import Dict, Any

class ConfidenceAnalyzer:
    def validate_and_enrich(self, raw_json: Dict[str, Any], text_transcript: str = "") -> float:
        raw_score = raw_json.get("confidence_score", 0.0)
        score = max(0.0, min(100.0, float(raw_score)))
        
        # Enrichment: penalize score if there are excessive filler words indicating low confidence
        fillers = ["um", "uh", "like", "you know"]
        filler_count = sum(text_transcript.lower().count(f) for f in fillers)
        if filler_count > 5:
            score = max(0.0, score - 10.0)
            
        return score
