from typing import Optional
from app.schemas.competency import CompetencyProfile
from app.schemas.scorecard import Scorecard
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db
import logging

logger = logging.getLogger("app.services.competency_manager")

class CompetencyManager:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()

    async def get_profile(self, candidate_id: str, subject: str) -> Optional[CompetencyProfile]:
        doc = await self.db["competency_profiles"].find_one({"candidate_id": candidate_id, "subject": subject})
        return CompetencyProfile(**doc) if doc else None

    async def update_competency(self, candidate_id: str, subject: str, scorecard: Scorecard):
        profile = await self.get_profile(candidate_id, subject)
        if not profile:
            profile = CompetencyProfile(candidate_id=candidate_id, subject=subject)
            
        # Update current scores
        profile.current_scores = {
            "technical": scorecard.technical_score,
            "reasoning": scorecard.reasoning_score,
            "communication": scorecard.communication_score,
            "confidence": scorecard.confidence_score
        }
        
        import datetime
        # Append timeline
        profile.timeline.append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "scores": profile.current_scores,
            "overall": scorecard.overall_score
        })
        if len(profile.timeline) > 10:
            profile.timeline.pop(0)
            
        # Calculate Rolling Average
        for key in profile.current_scores.keys():
            total = sum(h["scores"].get(key, 0.0) for h in profile.timeline)
            profile.rolling_average[key] = total / len(profile.timeline)
            
        # Calculate Improvement Rate (simple delta between first and last)
        if len(profile.timeline) >= 2:
            first_score = profile.timeline[0]["overall"]
            last_score = profile.timeline[-1]["overall"]
            profile.improvement_rate = last_score - first_score
            profile.performance_trend = "improving" if profile.improvement_rate > 0 else "declining"
        else:
            profile.improvement_rate = 0.0
            profile.performance_trend = "neutral"
            
        # Overall
        profile.overall_score = scorecard.overall_score
        
        # Save to Mongo
        await self.db["competency_profiles"].update_one(
            {"candidate_id": candidate_id, "subject": subject},
            {"$set": profile.model_dump()},
            upsert=True
        )
        logger.info(f"Competency profile updated for {candidate_id}")
