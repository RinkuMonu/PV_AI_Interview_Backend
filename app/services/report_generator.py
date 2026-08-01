from app.schemas.report import Report
from app.schemas.scorecard import Scorecard
from app.schemas.feedback import Feedback
from app.schemas.evaluation import EvaluationRecord
from typing import List

class ReportGenerator:
    def generate(self, candidate_id: str, interview_id: str, evaluations: List[EvaluationRecord], overall_score: float, passed: bool) -> Report:
        # Generate Question-wise evaluation summary
        question_wise = []
        strengths = set()
        weaknesses = set()
        recommendations = set()
        
        radar = {
            "technical": 0.0,
            "reasoning": 0.0,
            "communication": 0.0,
            "confidence": 0.0
        }
        
        for eval in evaluations:
            question_wise.append({
                "question": eval.question,
                "score": eval.scorecard.overall_score,
                "technical_reason": eval.scorecard.technical_reason,
                "communication_reason": eval.scorecard.communication_reason
            })
            strengths.update(eval.feedback.strengths)
            weaknesses.update(eval.feedback.weaknesses)
            recommendations.update(eval.feedback.topic_recommendations)
            
            radar["technical"] += eval.scorecard.technical_score
            radar["reasoning"] += eval.scorecard.reasoning_score
            radar["communication"] += eval.scorecard.communication_score
            radar["confidence"] += eval.scorecard.confidence_score
            
        if evaluations:
            for k in radar:
                radar[k] /= len(evaluations)
                
        verdict = "PASSED" if passed else "FAILED"
        executive_summary = f"Candidate {candidate_id} achieved {overall_score:.1f}% ({verdict})."
        
        return Report(
            candidate_id=candidate_id,
            interview_id=interview_id,
            executive_summary=executive_summary,
            question_wise_evaluation=question_wise,
            competency_radar=radar,
            strengths=list(strengths),
            weaknesses=list(weaknesses),
            recommendations=list(recommendations),
            final_verdict=verdict
        )
