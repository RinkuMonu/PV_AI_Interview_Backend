import abc
from typing import AsyncGenerator
from app.schemas.speech import AudioChunk
from app.schemas.avatar import AvatarFrame, EmotionState

class AvatarProvider(abc.ABC):
    @abc.abstractmethod
    async def render_stream(
        self, 
        audio_stream: AsyncGenerator[AudioChunk, None], 
        emotion: EmotionState
    ) -> AsyncGenerator[AvatarFrame, None]:
        pass

class ProviderNotConfiguredError(Exception):
    pass

class LivePortraitAdapter(AvatarProvider):
    async def render_stream(
        self, 
        audio_stream: AsyncGenerator[AudioChunk, None], 
        emotion: EmotionState
    ) -> AsyncGenerator[AvatarFrame, None]:
        # Functional stub for LivePortrait
        # Converts audio into facial frames/blendshapes mapped with emotion
        seq = 0
        async for audio_chunk in audio_stream:
            seq += 1
            yield AvatarFrame(
                frame_id=seq,
                data=b"fake_video_frame_bytes",
                emotion=emotion,
                timestamp_ms=audio_chunk.timestamp_ms
            )

class AvatarManager:
    def __init__(self, provider: AvatarProvider = None):
        self.provider = provider or LivePortraitAdapter()
        
    async def render(
        self, 
        audio_stream: AsyncGenerator[AudioChunk, None], 
        emotion: EmotionState
    ) -> AsyncGenerator[AvatarFrame, None]:
        async for frame in self.provider.render_stream(audio_stream, emotion):
            yield frame
