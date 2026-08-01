from app.schemas.interview_session import SessionState

class StateTransitionError(Exception):
    pass

class StateManager:
    def __init__(self):
        self.transitions = {
            SessionState.CREATED: [SessionState.WAITING],
            SessionState.WAITING: [SessionState.GREETING, SessionState.DISCONNECTED],
            SessionState.GREETING: [SessionState.QUESTIONING, SessionState.PAUSED, SessionState.DISCONNECTED],
            SessionState.QUESTIONING: [SessionState.CANDIDATE_SPEAKING, SessionState.PAUSED, SessionState.DISCONNECTED],
            SessionState.CANDIDATE_SPEAKING: [SessionState.THINKING, SessionState.PAUSED, SessionState.DISCONNECTED],
            SessionState.THINKING: [SessionState.EVALUATION, SessionState.AVATAR_SPEAKING, SessionState.PAUSED, SessionState.DISCONNECTED],
            SessionState.EVALUATION: [SessionState.QUESTIONING, SessionState.PAUSED, SessionState.DISCONNECTED],
            SessionState.AVATAR_SPEAKING: [SessionState.QUESTIONING, SessionState.COMPLETED, SessionState.PAUSED, SessionState.DISCONNECTED],
            SessionState.PAUSED: [SessionState.GREETING, SessionState.QUESTIONING, SessionState.CANDIDATE_SPEAKING, SessionState.THINKING, SessionState.EVALUATION, SessionState.AVATAR_SPEAKING, SessionState.CANCELLED],
            SessionState.DISCONNECTED: [SessionState.RECOVERED, SessionState.CANCELLED],
            SessionState.RECOVERED: [SessionState.WAITING, SessionState.GREETING, SessionState.QUESTIONING, SessionState.CANDIDATE_SPEAKING, SessionState.THINKING, SessionState.EVALUATION, SessionState.AVATAR_SPEAKING],
            SessionState.COMPLETED: [],
            SessionState.CANCELLED: []
        }
        
    def transition(self, current_state: SessionState, target_state: SessionState) -> SessionState:
        if target_state not in self.transitions.get(current_state, []):
            raise StateTransitionError(f"Cannot transition from {current_state} to {target_state}")
        return target_state
