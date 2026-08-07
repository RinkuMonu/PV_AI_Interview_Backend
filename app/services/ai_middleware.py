import logging
from typing import Any, List

from app.schemas.ai_request_context import AIRequestContext
from app.core.ai_middleware_interfaces import AIExtension
from app.services.prompt_optimizer import PromptOptimizer

logger = logging.getLogger("app.services.ai_middleware")

class PromptOptimizerExtension(AIExtension):
    def __init__(self):
        self.optimizer = PromptOptimizer()
        
    async def pre_request(self, context: AIRequestContext, kwargs: dict) -> dict:
        if "messages" in kwargs:
            retained, removed, stats = self.optimizer.run_optimization(kwargs["messages"], context)
            
            kwargs["messages"] = retained
            context.removed_history = removed
            
            logger.info(
                f"Prompt Optimization | "
                f"Msgs: {stats['original_count']} -> {stats['optimized_count']} (-{stats['removed_count']}) | "
                f"Chars: {stats['original_chars']} -> {stats['optimized_chars']} ({stats['compression_pct']}% compressed)"
            )
            
        return kwargs

class SummaryManagerExtension(AIExtension):
    def __init__(self):
        from app.services.summary_manager import SummaryManager
        self.manager = SummaryManager()
        
    async def pre_request(self, context: AIRequestContext, kwargs: dict, groq_service: Any = None) -> dict:
        messages = kwargs.get("messages", [])
        if not messages:
            return kwargs
            
        # Extract total turns from prompt optimizer's _original_index magic or just a rough estimate
        # Since PromptOptimizer groups by turns, we can estimate total turns by user messages
        total_turns = sum(1 for m in messages if m.get("role") == "user") + (len(context.removed_history) // 3)
            
        if self.manager.should_summarize(context, total_turns):
            import time
            start_time = time.time()
            latest_summary = await self.manager.get_latest_summary(context.interview_id)
            summary_request = self.manager.prepare_summary_request(latest_summary, context.removed_history)
            
            # Execute summary generation via GroqService directly
            if groq_service:
                summary_response = await groq_service.execute_chat_completion(**summary_request)
                response_text = summary_response.choices[0].message.content if summary_response.choices else "{}"
                
                turns_added = sum(1 for m in context.removed_history if m.get("role") == "user")
                new_summary = self.manager.process_summary_response(context, response_text, latest_summary, turns_added)
                
                if latest_summary:
                    await self.manager.update_summary(new_summary)
                else:
                    await self.manager.create_summary(new_summary)
                    
                # Inject summary message right after the system prompt
                sys_msg_idx = next((i for i, m in enumerate(messages) if m.get("role") == "system"), 0)
                summary_message = {
                    "role": "system",
                    "content": f"PREVIOUS CONVERSATION SUMMARY:\n{new_summary.summary_text}\n"
                               f"STRENGTHS: {new_summary.candidate_strengths}\n"
                               f"WEAKNESSES: {new_summary.candidate_weaknesses}\n"
                               f"TOPICS COVERED: {new_summary.covered_topics}",
                    "persistent": True
                }
                messages.insert(sys_msg_idx + 1, summary_message)
                kwargs["messages"] = messages
                
                # Clear removed_history as it has been summarized
                context.removed_history = []
                
                latency = int((time.time() - start_time) * 1000)
                original_count = len(messages)
                logger.info(f"Summary Generated | Interview: {context.interview_id} | Turns: {turns_added} | Latency: {latency}ms")
                
        return kwargs

class CacheManagerExtension(AIExtension):
    def __init__(self):
        from app.services.cache_manager import CacheManager
        self.manager = CacheManager()
        
    async def pre_request(self, context: AIRequestContext, kwargs: dict, groq_service: Any = None) -> dict:
        if not self.manager.is_cacheable(context.endpoint_name):
            return kwargs
            
        messages = kwargs.get("messages", [])
        if not messages:
            return kwargs
            
        # Extract system prompt
        system_prompt = next((m.get("content", "") for m in messages if m.get("role") == "system"), "")
        
        # We need provider, model, prompt_version. We assume groq_service provides them or we fallback.
        # In this context, we will use mock values if not available, or extract from kwargs
        provider = kwargs.get("provider", "groq")
        model = kwargs.get("model", "llama-3.3-70b-versatile")
        prompt_version = kwargs.get("prompt_version", "1.0")
        
        keys = self.manager.generate_cache_key(
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            system_prompt=system_prompt,
            context=context,
            messages=messages
        )
        
        context.cache_key = keys["cache_key"]
        
        # Check cache
        import time
        start_time = time.time()
        cached_doc = await self.manager.get_cached_response(context.cache_key)
        
        if cached_doc:
            context.cache_hit = True
            context.cached_response = cached_doc.response
            latency = int((time.time() - start_time) * 1000)
            
            # Simple token estimation for logging (e.g. 4 chars = 1 token roughly)
            estimated_tokens = len(str(messages)) // 4
            logger.info(f"Cache Hit | Key: {context.cache_key[:8]}... | Saved ~{estimated_tokens} tokens | Saved >{latency}ms")
        else:
            logger.info(f"Cache Miss | Key: {context.cache_key[:8]}...")
            
        # Store metadata for post_request saving
        context._cache_metadata = {
            "prompt_hash": keys["prompt_hash"],
            "system_prompt_hash": keys["system_prompt_hash"],
            "provider": provider,
            "model": model,
            "prompt_version": prompt_version
        }
            
        return kwargs
        
    async def post_request(self, context: AIRequestContext, kwargs: dict, response: Any, latency_ms: int) -> Any:
        if context.cache_key and not context.cache_hit and self.manager.is_cacheable(context.endpoint_name):
            meta = getattr(context, "_cache_metadata", {})
            if meta:
                await self.manager.save_response(
                    cache_key=context.cache_key,
                    prompt_hash=meta["prompt_hash"],
                    system_prompt_hash=meta["system_prompt_hash"],
                    provider=meta["provider"],
                    model=meta["model"],
                    prompt_version=meta["prompt_version"],
                    context=context,
                    response=response
                )
                logger.info(f"Cache Save | Key: {context.cache_key[:8]}...")
        return response

class BudgetManagerExtension(AIExtension):
    def __init__(self):
        from app.services.budget_manager import BudgetManager
        self.manager = BudgetManager()
        
    async def pre_request(self, context: AIRequestContext, kwargs: dict, groq_service: Any = None) -> dict:
        # We need model to initialize budget
        model = kwargs.get("model", "llama-3.3-70b-versatile")
        
        # Initialize budget if missing
        budget = await self.manager.initialize_budget(context.interview_id or "unknown", model, context)
        
        # Determine budget state
        level = budget.status.budget_level
        
        if self.manager.should_stop_interview(level):
            logger.error(f"Budget LIMIT_EXCEEDED for interview {context.interview_id}. Stopping AI generation.")
            # Raising exception to abort middleware chain safely
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="Interview budget limit exceeded.")
            
        if self.manager.should_enforce_grace_mode(level):
            if not context.is_essential:
                logger.warning(f"Rejecting non-essential request in GRACE_MODE for {context.interview_id}.")
                raise HTTPException(status_code=429, detail="Only essential requests permitted in Grace Mode.")
            context.grace_mode = True
            
        if self.manager.should_reduce_context(level):
            context.aggressive_compression = True
            
        if self.manager.should_trigger_summary(level):
            context.force_summary = True
            
        return kwargs
        
    async def post_request(self, context: AIRequestContext, kwargs: dict, response: Any, latency_ms: int) -> Any:
        # Mocking token extraction since TokenManager isn't fully implemented in this phase
        # In reality, TokenManager extracts these and we read them.
        prompt_tokens = 0
        completion_tokens = 0
        
        if not context.cache_hit and response and hasattr(response, "usage") and response.usage:
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
            completion_tokens = getattr(response.usage, "completion_tokens", 0)
            
        if prompt_tokens > 0 or completion_tokens > 0:
            # Simple mock cost calculation (e.g., $0.01 per 1k tokens)
            cost = (prompt_tokens + completion_tokens) / 1000 * 0.01
            
            await self.manager.update_usage(
                interview_id=context.interview_id or "unknown",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost=cost
            )
            
            budget = await self.manager.get_budget_status(context.interview_id or "unknown")
            if budget:
                logger.info(
                    f"Usage Tracked | ID: {context.interview_id} | "
                    f"Tokens: {prompt_tokens}p/{completion_tokens}c | "
                    f"Cost: ${budget.usage.total_cost:.4f} | "
                    f"Level: {budget.status.budget_level} | "
                    f"Remaining: {self.manager.remaining_tokens(budget)}t"
                )
        return response

