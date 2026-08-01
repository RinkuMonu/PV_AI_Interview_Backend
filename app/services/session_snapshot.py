from typing import Dict, Any
from app.services.realtime_context_manager import RealtimeContextManager
from app.schemas.interview_session import SessionState

class SessionSnapshot:
    def __init__(self):
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        
    def create_snapshot(self, session_id: str, state: SessionState, context: RealtimeContextManager):
        snapshot = {
            "state": state.value,
            "speaker": context.current_speaker,
            "question": context.active_question,
            "transcript": context.partial_transcript
        }
        self.snapshots[session_id] = snapshot
        
    def get_snapshot(self, session_id: str) -> Dict[str, Any]:
        return self.snapshots.get(session_id, {})
