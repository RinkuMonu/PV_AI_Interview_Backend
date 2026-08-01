from typing import Dict, Any, Callable
import logging
from app.schemas.realtime_events import RealtimeEvent
import datetime
import uuid

logger = logging.getLogger("app.services.realtime_event_manager")

class RealtimeEventManager:
    def __init__(self):
        self.subscribers: Dict[str, list[Callable]] = {}
        
    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    async def publish(self, session_id: str, event_type: str, payload: Dict[str, Any]):
        event = RealtimeEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            event_type=event_type,
            payload=payload,
            timestamp=datetime.datetime.utcnow()
        )
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in realtime event subscriber: {e}")
