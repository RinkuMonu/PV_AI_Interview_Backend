from typing import List, Optional
from app.schemas.routing import RoutingRequest, RoutingResponse
from app.services.model_registry import model_registry
from app.services.capability_matcher import CapabilityMatcher
from app.services.routing_engine import RoutingEngine
from app.services.load_balancer import LoadBalancer
from app.services.fallback_manager import FallbackManager

class AIRouter:
    def __init__(self):
        self.capability_matcher = CapabilityMatcher()
        self.routing_engine = RoutingEngine()
        self.load_balancer = LoadBalancer()
        self.fallback_manager = FallbackManager()

    async def route_request(self, request: RoutingRequest) -> RoutingResponse:
        # 1. Gather all models
        all_models = model_registry.list_models()
        
        # 2. Filter by Capabilities
        valid_models = self.capability_matcher.match(request, all_models)
        if not valid_models:
            raise ValueError("No models support the requested capabilities.")
            
        # 3. Apply Routing Strategy (e.g. Lowest Cost, Lowest Latency)
        # Assuming balanced for now
        ranked_models = self.routing_engine.sort_models(request, valid_models, policy="balanced")
        
        # 4. We can optionally apply load balancing to the top tier models if scores are identical
        # Simplification: we just pass the ordered list to the FallbackManager
        
        # 5. Execute with Circuit Breaking and Fallbacks
        return await self.fallback_manager.execute(request, ranked_models)
