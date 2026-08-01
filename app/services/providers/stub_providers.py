from typing import List, Dict, Any
from app.services.providers.base_provider import BaseProvider, ProviderNotConfiguredError

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str = None):
        if not api_key:
            raise ProviderNotConfiguredError("OpenAI API key not configured")
            
    @property
    def name(self) -> str:
        return "openai"

    async def chat(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> Any:
        raise ProviderNotConfiguredError("OpenAI provider not configured")

    async def stream_chat(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> Any:
        raise ProviderNotConfiguredError()

    async def embeddings(self, model: str, text: str) -> List[float]:
        raise ProviderNotConfiguredError()

    async def health_check(self) -> bool:
        return False

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        return 0.0

    def estimate_latency(self, model: str) -> int:
        return 0

    def supports_capability(self, capability: str) -> bool:
        return False

    def list_models(self) -> List[str]:
        return []

# We create stubs for Gemini, Anthropic, Ollama, AzureOpenAI identically
class GeminiProvider(OpenAIProvider):
    @property
    def name(self) -> str: return "gemini"

class AnthropicProvider(OpenAIProvider):
    @property
    def name(self) -> str: return "anthropic"

class OllamaProvider(OpenAIProvider):
    @property
    def name(self) -> str: return "ollama"

class AzureOpenAIProvider(OpenAIProvider):
    @property
    def name(self) -> str: return "azure_openai"
