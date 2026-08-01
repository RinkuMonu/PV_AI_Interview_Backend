from typing import Dict, Any
from app.schemas.scorecard import Scorecard
from app.schemas.rubric import EvaluationProfile

class ScoringEngine:
    def calculate(self, calibrated_scores: Dict[str, float], profile: EvaluationProfile, raw_json: Dict[str, Any]) -> Scorecard:
        sc = Scorecard()
        sc.technical_score = calibrated_scores.get("technical_score", 0.0)
        sc.technical_reason = raw_json.get("technical_reason", "")
        
        sc.reasoning_score = calibrated_scores.get("reasoning_score", 0.0)
        sc.reasoning_reason = raw_json.get("reasoning_reason", "")
        
        sc.communication_score = calibrated_scores.get("communication_score", 0.0)
        sc.communication_reason = raw_json.get("communication_reason", "")
        
        sc.confidence_score = calibrated_scores.get("confidence_score", 0.0)
        sc.confidence_reason = raw_json.get("confidence_reason", "")
        
        # Parse missing fields from raw json
        sc.accuracy_score = calibrated_scores.get("accuracy_score", 0.0)
        sc.completeness_score = calibrated_scores.get("completeness_score", 0.0)
        
        # Calculate Weighted Overall Score
        overall = 0.0
        weights = profile.scoring_weights
        
        overall += sc.technical_score * weights.get("technical", 0.0)
        overall += sc.reasoning_score * weights.get("reasoning", 0.0)
        overall += sc.communication_score * weights.get("communication", 0.0)
        overall += sc.confidence_score * weights.get("confidence", 0.0)
        
        # If weights don't add to 1, normalize (simplified)
        sc.overall_score = overall
        
        # Parse Pass Criteria
        try:
            # Dangerous in prod without sandboxing, but mock implementation of pass criteria
            # criteria usually looks like "overall_score >= 60"
            pass_val = float(profile.pass_criteria.split(">=")[1].strip())
            sc.passed = overall >= pass_val
        except Exception:
            sc.passed = overall >= 60.0
            
        sc.evaluation_confidence = float(raw_json.get("evaluation_confidence", 100.0))
        
        return sc
