class DecisionEngineService:
    @staticmethod
    def decide_next_action(evaluation: dict, candidate_summary: dict = None) -> dict:
        """
        Determines the next interview action based on the candidate's answer score.
        
        Rules:
        - Score >= 9: deeper_followup
        - Score 7-8: clarification_followup
        - Score <= 6: next_question
        """
        metrics = evaluation.get("metrics", {})
        
        if not metrics:
            score = 7.0 # Default to middle if missing
        else:
            score = sum(metrics.values()) / len(metrics.values())
            
        keywords = evaluation.get("keywords", [])
        topic = ", ".join(keywords) if keywords else "the topic"
        
        if score >= 9:
            return {
                "action": "deeper_followup",
                "reason": "high_score",
                "topic": topic,
                "keywords": keywords,
                "difficulty": "hard"
            }
        elif score >= 7:
            return {
                "action": "clarification_followup",
                "reason": "medium_score",
                "topic": topic,
                "keywords": keywords,
                "difficulty": "medium"
            }
        else:
            return {
                "action": "next_question",
                "reason": "low_score",
                "topic": topic,
                "keywords": keywords,
                "difficulty": "easy"
            }
