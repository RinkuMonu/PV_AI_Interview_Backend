from app.services.realtime_context_manager import RealtimeContextManager
from app.services.state_manager import StateManager
from app.schemas.interview_session import SessionState

class TurnManager:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        
    def end_candidate_turn(self, current_state: SessionState, context: RealtimeContextManager) -> SessionState:
        if current_state == SessionState.CANDIDATE_SPEAKING:
            context.switch_speaker("avatar")
            return self.state_manager.transition(current_state, SessionState.THINKING)
        return current_state
        
    def end_avatar_turn(self, current_state: SessionState, context: RealtimeContextManager, is_done: bool) -> SessionState:
        if current_state == SessionState.AVATAR_SPEAKING:
            context.switch_speaker("candidate")
            target = SessionState.COMPLETED if is_done else SessionState.QUESTIONING
            return self.state_manager.transition(current_state, target)
        return current_state
