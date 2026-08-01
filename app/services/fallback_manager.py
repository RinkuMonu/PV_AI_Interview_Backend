import logging
import asyncio
import time
from typing import List, Dict, Any
from app.schemas.model import ModelConfig
from app.schemas.routing import RoutingRequest, RoutingResponse
from app.services.provider_registry import provider_registry
from app.services.health_monitor import health_monitor
from app.core.events import event_bus

logger = logging.getLogger("app.services.fallback_manager")

class FallbackManager:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def execute(self, request: RoutingRequest, ranked_models: List[ModelConfig]) -> RoutingResponse:
        for attempt, model in enumerate(ranked_models):
            provider = provider_registry.get_provider(model.provider)
            if not provider:
                continue

            # Circuit Breaker Check
            if not health_monitor.get_status(provider.name).is_active:
                logger.warning(f"Skipping {provider.name}: Circuit Breaker open.")
                continue

            start_time = time.time()
            try:
                # Execution
                if request.require_streaming:
                    result = await provider.stream_chat(model.model_name, request.messages)
                else:
                    result = await provider.chat(model.model_name, request.messages)
                
                latency_ms = int((time.time() - start_time) * 1000)
                await health_monitor.mark_success(provider.name, latency_ms)
                await event_bus.publish("provider_selected", {"provider": provider.name, "model": model.model_name})
                
                # Format Response (simplification for sandbox)
                usage = {}
                content = None
                if hasattr(result, "usage"):
                    usage = {"prompt_tokens": result.usage.prompt_tokens, "completion_tokens": result.usage.completion_tokens}
                if hasattr(result, "choices") and result.choices:
                    content = result.choices[0].message.content

                return RoutingResponse(
                    provider_name=provider.name,
                    model_name=model.model_name,
                    content=content,
                    usage=usage,
                    latency_ms=latency_ms
                )
                
            except Exception as e:
                # Fallback Triggered
                await health_monitor.mark_failure(provider.name)
                await event_bus.publish("fallback_triggered", {"failed_provider": provider.name, "error": str(e)})
                logger.error(f"Provider {provider.name} failed: {e}. Trying next fallback.")
                
                # Exponential backoff before next attempt if configured
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError("All providers and fallbacks failed to satisfy the request.")
