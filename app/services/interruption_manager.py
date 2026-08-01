from app.services.realtime_context_manager import RealtimeContextManager
import logging

logger = logging.getLogger("app.services.interruption_manager")

class InterruptionManager:
    def handle_interruption(self, context: RealtimeContextManager):
        if context.current_speaker == "avatar":
            logger.info("Avatar interrupted by candidate!")
            context.interrupted = True
            context.switch_speaker("candidate")
