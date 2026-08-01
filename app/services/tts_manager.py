import abc
from typing import AsyncGenerator
from app.schemas.speech import AudioChunk

class TTSProvider(abc.ABC):
    @abc.abstractmethod
    async def synthesize_stream(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[AudioChunk, None]:
        pass

class ProviderNotConfiguredError(Exception):
    pass

class OpenAITTSAdapter(TTSProvider):
    async def synthesize_stream(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[AudioChunk, None]:
        # Functional stub for OpenAI TTS
        seq = 0
        async for text_chunk in text_stream:
            # Request audio from api.openai.com/v1/audio/speech
            # Mock return
            seq += 1
            yield AudioChunk(sequence_id=seq, audio_data=b"fake_audio_bytes", timestamp_ms=0.0)

class TTSManager:
    def __init__(self, provider: TTSProvider = None):
        self.provider = provider or OpenAITTSAdapter()
        
    async def synthesize(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[AudioChunk, None]:
        async for chunk in self.provider.synthesize_stream(text_stream):
            yield chunk
