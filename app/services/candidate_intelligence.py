import logging
from typing import List, Dict

logger = logging.getLogger("candidate_intelligence")

class CandidateIntelligenceService:
    @staticmethod
    def build_candidate_summary(conversation: List[dict], profile: dict, metrics: dict) -> dict:
        """
        Dynamically constructs the Candidate Summary using existing database structures
        and heuristics. Does not require new LLM calls or database schema changes.
        """
        
        # 1. Basic Info is already in profile
        
        # 2. Behavior Profile (Heuristics)
        behavior_flags = set()
        candidate_turns = [t for t in conversation if t.get("role") == "candidate"]
        interviewer_turns = [t for t in conversation if t.get("role") in ["interviewer", "assistant"]]
        
        if candidate_turns:
            # Word Count Heuristics
            words = [len(t.get("content", "").split()) for t in candidate_turns]
            avg_words = sum(words) / len(words)
            
            if avg_words < 10:
                behavior_flags.add("Very Short Answers")
                behavior_flags.add("Nervousness")
            elif avg_words > 100:
                behavior_flags.add("Very Long Answers")
                behavior_flags.add("Overconfidence")
            else:
                behavior_flags.add("Confidence")
                
            # Repetitive Answers Check (Simple heuristic: same exact text repeated)
            answers = [t.get("content", "").strip().lower() for t in candidate_turns]
            if len(answers) != len(set(answers)):
                behavior_flags.add("Repetitive Answers")
                
        # 3. Learning Profile (Heuristics)
        topics_discussed = set()
        for t in interviewer_turns:
            if t.get("topic") and t.get("topic") != "General":
                topics_discussed.add(t.get("topic"))
                
        # Determine Mastered vs Needing Revision based on cumulative score threshold
        avg_score = 0
        if metrics:
            scores = list(metrics.values())
            avg_score = sum(scores) / max(len(scores), 1)
            
        topics_mastered = list(topics_discussed) if avg_score >= 8.0 else []
        topics_revision = list(topics_discussed) if avg_score < 6.0 else []
        
        # 4. Synthesize Summary
        strengths = profile.get("strengths", [])
        weaknesses = profile.get("weaknesses", [])
        
        communication_level = "High" if avg_score >= 8.0 else ("Medium" if avg_score >= 6.0 else "Low")
        subject_readiness = "Ready" if avg_score >= 7.5 else ("Needs Work" if avg_score >= 5.0 else "Unprepared")
        
        summary = {
            "overall_strengths": strengths[:3] if strengths else [],
            "overall_weaknesses": weaknesses[:3] if weaknesses else [],
            "behavior_flags": list(behavior_flags),
            "topics_discussed": list(topics_discussed),
            "topics_mastered": topics_mastered,
            "topics_needing_revision": topics_revision,
            "communication_level": communication_level,
            "subject_readiness": subject_readiness,
            "average_score": avg_score
        }
        
        print("====== CANDIDATE SUMMARY ======")
        import json
        print(json.dumps(summary, indent=2))
        print("===============================")
        
        return summary
