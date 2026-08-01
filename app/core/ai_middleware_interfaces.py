from abc import ABC, abstractmethod
from typing import Any
from app.schemas.ai_request_context import AIRequestContext

class AIExtension(ABC):
    async def pre_request(self, context: AIRequestContext, kwargs: dict, groq_service: Any = None) -> dict:
        """Modify or prepare request before hitting the AI API."""
        return kwargs
        
    async def post_request(self, context: AIRequestContext, kwargs: dict, response: Any, latency_ms: int) -> Any:
        """Process the response after hitting the AI API."""
        return response

class BudgetManagerExtension(AIExtension):
    pass

class CacheManagerExtension(AIExtension):
    pass

class QuestionManagerExtension(AIExtension):
    pass
