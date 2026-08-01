import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://localhost:8000/api/v1/interview-session/ws/test-123') as ws:
            print('Connected')
            await ws.send('{"type":"ping"}')
            res = await ws.recv()
            print('Received:', res)
    except Exception as e:
        print('Error:', e)

asyncio.run(test())
