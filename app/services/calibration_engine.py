from typing import Dict, Any

class CalibrationEngine:
    def calibrate(self, validated_scores: Dict[str, float], raw_json: Dict[str, Any]) -> Dict[str, float]:
        """
        Applies deterministic rules to normalize values and reject impossible combinations.
        """
        calibrated = validated_scores.copy()
        
        # Impossible combination rule: High technical score but completely wrong answer
        # If accuracy is very low, technical score cannot be 100
        accuracy = float(raw_json.get("accuracy_score", 0.0))
        if accuracy < 20.0 and calibrated.get("technical_score", 0.0) > 80.0:
            calibrated["technical_score"] = min(calibrated["technical_score"], 40.0)
            
        # Normalize: If any score is mysteriously > 100 or < 0
        for k, v in calibrated.items():
            calibrated[k] = max(0.0, min(100.0, float(v)))
            
        return calibrated
