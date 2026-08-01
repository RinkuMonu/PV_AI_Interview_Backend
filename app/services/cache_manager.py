import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.schemas.ai_cache import AICache
from app.schemas.ai_request_context import AIRequestContext
from app.core.database import get_db

logger = logging.getLogger("app.services.cache_manager")

class CacheManager:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db
        self.cacheable_endpoints = {
            "evaluation_prompt",
            "rubric_analysis",
            "candidate_profile_analysis",
            "question_explanation",
            "resume_analysis"
        }
        self.ttl_hours = getattr(settings, "CACHE_TTL_HOURS", 24)

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()
        
    @property
    def collection(self):
        return self.db["ai_cache"]

    def is_cacheable(self, endpoint_name: str) -> bool:
        return endpoint_name in self.cacheable_endpoints

    def _normalize_prompt(self, messages: List[Dict[str, Any]]) -> str:
        # Simplistic normalization: stringify and lowercase
        # In a robust system, we might sort keys or trim extra whitespace thoroughly
        try:
            return json.dumps(messages, sort_keys=True).strip().lower()
        except Exception:
            return str(messages).strip().lower()

    def generate_cache_key(self, provider: str, model: str, prompt_version: str, system_prompt: str, context: AIRequestContext, messages: List[Dict[str, Any]]) -> Dict[str, str]:
        system_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
        normalized_prompt = self._normalize_prompt(messages)
        prompt_hash = hashlib.sha256(normalized_prompt.encode("utf-8")).hexdigest()
        
        # Format: Provider|Model|PromptVersion|SystemHash|Endpoint|Type|Subject|PromptHash
        type_str = context.interview_type or "none"
        subject_str = context.subject or "none"
        
        key_string = f"{provider}|{model}|{prompt_version}|{system_hash}|{context.endpoint_name}|{type_str}|{subject_str}|{prompt_hash}"
        cache_key = hashlib.sha256(key_string.encode("utf-8")).hexdigest()
        
        return {
            "cache_key": cache_key,
            "prompt_hash": prompt_hash,
            "system_prompt_hash": system_hash
        }

    async def get_cached_response(self, cache_key: str) -> Optional[AICache]:
        doc = await self.collection.find_one({"cache_key": cache_key})
        if not doc:
            return None
            
        cache_item = AICache(**doc)
        
        # Check expiration
        if datetime.utcnow() > cache_item.expires_at:
            await self.invalidate_cache(cache_key)
            return None
            
        # Update last accessed and hit count asynchronously
        await self.collection.update_one(
            {"cache_key": cache_key},
            {
                "$set": {"last_accessed": datetime.utcnow()},
                "$inc": {"hit_count": 1}
            }
        )
        return cache_item

    async def save_response(self, cache_key: str, prompt_hash: str, system_prompt_hash: str, provider: str, model: str, prompt_version: str, context: AIRequestContext, response: Any):
        expires_at = datetime.utcnow() + timedelta(hours=self.ttl_hours)
        
        cache_item = AICache(
            cache_key=cache_key,
            prompt_hash=prompt_hash,
            model=model,
            provider=provider,
            system_prompt_hash=system_prompt_hash,
            prompt_version=prompt_version,
            response=response,
            endpoint_name=context.endpoint_name,
            interview_type=context.interview_type,
            subject=context.subject,
            expires_at=expires_at
        )
        
        await self.collection.update_one(
            {"cache_key": cache_key},
            {"$set": cache_item.model_dump()},
            upsert=True
        )

    async def invalidate_cache(self, cache_key: str = None, cache_version: int = None):
        """Invalidate by cache_key or bulk invalidate by cache_version."""
        if cache_key:
            await self.collection.delete_one({"cache_key": cache_key})
        elif cache_version is not None:
            await self.collection.delete_many({"cache_version": cache_version})
