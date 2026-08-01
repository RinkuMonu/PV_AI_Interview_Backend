from typing import List
from app.schemas.model import ModelConfig

class LoadBalancer:
    def __init__(self):
        self._round_robin_counters = {}

    def select(self, models: List[ModelConfig]) -> ModelConfig:
        if not models:
            raise ValueError("No models available for load balancing")
        
        # Simple Round Robin implementation
        key = hash(tuple(m.model_name for m in models))
        count = self._round_robin_counters.get(key, 0)
        selected = models[count % len(models)]
        self._round_robin_counters[key] = count + 1
        return selected