class AnalyticsExtension(AIExtension):
    async def pre_request(self, context: AIRequestContext, kwargs: dict, groq_service: Any = None) -> dict:
        import time
        import uuid
        context._analytics_start_time = time.time()
        
        # Ensure trace_id and request_id exist
        if not context.trace_id:
            context.trace_id = str(uuid.uuid4())
        if not context.request_id:
            context.request_id = str(uuid.uuid4())
            
        return kwargs
        
    async def post_request(self, context: AIRequestContext, kwargs: dict, response: Any, latency_ms: int) -> Any:
        import time
        from app.core.events import event_bus
        from app.services.budget_manager import BudgetManager
        
        start_time = getattr(context, "_analytics_start_time", time.time())
        total_time_ms = int((time.time() - start_time) * 1000)
        
        # Determine token usage from budget manager or response
        bm = BudgetManager()
        budget = await bm.get_budget_status(context.interview_id or "unknown")
        budget_level = budget.status.budget_level if budget else "SAFE"
        
        prompt_tokens = 0
        completion_tokens = 0
        request_cost = 0.0
        
        if not context.cache_hit and response and hasattr(response, "usage") and response.usage:
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
            completion_tokens = getattr(response.usage, "completion_tokens", 0)
            request_cost = (prompt_tokens + completion_tokens) / 1000 * 0.01
        
        # Calculate middleware vs LLM time
        middleware_time_ms = total_time_ms - latency_ms
        
        # Capture error details if passed
        error_details = None
        if hasattr(context, "_captured_error"):
            import hashlib
            exc = context._captured_error
            stack_hash = hashlib.md5(str(exc).encode('utf-8')).hexdigest()
            error_details = {
                "error_type": type(exc).__name__,
                "error_source": "groq_service",
                "provider": kwargs.get("provider", "groq"),
                "retry_count": 0,
                "recoverable": False,
                "stack_trace_hash": stack_hash
            }
        
        payload = {
            "request_id": context.request_id,
            "trace_id": context.trace_id,
            "interview_id": context.interview_id,
            "session_id": context.session_id,
            "candidate_id": context.candidate_id,
            "endpoint": context.endpoint_name,
            "provider": kwargs.get("provider", "groq"),
            "model": kwargs.get("model", "llama3"),
            "queue_time_ms": 0,
            "middleware_time_ms": middleware_time_ms,
            "llm_time_ms": latency_ms,
            "db_time_ms": 0,
            "total_request_time_ms": total_time_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "request_cost": request_cost,
            "cache_hit": context.cache_hit,
            "cache_key": context.cache_key,
            "summary_generated": context.force_summary,
            "compression_ratio": getattr(context, "compression_ratio", 0.0),
            "budget_level": budget_level,
            "optimization_actions": [],
            "error": error_details
        }
        
        if context.grace_mode: payload["optimization_actions"].append("grace_mode")
        if context.aggressive_compression: payload["optimization_actions"].append("aggressive_compression")
        
        # Fire and forget publishing
        await event_bus.publish("ai_request_completed", payload)
        return response

