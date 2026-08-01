import logging
from typing import Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_db
from app.schemas.token_usage import TokenUsageCreate, TokenUsageDB

logger = logging.getLogger("app.services.token_manager")

class TokenManager:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        """
        Initialize TokenManager with an optional DB connection.
        If not provided, it fetches the default DB connection lazily.
        """
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()
        
    @property
    def collection(self):
        return self.db["token_usage"]

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculates the estimated cost based on the model and token counts.
        (Costs per 1,000 tokens)
        """
        rates = {
            "llama3-8b-8192": {"prompt": 0.00005, "completion": 0.00008},
            "llama3-70b-8192": {"prompt": 0.00059, "completion": 0.00079},
            "mixtral-8x7b-32768": {"prompt": 0.00024, "completion": 0.00024},
            "gemma-7b-it": {"prompt": 0.00007, "completion": 0.00007},
            "gpt-oss-20b": {"prompt": 0.00020, "completion": 0.00020} # Groq API (GPT-OSS-20B) dummy rate
        }
        
        # Default fallback if model isn't in rates list
        model_rates = rates.get(model, {"prompt": 0.0001, "completion": 0.0001})
        
        prompt_cost = (prompt_tokens / 1000) * model_rates["prompt"]
        completion_cost = (completion_tokens / 1000) * model_rates["completion"]
        
        return prompt_cost + completion_cost

    async def log_usage(
        self,
        interview_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        endpoint_name: str,
        candidate_id: Optional[str] = None,
        subject: Optional[str] = None,
        request_time: Optional[datetime] = None,
        response_time: Optional[datetime] = None
    ) -> Optional[TokenUsageDB]:
        """
        Logs the token usage to the MongoDB collection asynchronously.
        Catches exceptions so it doesn't interrupt the main interview flow.
        """
        try:
            total_tokens = prompt_tokens + completion_tokens
            estimated_cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
            
            req_time = request_time or datetime.utcnow()
            res_time = response_time or datetime.utcnow()

            usage_data = TokenUsageCreate(
                interview_id=interview_id,
                candidate_id=candidate_id,
                subject=subject,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost,
                request_time=req_time,
                response_time=res_time,
                latency_ms=latency_ms,
                endpoint_name=endpoint_name
            )

            db_model = TokenUsageDB(**usage_data.dict())
            
            # Asynchronously insert into db
            result = await self.collection.insert_one(db_model.dict(exclude={"id"}))
            db_model.id = str(result.inserted_id)
            
            logger.info(f"Token usage logged for interview {interview_id}: {total_tokens} tokens (${estimated_cost:.5f}) via {endpoint_name}")
            
            return db_model
            
        except Exception as e:
            logger.error(f"Failed to log token usage: {str(e)}")
            return None

    async def get_interview_usage(self, interview_id: str) -> Dict[str, Any]:
        """
        Aggregates total tokens and cost for a specific interview.
        """
        try:
            pipeline = [
                {"$match": {"interview_id": interview_id}},
                {"$group": {
                    "_id": "$interview_id",
                    "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$completion_tokens"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "total_cost": {"$sum": "$estimated_cost"},
                    "request_count": {"$sum": 1},
                    "average_latency_ms": {"$avg": "$latency_ms"}
                }}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(1)
            
            if result:
                return result[0]
                
            return {
                "_id": interview_id,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "request_count": 0,
                "average_latency_ms": 0
            }
        except Exception as e:
            logger.error(f"Error fetching interview usage: {str(e)}")
            return {}

    async def get_candidate_usage(self, candidate_id: str) -> Dict[str, Any]:
        """
        Aggregates total tokens and cost for all interviews of a specific candidate.
        """
        try:
            pipeline = [
                {"$match": {"candidate_id": candidate_id}},
                {"$group": {
                    "_id": "$candidate_id",
                    "total_prompt_tokens": {"$sum": "$prompt_tokens"},
                    "total_completion_tokens": {"$sum": "$completion_tokens"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "total_cost": {"$sum": "$estimated_cost"},
                    "request_count": {"$sum": 1},
                    "interviews_count": {"$addToSet": "$interview_id"}
                }},
                {"$project": {
                    "total_prompt_tokens": 1,
                    "total_completion_tokens": 1,
                    "total_tokens": 1,
                    "total_cost": 1,
                    "request_count": 1,
                    "interviews_count": {"$size": "$interviews_count"}
                }}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(1)
            
            if result:
                return result[0]
            return {}
        except Exception as e:
            logger.error(f"Error fetching candidate usage: {str(e)}")
            return {}

# Dependency injection for FastAPI endpoints
def get_token_manager() -> TokenManager:
    return TokenManager()
