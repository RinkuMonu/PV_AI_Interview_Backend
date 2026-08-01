from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db
from app.schemas.interview_session import InterviewSession
from typing import Optional

class SessionRepository:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()

    async def save_session(self, session: InterviewSession):
        await self.db["interview_sessions"].update_one(
            {"session_id": session.session_id},
            {"$set": session.model_dump()},
            upsert=True
        )

    async def get_session(self, session_id: str) -> Optional[InterviewSession]:
        doc = await self.db["interview_sessions"].find_one({"session_id": session_id})
        return InterviewSession(**doc) if doc else None
