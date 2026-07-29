from typing import List

DIFFICULTY_LEVELS = [
    "Easy",
    "Medium",
    "Advanced",
    "Scenario-Based",
    "Case Study"
]

class DifficultyService:
    @staticmethod
    def adjust_difficulty(current_difficulty: str, candidate_summary: dict) -> str:
        try:
            current_index = DIFFICULTY_LEVELS.index(current_difficulty)
        except ValueError:
            current_index = 1 # Default to Medium
            
        avg_score = candidate_summary.get("average_score", 7.0)
        
        if avg_score < 5.0:
            # Drop difficulty if they struggle, but not below Easy
            new_index = max(0, current_index - 1)
        elif avg_score >= 8.5:
            # Increase difficulty slowly as they succeed
            new_index = min(len(DIFFICULTY_LEVELS) - 1, current_index + 1)
        else:
            new_index = current_index
            
        return DIFFICULTY_LEVELS[new_index]
