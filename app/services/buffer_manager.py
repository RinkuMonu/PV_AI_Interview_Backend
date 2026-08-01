import asyncio
from typing import Generic, TypeVar, List

T = TypeVar('T')

class BufferManager(Generic[T]):
    def __init__(self, max_size: int = 1000):
        self.queue: asyncio.Queue[T] = asyncio.Queue(maxsize=max_size)
        
    async def push(self, item: T):
        await self.queue.put(item)
        
    async def pop(self) -> T:
        return await self.queue.get()
        
    def empty(self) -> bool:
        return self.queue.empty()
        
    def clear(self):
        while not self.queue.empty():
            self.queue.get_nowait()
