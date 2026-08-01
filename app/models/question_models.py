from enum import Enum

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADAPTIVE = "adaptive"

class BloomLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"

class InterviewStage(str, Enum):
    INTRODUCTION = "introduction"
    TECHNICAL_SCREENING = "technical_screening"
    DEEP_DIVE = "deep_dive"
    SYSTEM_DESIGN = "system_design"
    BEHAVIORAL = "behavioral"
    WRAP_UP = "wrap_up"
