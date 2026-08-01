from typing import AsyncGenerator
from app.schemas.speech import AudioChunk
from app.schemas.avatar import AvatarFrame

class SyncManager:
    """Synchronizes TTS audio chunks with Avatar frames based on timestamp."""
    
    async def sync_streams(
        self, 
        audio_stream: AsyncGenerator[AudioChunk, None], 
        frame_stream: AsyncGenerator[AvatarFrame, None]
    ) -> AsyncGenerator[dict, None]:
        
        # In a real implementation, this would buffer and yield paired payloads
        # aligned exactly by timestamp_ms.
        # Here we mock simultaneous iteration using anzip-like semantics.
        
        audio_iter = audio_stream.__aiter__()
        frame_iter = frame_stream.__aiter__()
        
        while True:
            try:
                audio = await audio_iter.__anext__()
                frame = await frame_iter.__anext__()
                
                yield {
                    "audio": audio.model_dump(),
                    "frame": frame.model_dump()
                }
            except StopAsyncIteration:
                break
