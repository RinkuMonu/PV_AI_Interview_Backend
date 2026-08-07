"""
AI Tutor Doubt Solver — Fully functional endpoints with Groq AI.

Routes (mounted at /api/ai-tutor):
  POST   /chat            → Ask a question (creates/continues session)
  GET    /chat/history     → List all sessions (sidebar)
  GET    /chat/{id}        → Get all messages of one session
  DELETE /chat/{id}        → Delete a session

  POST   /create-study-plan
  GET    /my-study-plan
  PATCH  /complete-task/{plan_id}/{day}
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


# ── Pydantic models ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    subject: Optional[str] = None
    language: Optional[str] = "en"      # "hi" | "en"

class MessageOut(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatResponse(BaseModel):
    success: bool
    session_id: str
    messages: List[MessageOut]
    created_at: datetime

class SessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime

class HistoryResponse(BaseModel):
    sessions: List[SessionSummary]

class StudyPlanRequest(BaseModel):
    goal: Optional[str] = None
    current_level: Optional[str] = None
    daily_hours: Optional[int] = None
    target_date: Optional[str] = None
    language: Optional[str] = None
    strong_subjects: Optional[List[str]] = None
    weak_subjects: Optional[List[str]] = None
    subject: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_title(question: str) -> str:
    return question.strip()[:60] + ("…" if len(question) > 60 else "")


def _build_system_prompt(subject: Optional[str], language: str) -> str:
    lang_instr = (
        "Answer in Hindi (Devanagari script). Be clear and concise."
        if language == "hi"
        else "Answer in English. Be clear and concise."
    )
    subject_context = f" The student is studying for: {subject}." if subject else ""
    return (
        f"You are an expert AI tutor helping students prepare for Indian government exams "
        f"(SSC, KVS, NVS, RPSC, etc.).{subject_context} "
        f"Explain concepts step-by-step. {lang_instr}"
    )


async def _call_ai(messages_for_ai: list, subject: Optional[str], language: str) -> str:
    """Call Groq AI to get an answer."""
    import openai as _openai

    api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="No AI API key configured. Set GROQ_API_KEY in your .env file."
        )

    # Decide provider
    if settings.GROQ_API_KEY:
        base_url = "https://api.groq.com/openai/v1"
        model = "llama-3.1-8b-instant"
        key = settings.GROQ_API_KEY
    else:
        base_url = None
        model = "gpt-4o-mini"
        key = settings.OPENAI_API_KEY

    system = _build_system_prompt(subject, language)
    payload = [{"role": "system", "content": system}] + messages_for_ai

    try:
        client = _openai.AsyncOpenAI(api_key=key, base_url=base_url)
        resp = await client.chat.completions.create(
            model=model,
            messages=payload,
            temperature=0.7,
            max_tokens=1024,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI ERROR] {e}")
        raise HTTPException(status_code=503, detail=f"AI service error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# Doubt Solver Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/chat", tags=["AI Tutor Doubt Solver"], response_model=ChatResponse)
async def ask_doubt(body: ChatRequest):
    """Ask a question. Creates a new session or continues an existing one."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    sessions_col = db["doubt_sessions"]
    now = datetime.now(timezone.utc)

    # ── Load or create session ────────────────────────────────────────────
    if body.session_id:
        doc = await sessions_col.find_one({"session_id": body.session_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Session not found")
        session_id   = body.session_id
        messages_raw = doc.get("messages", [])
        created_at   = doc.get("created_at", now)
    else:
        session_id   = str(uuid.uuid4())
        messages_raw = []
        created_at   = now
        await sessions_col.insert_one({
            "session_id":  session_id,
            "title":       _make_title(body.question),
            "subject":     body.subject,
            "language":    body.language,
            "messages":    [],
            "created_at":  created_at,
            "updated_at":  created_at,
        })

    # ── Append user message ───────────────────────────────────────────────
    user_msg = {
        "role":      "user",
        "content":   body.question,
        "timestamp": now,
    }
    messages_raw.append(user_msg)

    # Only send last 10 messages for context
    ai_context = [{"role": m["role"], "content": m["content"]}
                  for m in messages_raw[-10:]]

    # ── Call AI ────────────────────────────────────────────────────────────
    answer = await _call_ai(ai_context, body.subject, body.language or "en")

    ai_msg = {
        "role":      "assistant",
        "content":   answer,
        "timestamp": datetime.now(timezone.utc),
    }
    messages_raw.append(ai_msg)

    # ── Save to MongoDB ───────────────────────────────────────────────────
    await sessions_col.update_one(
        {"session_id": session_id},
        {"$set": {
            "messages":   messages_raw,
            "updated_at": datetime.now(timezone.utc),
        }},
    )

    return ChatResponse(
        success=True,
        session_id=session_id,
        messages=[MessageOut(**m) for m in messages_raw],
        created_at=created_at,
    )


@router.get("/chat/history", tags=["AI Tutor Doubt Solver"], response_model=HistoryResponse)
async def get_history():
    """Return all sessions sorted by most recent first."""
    db = get_db()
    if db is None:
        return HistoryResponse(sessions=[])

    cursor = db["doubt_sessions"].find(
        {},
        {"session_id": 1, "title": 1, "created_at": 1, "updated_at": 1, "_id": 0},
    ).sort("updated_at", -1).limit(50)

    sessions = []
    async for doc in cursor:
        sessions.append(SessionSummary(
            session_id=doc["session_id"],
            title=doc.get("title", "Untitled"),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
        ))

    return HistoryResponse(sessions=sessions)


@router.get("/chat/{session_id}", tags=["AI Tutor Doubt Solver"], response_model=ChatResponse)
async def get_session(session_id: str):
    """Return full message thread for one session."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    doc = await db["doubt_sessions"].find_one({"session_id": session_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")

    return ChatResponse(
        success=True,
        session_id=session_id,
        messages=[MessageOut(**m) for m in doc.get("messages", [])],
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
    )


@router.delete("/chat/{session_id}", tags=["AI Tutor Doubt Solver"])
async def delete_session(session_id: str):
    """Delete an entire session and all its messages."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    result = await db["doubt_sessions"].delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "message": "Session deleted"}


# ══════════════════════════════════════════════════════════════════════════════
# Study Planner Endpoints (stubs kept as-is)
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/create-study-plan", tags=["AI Tutor"])
async def create_study_plan(request: StudyPlanRequest):
    """Create Plan"""
    return {"status": "success", "message": "Study plan created"}

@router.get("/my-study-plan", tags=["AI Tutor"])
async def get_my_study_plan():
    """My Plan"""
    return {"status": "success", "data": {}}

@router.patch("/complete-task/{plan_id}/{day}", tags=["AI Tutor"])
async def complete_task(plan_id: str, day: str):
    """Mark Complete"""
    return {"status": "success", "message": f"Task for plan {plan_id} on day {day} marked complete"}
