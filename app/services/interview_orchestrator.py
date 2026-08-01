import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional

from app.schemas.interview_session import SessionState, InterviewSession
from app.schemas.speech import AudioChunk
from app.services.session_manager import SessionManager
from app.services.state_manager import StateManager
from app.services.turn_manager import TurnManager
from app.services.interruption_manager import InterruptionManager
from app.services.websocket_manager import WebSocketManager
from app.services.realtime_event_manager import RealtimeEventManager
from app.services.conversation_manager import ConversationManager
from app.services.realtime_context_manager import RealtimeContextManager
from app.services.buffer_manager import BufferManager
from app.services.stt_manager import STTManager
from app.services.tts_manager import TTSManager
from app.services.vad_manager import VADManager
from app.services.avatar_manager import AvatarManager
from app.services.sync_manager import SyncManager
from app.services.emotion_engine import EmotionEngine
from app.services.latency_manager import LatencyManager
from app.services.session_timeline import SessionTimeline
from app.services.session_snapshot import SessionSnapshot

logger = logging.getLogger("app.services.interview_orchestrator")
fh = logging.FileHandler('ws_debug.log')
fh.setLevel(logging.INFO)
logger.addHandler(fh)

class InterviewOrchestrator:
    def __init__(self):
        self.session_manager = SessionManager()
        self.state_manager = StateManager()
        self.turn_manager = TurnManager(self.state_manager)
        self.interruption_manager = InterruptionManager()
        self.ws_manager = WebSocketManager()
        self.event_manager = RealtimeEventManager()
        
        # Per-session managers (in a real app, these would be instanced or keyed per session)
        # For simplicity in this architectural demo, we'll assume stateless/keyed usage or single session
        self.stt_manager = STTManager()
        self.tts_manager = TTSManager()
        self.vad_manager = VADManager()
        self.avatar_manager = AvatarManager()
        self.sync_manager = SyncManager()
        self.emotion_engine = EmotionEngine()
        self.latency_manager = LatencyManager()
        
        # In-memory session tracking
        self.contexts: dict[str, RealtimeContextManager] = {}
        self.conversations: dict[str, ConversationManager] = {}
        self.timelines: dict[str, SessionTimeline] = {}
        self.snapshots = SessionSnapshot()
        
    async def start_session(self, interview_id: str, candidate_id: str) -> InterviewSession:
        session = await self.session_manager.create_session(interview_id, candidate_id)
        self.contexts[session.session_id] = RealtimeContextManager()
        self.conversations[session.session_id] = ConversationManager()
        self.timelines[session.session_id] = SessionTimeline()
        
        await self.event_manager.publish(session.session_id, "session_created", {})
        return session
        
    async def pause_session(self, session_id: str):
        await self.session_manager.update_state(session_id, SessionState.PAUSED)
        await self.event_manager.publish(session_id, "session_paused", {})
        
    async def resume_session(self, session_id: str):
        await self.session_manager.update_state(session_id, SessionState.GREETING) # Simplified resume
        await self.event_manager.publish(session_id, "session_resumed", {})
        
    async def end_session(self, session_id: str):
        await self.session_manager.update_state(session_id, SessionState.COMPLETED)
        await self.event_manager.publish(session_id, "session_completed", {})
        self.ws_manager.disconnect(session_id)
        
    async def handle_websocket(self, session_id: str, websocket: WebSocket):
        logger.info(f"Incoming WS connection for {session_id}")
        await self.ws_manager.connect(session_id, websocket)
        logger.info(f"WS connected for {session_id}")
        
        # Try to update state - may fail if session is in a different collection (live_interview_sessions vs interview_sessions)
        state = SessionState.WAITING
        try:
            session = await self.session_manager.update_state(session_id, SessionState.WAITING)
            if session:
                state = session.state
        except Exception as e:
            logger.warning(f"Could not update session state for {session_id}: {e} — continuing anyway")
        
        # Snapshot state
        try:
            self.snapshots.create_snapshot(session_id, state, self.contexts.get(session_id, RealtimeContextManager()))
            logger.info(f"Snapshot created for {session_id}")
        except Exception as e:
            logger.warning(f"Could not create snapshot for {session_id}: {e}")
        
        try:
            import json
            import base64
            while True:
                logger.info(f"Waiting for json from {session_id}")
                data = await websocket.receive_json()
                logger.info(f"Received data: {data.get('type')}")
                
                if data.get("type") == "ping":
                    continue
                    
                if data.get("type") == "audio_chunk":
                    audio_b64 = data.get("payload", {}).get("audio", "")
                    if audio_b64:
                        try:
                            raw_audio = base64.b64decode(audio_b64)
                            chunk = AudioChunk(sequence_id=0, audio_data=raw_audio, timestamp_ms=0.0)
                            
                            # VAD & Interruption
                            is_speech = self.vad_manager.detect_speech(chunk)
                            context = self.contexts.get(session_id)
                            
                            if is_speech and context and context.current_speaker == "avatar":
                                self.interruption_manager.handle_interruption(context)
                                await self.event_manager.publish(session_id, "interruption_detected", {})
                                
                            await self.ws_manager.send_json(session_id, {"event": "audio_ack", "bytes": len(raw_audio)})
                        except Exception as e:
                            logger.error(f"Error decoding audio chunk: {e}")
                
                # Acknowledge receipt of any message for now
                await self.ws_manager.send_json(session_id, {"event": "ack", "type": data.get("type")})
                
        except WebSocketDisconnect:
            logger.info(f"Client disconnected: {session_id}")
            self.ws_manager.disconnect(session_id)
            await self.session_manager.update_state(session_id, SessionState.DISCONNECTED)
