import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.analytics import AnalyticsEvent, SystemHealth
from app.core.database import get_db

logger = logging.getLogger("app.services.analytics_repository")

class AnalyticsRepository:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()

    async def save_event(self, event: AnalyticsEvent):
        # 1. Insert immutable event
        await self.db["analytics_events"].insert_one(event.model_dump())
        
        # 2. Update daily & hourly aggregations incrementally
        now = event.created_at
        daily_id = now.strftime("%Y-%m-%d")
        hourly_id = now.strftime("%Y-%m-%d-%H")
        
        inc_data = {
            "total_requests": 1,
            "total_tokens": event.total_tokens,
            "total_cost": event.request_cost,
            "total_latency_ms": event.latency_metrics.total_request_time_ms
        }
        
        if event.cache_hit:
            inc_data["cache_hits"] = 1
        if event.summary_generated:
            inc_data["summary_count"] = 1
            
        # Hourly Update
        await self.db["analytics_hourly"].update_one(
            {"_id": hourly_id},
            {
                "$set": {"hour": hourly_id},
                "$inc": inc_data
            },
            upsert=True
        )
        
        # Daily Update
        await self.db["analytics_daily"].update_one(
            {"_id": daily_id},
            {
                "$set": {"date": daily_id},
                "$inc": inc_data
            },
            upsert=True
        )
        
        # 3. Update Realtime Active Interviews (if interview_id is present)
        if event.interview_id:
            await self.db["analytics_realtime"].update_one(
                {"interview_id": event.interview_id},
                {
                    "$set": {
                        "interview_id": event.interview_id,
                        "session_id": event.session_id,
                        "candidate_id": event.candidate_id,
                        "last_active": now
                    },
                    "$inc": {"request_count": 1},
                    "$setOnInsert": {"start_time": now}
                },
                upsert=True
            )

    async def remove_realtime_interview(self, interview_id: str):
        await self.db["analytics_realtime"].delete_one({"interview_id": interview_id})

    async def run_retention_policy(self, retention_days: int):
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Archive to a different collection (optional for production, but good practice if needed)
        # For this requirement, we'll just delete them to enforce retention.
        result = await self.db["analytics_events"].delete_many(
            {"created_at": {"$lt": cutoff_date}}
        )
        if result.deleted_count > 0:
            logger.info(f"Retention policy removed {result.deleted_count} old events.")

    async def update_system_health(self, health: SystemHealth):
        await self.db["system_health"].update_one(
            {"provider": health.provider, "model": health.model},
            {"$set": health.model_dump()},
            upsert=True
        )

    # Aggregation helpers for Dashboard Service
    async def get_daily_metrics(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        cursor = self.db["analytics_daily"].find(
            {"_id": {"$gte": start_date, "$lte": end_date}}
        ).sort("_id", 1)
        return await cursor.to_list(length=100)
