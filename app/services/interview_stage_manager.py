from typing import List, Dict, Any

class InterviewStageManager:
    # Deterministic ordered list of stages
    STAGES = [
        "Greeting",
        "Candidate Introduction",
        "Educational Background",
        "Projects / Experience",
        "Government Motivation",
        "Subject Fundamentals",
        "Subject Deep Dive",
        "Classroom / Practical Scenarios",
        "Current Affairs",
        "Behavioural Questions",
        "Closing"
    ]
    
    # Mandatory stages that cannot be skipped
    MANDATORY_STAGES = ["Greeting", "Candidate Introduction", "Closing"]
    
    # Configuration per stage
    STAGE_CONFIG = {
        "Greeting": {"min": 1, "max": 1},
        "Candidate Introduction": {"min": 1, "max": 2},
        "Educational Background": {"min": 1, "max": 2},
        "Projects / Experience": {"min": 1, "max": 3},
        "Government Motivation": {"min": 1, "max": 2},
        "Subject Fundamentals": {"min": 2, "max": 3},
        "Subject Deep Dive": {"min": 2, "max": 4},
        "Classroom / Practical Scenarios": {"min": 1, "max": 3},
        "Current Affairs": {"min": 1, "max": 2},
        "Behavioural Questions": {"min": 1, "max": 2},
        "Closing": {"min": 1, "max": 1},
    }

    @staticmethod
    def get_initial_stage() -> str:
        return InterviewStageManager.STAGES[0]

    @staticmethod
    def compute_stage_memory(conversation: List[dict], stage_name: str) -> dict:
        """
        Dynamically computes conversation memory for a specific stage
        without requiring database schema changes.
        """
        stage_turns = [t for t in conversation if t.get("stage") == stage_name]
        
        if not stage_turns:
            return None
            
        start_time = stage_turns[0].get("timestamp")
        end_time = stage_turns[-1].get("timestamp")
        questions_asked = sum(1 for t in stage_turns if t.get("role") == "interviewer")
        
        # Extract topics dynamically from the LLM or pre-defined metadata if available
        topics_covered = set([t.get("topic") for t in stage_turns if t.get("topic") and t.get("topic") != "General"])
        
        return {
            "stage_name": stage_name,
            "start_time": start_time,
            "end_time": end_time,
            "questions_asked": questions_asked,
            "topics_covered": list(topics_covered)
        }

    @staticmethod
    def determine_next_stage(current_stage: str, conversation: list, current_score: float = 7.0, candidate_summary: dict = None) -> str:
        """
        Determines if the interview should transition to the next stage based on
        entry/exit conditions, minimum questions, and the candidate's current performance score.
        """
        try:
            current_index = InterviewStageManager.STAGES.index(current_stage)
        except ValueError:
            current_index = 0
            
        config = InterviewStageManager.STAGE_CONFIG.get(current_stage, {"min": 1, "max": 2})
        questions_asked_in_stage = sum(1 for t in conversation if t.get("role") == "interviewer" and t.get("stage") == current_stage)
        
        # Adaptive Progression Logic
        # If score >= 7 (performing well), allow up to max_questions
        # If score < 7 (struggling), move on after min_questions to avoid pressure
        
        max_allowed = config["max"] if current_score >= 7.0 else config["min"]
        
        # If we haven't met the minimum, we must stay in the current stage
        if questions_asked_in_stage < config["min"]:
            return current_stage
            
        # If we have reached the adaptive maximum, transition to the next stage
        if questions_asked_in_stage >= max_allowed:
            if current_index + 1 < len(InterviewStageManager.STAGES):
                return InterviewStageManager.STAGES[current_index + 1]
                
        # Otherwise, stay in the current stage
        return current_stage
