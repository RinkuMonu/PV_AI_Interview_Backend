from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db
from app.schemas.evaluation import EvaluationRecord
from app.schemas.rubric import Rubric, EvaluationProfile
from app.models.evaluation_models import InterviewProfileType

class EvaluationRepository:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()

    async def save_evaluation(self, record: EvaluationRecord):
        await self.db["evaluations"].insert_one(record.model_dump())

    async def get_evaluation(self, evaluation_id: str) -> Optional[EvaluationRecord]:
        doc = await self.db["evaluations"].find_one({"evaluation_id": evaluation_id})
        return EvaluationRecord(**doc) if doc else None

    async def get_interview_evaluations(self, interview_id: str) -> List[EvaluationRecord]:
        cursor = self.db["evaluations"].find({"interview_id": interview_id})
        docs = await cursor.to_list(length=100)
        return [EvaluationRecord(**doc) for doc in docs]

    async def get_rubric(self, rubric_id: str) -> Optional[Rubric]:
        doc = await self.db["rubrics"].find_one({"rubric_id": rubric_id})
        return Rubric(**doc) if doc else None

    async def save_rubric(self, rubric: Rubric):
        await self.db["rubrics"].update_one(
            {"rubric_id": rubric.rubric_id},
            {"$set": rubric.model_dump()},
            upsert=True
        )

    async def get_profile(self, profile_type: InterviewProfileType) -> Optional[EvaluationProfile]:
        doc = await self.db["evaluation_profiles"].find_one({"type": profile_type.value})
        return EvaluationProfile(**doc) if doc else None
