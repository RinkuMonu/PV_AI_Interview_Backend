from app.schemas.avatar import EmotionState
from app.services.realtime_context_manager import RealtimeContextManager

class EmotionEngine:
    def determine_emotion(self, text_chunk: str, context: RealtimeContextManager) -> EmotionState:
        """
        Analyzes the text being spoken (or listened to) to determine avatar emotion.
        """
        text_lower = text_chunk.lower()
        if "great" in text_lower or "excellent" in text_lower or "good" in text_lower:
            return EmotionState.HAPPY
        elif "?" in text_chunk or "how" in text_lower or "why" in text_lower:
            return EmotionState.THINKING
        
        if context.current_speaker == "candidate":
            return EmotionState.LISTENING
            
        return EmotionState.NEUTRAL
