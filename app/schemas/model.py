from pydantic import BaseModel, ConfigDict
from typing import Optional

class ModelCapabilities(BaseModel):
    supports_streaming: bool = False
    supports_json: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_audio: bool = False
    supports_embeddings: bool = False

class ModelConfig(BaseModel):
    model_name: str
    provider: str
    context_window: int
    input_cost: float = 0.0 # Cost per 1M tokens or 1K tokens depending on config
    output_cost: float = 0.0
    capabilities: ModelCapabilities = ModelCapabilities()
    max_tokens: Optional[int] = None
    temperature_limits: Optional[tuple[float, float]] = None
    
    model_config = ConfigDict(protected_namespaces=())
