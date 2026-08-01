import asyncio
import logging
from typing import Dict
from datetime import datetime
from app.schemas.provider import ProviderStatus
from app.services.provider_registry import provider_registry
from app.core.events import event_bus

logger = logging.getLogger("app.services.health_monitor")

class HealthMonitor:
    def __init__(self):
        self._health_status: Dict[str, ProviderStatus] = {}
        self._running = False
        
    def initialize_provider(self, name: str):
        if name not in self._health_status:
            self._health_status[name] = ProviderStatus(name=name)
            
    def get_status(self, name: str) -> ProviderStatus:
        self.initialize_provider(name)
        return self._health_status[name]

    async def mark_success(self, provider_name: str, latency_ms: int):
        self.initialize_provider(provider_name)
        status = self._health_status[provider_name]
        status.success_rate = (status.success_rate * 0.9) + 0.1
        status.failure_rate = (status.failure_rate * 0.9)
        status.average_latency_ms = (status.average_latency_ms * 0.9) + (latency_ms * 0.1)
        if not status.is_active:
            status.is_active = True
            await event_bus.publish("provider_recovered", {"provider": provider_name})

    async def mark_failure(self, provider_name: str):
        self.initialize_provider(provider_name)
        status = self._health_status[provider_name]
        status.success_rate = (status.success_rate * 0.9)
        status.failure_rate = (status.failure_rate * 0.9) + 0.1
        if status.failure_rate > 0.5 and status.is_active:
            status.is_active = False
            await event_bus.publish("provider_failed", {"provider": provider_name})

    async def _monitor_loop(self, interval_seconds: int = 60):
        while self._running:
            for name in provider_registry.list_providers():
                provider = provider_registry.get_provider(name)
                if provider:
                    try:
                        is_healthy = await provider.health_check()
                        status = self.get_status(name)
                        status.last_heartbeat = datetime.utcnow().isoformat()
                        if not is_healthy and status.is_active:
                            status.is_active = False
                            await event_bus.publish("provider_failed", {"provider": name})
                        elif is_healthy and not status.is_active:
                            status.is_active = True
                            await event_bus.publish("provider_recovered", {"provider": name})
                    except Exception as e:
                        logger.error(f"Health check failed for {name}: {e}")
            await asyncio.sleep(interval_seconds)

    def start(self, interval_seconds: int = 60):
        if not self._running:
            self._running = True
            asyncio.create_task(self._monitor_loop(interval_seconds))

    def stop(self):
        self._running = False

# Singleton instance
health_monitor = HealthMonitor()
