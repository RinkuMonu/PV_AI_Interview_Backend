from typing import List, Dict, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger("app.services.session_timeline")

class SessionTimeline:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        
    def record(self, event_type: str, payload: Dict[str, Any]):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "payload": payload
        }
        self.events.append(event)
        
    def export(self) -> str:
        return json.dumps(self.events)
