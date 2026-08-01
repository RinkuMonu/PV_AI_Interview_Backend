from typing import AsyncGenerator, Any

class StreamingManager:
    async def broadcast_stream(self, stream: AsyncGenerator[Any, None], ws_callback):
        async for item in stream:
            await ws_callback(item)
