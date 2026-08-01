from typing import List
from app.schemas.model import ModelConfig
from app.schemas.routing import RoutingRequest

class CapabilityMatcher:
    @staticmethod
    def match(request: RoutingRequest, models: List[ModelConfig]) -> List[ModelConfig]:
        valid_models = []
        for model in models:
            caps = model.capabilities
            
            if request.require_streaming and not caps.supports_streaming:
                continue
            if request.require_json and not caps.supports_json:
                continue
            if request.max_tokens and model.context_window < request.max_tokens:
                continue
                
            valid_models.append(model)
            
        return valid_models
