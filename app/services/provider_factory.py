from typing import Optional
from app.services.providers.base_provider import BaseProvider
from app.services.providers.groq_provider import GroqProvider
from app.services.providers.stub_providers import OpenAIProvider, GeminiProvider, AnthropicProvider, OllamaProvider, AzureOpenAIProvider

class ProviderFactory:
    @staticmethod
    def create(name: str, config: dict) -> BaseProvider:
        api_key = config.get("api_key")
        if name == "groq":
            return GroqProvider(api_key=api_key or "mock_key")
        elif name == "openai":
            return OpenAIProvider(api_key=api_key)
        elif name == "gemini":
            return GeminiProvider(api_key=api_key)
        elif name == "anthropic":
            return AnthropicProvider(api_key=api_key)
        elif name == "ollama":
            return OllamaProvider(api_key=api_key)
        elif name == "azure_openai":
            return AzureOpenAIProvider(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {name}")