class AIMiddleware:
    def __init__(self):
        # Optimization priority: 1. Cache, 2. Prompt Optimizer, 3. Summary Manager, (4. Context Reduction via flags, 5. Grace, 6. Stop via Budget)
        # BudgetManager runs first in pre to set flags, and last in post to track final usage.
        # AnalyticsExtension runs absolutely last to observe everything.
        self.extensions: List[AIExtension] = [
            BudgetManagerExtension(),
            CacheManagerExtension(),
            PromptOptimizerExtension(),
            SummaryManagerExtension(),
            AnalyticsExtension()
        ]

    async def generate_response(self, context: AIRequestContext, **kwargs) -> Any:
        from app.services.ai_router import AIRouter
        from app.schemas.routing import RoutingRequest
        
        # 1. Execute pre_request extensions
        for ext in self.extensions:
            kwargs = await ext.pre_request(context, kwargs, None)
            
        if context.cache_hit and context.cached_response is not None:
            # We don't execute the LLM, but we still run post_request hooks for other extensions
            response = context.cached_response
            latency_ms = 0
        else:
            # 2. Call the AI Router
            import time
            start_time = time.time()
            router = AIRouter()
            
            # Map kwargs to a RoutingRequest. 
            # In production, callers would build this directly.
            req = RoutingRequest(
                task_type="chat",
                messages=kwargs.get("messages", []),
                temperature=kwargs.get("temperature", 0.7),
                require_json=kwargs.get("response_format", {}).get("type") == "json_object"
            )
            
            try:
                # The router handles fallback, execution, and returning a RoutingResponse
                route_resp = await router.route_request(req)
                
                # Mocking a response object structure so existing extensions that expect 
                # object-notation (like `response.usage.prompt_tokens`) don't break.
                class MockUsage:
                    prompt_tokens = route_resp.usage.get("prompt_tokens", 0)
                    completion_tokens = route_resp.usage.get("completion_tokens", 0)
                class MockChoice:
                    message = type("Msg", (), {"content": route_resp.content})()
                class MockResponse:
                    choices = [MockChoice()]
                    usage = MockUsage()
                
                response = MockResponse()
                kwargs["provider"] = route_resp.provider_name
                kwargs["model"] = route_resp.model_name
                
            except Exception as e:
                # Capture error for analytics
                context._captured_error = e
                response = None
            finally:
                latency_ms = int((time.time() - start_time) * 1000)
        
        # 3. Execute post_request extensions
        for ext in self.extensions:
            response = await ext.post_request(context, kwargs, response, latency_ms)
            
        # If there was an error, re-raise it after analytics has recorded it
        if hasattr(context, "_captured_error") and context._captured_error:
            raise context._captured_error
            
        return response
