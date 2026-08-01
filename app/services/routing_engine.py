from abc import ABC, abstractmethod
from typing import List
from app.schemas.model import ModelConfig
from app.schemas.routing import RoutingRequest
from app.services.health_monitor import health_monitor

class RoutingStrategy(ABC):
    @abstractmethod
    def score_models(self, request: RoutingRequest, models: List[ModelConfig]) -> List[ModelConfig]:
        pass

class LowestCostStrategy(RoutingStrategy):
    def score_models(self, request: RoutingRequest, models: List[ModelConfig]) -> List[ModelConfig]:
        # Sort by total cost per token
        return sorted(models, key=lambda m: m.input_cost + m.output_cost)

class LowestLatencyStrategy(RoutingStrategy):
    def score_models(self, request: RoutingRequest, models: List[ModelConfig]) -> List[ModelConfig]:
        # Sort by average latency tracked in health monitor
        return sorted(
            models, 
            key=lambda m: health_monitor.get_status(m.provider).average_latency_ms
        )

class RoutingEngine:
    def __init__(self):
        self.strategies = {
            "lowest_cost": LowestCostStrategy(),
            "lowest_latency": LowestLatencyStrategy(),
            "balanced": LowestCostStrategy() # Simplified for sandbox
        }

    def sort_models(self, request: RoutingRequest, models: List[ModelConfig], policy: str = "balanced") -> List[ModelConfig]:
        strategy = self.strategies.get(policy, self.strategies["balanced"])
        return strategy.score_models(request, models)
