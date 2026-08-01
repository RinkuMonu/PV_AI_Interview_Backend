from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.knowledge_graph import CandidateKnowledgeGraph
from app.core.database import get_db

class KnowledgeGraphRepository:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()

    async def update_node(self, graph: CandidateKnowledgeGraph):
        graph.last_updated = datetime.utcnow()
        await self.db["candidate_knowledge_graph"].update_one(
            {
                "candidate_id": graph.candidate_id, 
                "subject": graph.subject, 
                "topic": graph.topic
            },
            {"$set": graph.model_dump()},
            upsert=True
        )

    async def get_graph(self, candidate_id: str) -> List[CandidateKnowledgeGraph]:
        cursor = self.db["candidate_knowledge_graph"].find({"candidate_id": candidate_id})
        docs = await cursor.to_list(length=100)
        return [CandidateKnowledgeGraph(**doc) for doc in docs]
