from typing import List, Dict, Optional
from app.schemas.model import ModelConfig, ModelCapabilities

class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}

    def load_from_config(self, models_config: List[dict]):
        for cfg in models_config:
            cap_dict = cfg.pop("capabilities", {})
            capabilities = ModelCapabilities(**cap_dict)
            model = ModelConfig(capabilities=capabilities, **cfg)
            self._models[model.model_name] = model

    def get_model(self, model_name: str) -> Optional[ModelConfig]:
        return self._models.get(model_name)

    def list_models(self) -> List[ModelConfig]:
        return list(self._models.values())

# Singleton instance
model_registry = ModelRegistry()

# Load a default model strictly for fallback so testing works
model_registry.load_from_config([
    {
        "model_name": "llama3-8b-8192",
        "provider": "groq",
        "context_window": 8192,
        "input_cost": 0.05,
        "output_cost": 0.08,
        "capabilities": {
            "supports_streaming": True,
            "supports_json": True
        }
    }
])
