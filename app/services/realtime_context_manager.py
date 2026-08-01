from pydantic import BaseModel, Field
from typing import Dict, Any, List
from app.schemas.avatar import EmotionState

class RealtimeContextManager:
    def __init__(self):
        self.current_speaker: str = "avatar" # "avatar" or "candidate"
        self.partial_transcript: str = ""
        self.active_question: str = ""
        self.current_evaluation: Dict[str, Any] = {}
        self.live_token_count: int = 0
        self.interrupted: bool = False
        self.current_emotion: EmotionState = EmotionState.NEUTRAL
        
    def reset_turn(self):
        self.partial_transcript = ""
        self.interrupted = False

    def update_transcript(self, partial: str):
        self.partial_transcript += partial
        
    def switch_speaker(self, speaker: str):
        self.current_speaker = speaker
        self.reset_turn()
