import abc
from typing import AsyncGenerator
from app.schemas.speech import AudioChunk

class STTProvider(abc.ABC):
    @abc.abstractmethod
    async def transcribe_stream(self, audio_stream: AsyncGenerator[AudioChunk, None]) -> AsyncGenerator[str, None]:
        pass

class ProviderNotConfiguredError(Exception):
    pass

class OpenAIRealtimeSTTAdapter(STTProvider):
    async def transcribe_stream(self, audio_stream: AsyncGenerator[AudioChunk, None]) -> AsyncGenerator[str, None]:
        # Functional stub for OpenAI Realtime API WebSockets
        # Would establish ws to wss://api.openai.com/v1/realtime
        async for chunk in audio_stream:
            # yield partial transcripts based on chunks
            yield " (transcription chunk) "

class STTManager:
    def __init__(self, provider: STTProvider = None):
        self.provider = provider or OpenAIRealtimeSTTAdapter()
        
    async def process_stream(self, audio_stream: AsyncGenerator[AudioChunk, None]) -> AsyncGenerator[str, None]:
        async for text_chunk in self.provider.transcribe_stream(audio_stream):
            yield text_chunk
