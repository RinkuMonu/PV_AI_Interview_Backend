import logging
from typing import Dict, Any

from app.core.events import event_bus
from app.schemas.analytics import AnalyticsEvent, LatencyMetrics
from app.services.analytics_repository import AnalyticsRepository

logger = logging.getLogger("app.services.analytics_manager")

class AnalyticsManager:
    def __init__(self, repository: AnalyticsRepository = None):
        self.repository = repository or AnalyticsRepository()
        self._subscribe_to_events()
        
    def _subscribe_to_events(self):
        event_bus.subscribe("ai_request_completed", self.handle_ai_request_completed)
        event_bus.subscribe("interview_finished", self.handle_interview_finished)
        logger.info("AnalyticsManager subscribed to events")

    async def handle_interview_finished(self, payload: Dict[str, Any]):
        interview_id = payload.get("interview_id")
        if interview_id:
            await self.repository.remove_realtime_interview(interview_id)
            logger.debug(f"Removed realtime tracking for finished interview {interview_id}")

            # Also trigger retention cleanup as a background maintenance task periodically
            from app.core.config import settings
            retention_days = getattr(settings, "ANALYTICS_RETENTION_DAYS", 90)
            await self.repository.run_retention_policy(retention_days)

    async def handle_ai_request_completed(self, payload: Dict[str, Any]):
        """
        Passive observer handler. Receives dictionary payload from the middleware publisher,
        parses it into an AnalyticsEvent, and passes it to the repository.
        """
        try:
            latency = LatencyMetrics(
                queue_time_ms=payload.get("queue_time_ms", 0),
                middleware_time_ms=payload.get("middleware_time_ms", 0),
                llm_time_ms=payload.get("llm_time_ms", 0),
                db_time_ms=payload.get("db_time_ms", 0),
                total_request_time_ms=payload.get("total_request_time_ms", 0)
            )
            
            # Handle Error Details
            error_details = None
            if payload.get("error"):
                from app.schemas.analytics import ErrorDetails
                error_dict = payload.get("error", {})
                error_details = ErrorDetails(
                    error_type=error_dict.get("error_type", "UnknownError"),
                    error_source=error_dict.get("error_source", "unknown"),
                    provider=error_dict.get("provider", payload.get("provider", "unknown")),
                    retry_count=error_dict.get("retry_count", 0),
                    recoverable=error_dict.get("recoverable", False),
                    stack_trace_hash=error_dict.get("stack_trace_hash")
                )

            event = AnalyticsEvent(
                request_id=payload.get("request_id", "unknown"),
                trace_id=payload.get("trace_id", "unknown"),
                interview_id=payload.get("interview_id"),
                session_id=payload.get("session_id"),
                candidate_id=payload.get("candidate_id"),
                endpoint=payload.get("endpoint", "unknown"),
                provider=payload.get("provider", "unknown"),
                model=payload.get("model", "unknown"),
                latency_metrics=latency,
                prompt_tokens=payload.get("prompt_tokens", 0),
                completion_tokens=payload.get("completion_tokens", 0),
                total_tokens=payload.get("total_tokens", 0),
                request_cost=payload.get("request_cost", 0.0),
                cache_hit=payload.get("cache_hit", False),
                cache_key=payload.get("cache_key"),
                summary_generated=payload.get("summary_generated", False),
                compression_ratio=payload.get("compression_ratio", 0.0),
                budget_level=payload.get("budget_level", "SAFE"),
                optimization_actions=payload.get("optimization_actions", []),
                error_details=error_details
            )
            
            await self.repository.save_event(event)
            logger.debug(f"Analytics event saved for interview {event.interview_id}")
            
        except Exception as e:
            logger.error(f"Failed to process analytics event: {e}")
