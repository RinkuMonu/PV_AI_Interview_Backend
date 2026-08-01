from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db

class HistoryRepository:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()

    async def record_question_asked(self, payload: Dict[str, Any]):
        await self.db["question_history"].insert_one(payload)

    async def get_history(self, interview_id: str) -> List[Dict[str, Any]]:
        cursor = self.db["question_history"].find({"interview_id": interview_id}).sort("asked_at", 1)
        return await cursor.to_list(length=100)
        
    async def has_been_asked(self, interview_id: str, question_id: str) -> bool:
        count = await self.db["question_history"].count_documents({
            "interview_id": interview_id,
            "question_id": question_id
        })
        return count > 0
