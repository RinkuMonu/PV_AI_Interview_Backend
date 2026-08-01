from pydantic import BaseModel
from enum import Enum
from typing import Any

class EmotionState(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    THINKING = "thinking"
    LISTENING = "listening"
    SURPRISED = "surprised"

class AvatarFrame(BaseModel):
    frame_id: int
    data: bytes  # Encoded frame or blendshapes
    emotion: EmotionState
    timestamp_ms: float
