import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException

from app.core.config import settings
from app.schemas.ai_request_context import AIRequestContext
from app.schemas.budget_status import InterviewBudget, BudgetPolicy, BudgetEvent
from app.core.database import get_db

logger = logging.getLogger("app.services.budget_manager")

class BudgetManager:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()
        
    @property
    def collection(self):
        return self.db["interview_budget"]
        
    @property
    def events_collection(self):
        return self.db["budget_events"]

    async def initialize_budget(self, interview_id: str, model: str, context: AIRequestContext) -> InterviewBudget:
        policy = BudgetPolicy(
            max_prompt_tokens=getattr(settings, "MAX_PROMPT_TOKENS", 50000),
            max_completion_tokens=getattr(settings, "MAX_COMPLETION_TOKENS", 10000),
            max_total_tokens=getattr(settings, "MAX_TOTAL_TOKENS", 60000),
            max_cost=getattr(settings, "MAX_INTERVIEW_COST", 0.50),
            warning_threshold=getattr(settings, "WARNING_THRESHOLD", 80),
            critical_threshold=getattr(settings, "CRITICAL_THRESHOLD", 90),
            grace_threshold=getattr(settings, "GRACE_THRESHOLD", 100),
            stop_threshold=getattr(settings, "STOP_THRESHOLD", 110),
        )
        
        budget = InterviewBudget(
            interview_id=interview_id,
            session_id=context.session_id,
            candidate_id=context.candidate_id,
            interview_type=context.interview_type,
            subject=context.subject,
            model=model,
            budget=policy
        )
        
        await self.collection.update_one(
            {"interview_id": interview_id},
            {"$setOnInsert": budget.model_dump()},
            upsert=True
        )
        
        return await self.get_budget_status(interview_id) or budget

    async def get_budget_status(self, interview_id: str) -> Optional[InterviewBudget]:
        doc = await self.collection.find_one({"interview_id": interview_id})
        if doc:
            return InterviewBudget(**doc)
        return None

    def calculate_utilization(self, budget: InterviewBudget) -> Tuple[float, str]:
        # Based on cost first, or total tokens if cost is 0
        if budget.budget.max_cost > 0:
            pct = (budget.usage.total_cost / budget.budget.max_cost) * 100
        elif budget.budget.max_total_tokens > 0:
            pct = (budget.usage.total_tokens_used / budget.budget.max_total_tokens) * 100
        else:
            pct = 0.0
            
        level = "SAFE"
        if pct > budget.budget.stop_threshold:
            level = "LIMIT_EXCEEDED"
        elif pct > budget.budget.grace_threshold:
            level = "GRACE_MODE"
        elif pct > budget.budget.critical_threshold:
            level = "CRITICAL"
        elif pct > budget.budget.warning_threshold:
            level = "WARNING"
        elif pct > 60: # 60%
            level = "NORMAL"
            
        return pct, level

    def remaining_tokens(self, budget: InterviewBudget) -> int:
        return max(0, budget.budget.max_total_tokens - budget.usage.total_tokens_used)

    def remaining_cost(self, budget: InterviewBudget) -> float:
        return max(0.0, budget.budget.max_cost - budget.usage.total_cost)

    async def update_usage(self, interview_id: str, prompt_tokens: int, completion_tokens: int, cost: float):
        budget = await self.get_budget_status(interview_id)
        if not budget:
            return
            
        budget.usage.prompt_tokens_used += prompt_tokens
        budget.usage.completion_tokens_used += completion_tokens
        budget.usage.total_tokens_used += (prompt_tokens + completion_tokens)
        budget.usage.total_cost += cost
        
        pct, level = self.calculate_utilization(budget)
        
        # Determine if level changed to trigger optimization record
        level_changed = budget.status.budget_level != level
        
        budget.status.utilization_percentage = pct
        budget.status.budget_level = level
        budget.updated_at = datetime.utcnow()
        
        await self.collection.update_one(
            {"interview_id": interview_id},
            {"$set": {
                "usage": budget.usage.model_dump(),
                "status": budget.status.model_dump(),
                "updated_at": budget.updated_at
            }}
        )
        
        if level_changed:
            await self.record_optimization(interview_id, level, "Level Transition", f"Budget reached {pct:.1f}%")

    async def record_optimization(self, interview_id: str, budget_level: str, action: str, reason: str):
        budget = await self.get_budget_status(interview_id)
        if not budget:
            return
            
        event = BudgetEvent(
            interview_id=interview_id,
            budget_level=budget_level,
            action=action,
            reason=reason,
            prompt_tokens=budget.usage.prompt_tokens_used,
            completion_tokens=budget.usage.completion_tokens_used,
            total_tokens=budget.usage.total_tokens_used,
            total_cost=budget.usage.total_cost
        )
        await self.events_collection.insert_one(event.model_dump())
        logger.warning(f"Optimization Action [{budget_level}]: {action} - {reason}")
        
        # Track in main budget record
        budget.optimization.optimization_actions.append(f"{datetime.utcnow().isoformat()}: {action}")
        await self.collection.update_one(
            {"interview_id": interview_id},
            {"$set": {"optimization.optimization_actions": budget.optimization.optimization_actions[-10:]}} # Keep last 10
        )

    # Policy checks based on current level
    def should_trigger_summary(self, level: str) -> bool:
        return level in ["WARNING", "CRITICAL", "GRACE_MODE", "LIMIT_EXCEEDED"]

    def should_reduce_context(self, level: str) -> bool:
        return level in ["WARNING", "CRITICAL", "GRACE_MODE", "LIMIT_EXCEEDED"]
        
    def should_disable_cache(self, level: str) -> bool:
        # We generally INCREASE cache priority to save money, we do not disable it.
        return False
        
    def should_enforce_grace_mode(self, level: str) -> bool:
        return level in ["GRACE_MODE", "LIMIT_EXCEEDED"]

    def should_stop_interview(self, level: str) -> bool:
        return level == "LIMIT_EXCEEDED"

    # Future compatibility stubs
    def _ai_analytics_hook(self): pass
    def _multi_model_router_hook(self): pass
    def _auto_scaling_hook(self): pass
    def _dynamic_policies_hook(self): pass
