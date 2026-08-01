import logging
from typing import Dict, Any

from app.services.analytics_repository import AnalyticsRepository

logger = logging.getLogger("app.services.dashboard_service")

class DashboardService:
    def __init__(self, repository: AnalyticsRepository = None):
        self.repository = repository or AnalyticsRepository()

    async def get_overview(self) -> Dict[str, Any]:
        """
        Aggregate total metrics from analytics_events or analytics_daily.
        For speed, we sum the pre-aggregated daily collection.
        """
        db = self.repository.db
        
        pipeline = [
            {"$group": {
                "_id": None,
                "total_requests": {"$sum": "$total_requests"},
                "total_tokens": {"$sum": "$total_tokens"},
                "total_cost": {"$sum": "$total_cost"},
                "cache_hits": {"$sum": "$cache_hits"},
                "summary_count": {"$sum": "$summary_count"},
                "total_latency": {"$sum": "$total_latency_ms"}
            }}
        ]
        
        cursor = db["analytics_daily"].aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if not result:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "cache_hit_rate": 0.0,
                "summary_count": 0,
                "average_latency_ms": 0,
                "average_cost": 0.0
            }
            
        data = result[0]
        total_requests = data.get("total_requests", 0)
        
        cache_hit_rate = (data.get("cache_hits", 0) / total_requests * 100) if total_requests > 0 else 0.0
        average_latency = (data.get("total_latency", 0) / total_requests) if total_requests > 0 else 0.0
        average_cost = (data.get("total_cost", 0) / total_requests) if total_requests > 0 else 0.0
        
        return {
            "total_requests": total_requests,
            "total_tokens": data.get("total_tokens", 0),
            "total_cost": round(data.get("total_cost", 0.0), 4),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "summary_count": data.get("summary_count", 0),
            "average_latency_ms": round(average_latency, 2),
            "average_cost": round(average_cost, 4)
        }
