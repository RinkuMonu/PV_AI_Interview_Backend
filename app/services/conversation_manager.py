from typing import List
from app.schemas.conversation_turn import ConversationTurn
from app.schemas.interview_session import SessionState

class ConversationManager:
    def __init__(self):
        self.history: List[ConversationTurn] = []
        self.current_topic: str = "General"
        self.current_difficulty: str = "Medium"
        self.summary_context: str = ""
        
    def add_turn(self, turn: ConversationTurn):
        self.history.append(turn)
        
    def get_recent_turns(self, limit: int = 5) -> List[ConversationTurn]:
        return self.history[-limit:]
