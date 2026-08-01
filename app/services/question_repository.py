from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.interview_question import InterviewQuestion
from app.core.database import get_db

class QuestionRepository:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()

    async def get_by_id(self, question_id: str) -> Optional[InterviewQuestion]:
        doc = await self.db["questions"].find_one({"question_id": question_id})
        return InterviewQuestion(**doc) if doc else None

    async def search_by_topic(self, topic: str, difficulty: Optional[str] = None, limit: int = 20) -> List[InterviewQuestion]:
        query = {"topic": topic}
        if difficulty:
            query["difficulty"] = difficulty
            
        cursor = self.db["questions"].find(query).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [InterviewQuestion(**doc) for doc in docs]

    async def vector_search(self, query_embedding: List[float], limit: int = 10) -> List[InterviewQuestion]:
        # Implementation for MongoDB Atlas Vector Search or similar
        # Fallback to standard query for mock
        pipeline = [
            {
                "$search": {
                    "index": "default",
                    "knnBeta": {
                        "vector": query_embedding,
                        "path": "embeddings",
                        "k": limit
                    }
                }
            }
        ]
        try:
            docs = await self.db["questions"].aggregate(pipeline).to_list(length=limit)
            return [InterviewQuestion(**doc) for doc in docs]
        except Exception:
            # Fallback if no search index exists locally
            return await self.search_by_topic("fallback", limit=limit)
