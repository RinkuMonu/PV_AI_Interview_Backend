from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from app.services.interview_orchestrator import InterviewOrchestrator
from app.schemas.interview_session import InterviewSession

router = APIRouter()
orchestrator = InterviewOrchestrator()

@router.post("/start")
async def start_session(interview_id: str, candidate_id: str) -> InterviewSession:
    return await orchestrator.start_session(interview_id, candidate_id)

@router.post("/pause/{session_id}")
async def pause_session(session_id: str):
    await orchestrator.pause_session(session_id)
    return {"status": "paused"}

@router.post("/resume/{session_id}")
async def resume_session(session_id: str):
    await orchestrator.resume_session(session_id)
    return {"status": "resumed"}

@router.post("/end/{session_id}")
async def end_session(session_id: str):
    await orchestrator.end_session(session_id)
    return {"status": "ended"}

@router.get("/{session_id}", response_model=InterviewSession)
async def get_session(session_id: str):
    session = await orchestrator.session_manager.repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, token: str = None):
    # In production, validate token here
    await orchestrator.handle_websocket(session_id, websocket)
