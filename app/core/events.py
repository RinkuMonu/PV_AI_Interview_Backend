import asyncio
import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger("app.core.events")

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, callback: Callable):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscribed to topic: {topic}")

    async def publish(self, topic: str, data: Any):
        if topic in self._subscribers:
            for callback in self._subscribers[topic]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        # Run subscribers in the background so publishers aren't blocked
                        asyncio.create_task(callback(data))
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in event subscriber for topic {topic}: {str(e)}")

# Global event bus instance
event_bus = EventBus()
