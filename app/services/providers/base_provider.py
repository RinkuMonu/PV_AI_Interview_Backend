from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ProviderNotConfiguredError(Exception):
    pass

class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def chat(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> Any:
        pass

    @abstractmethod
    async def stream_chat(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> Any:
        pass

    @abstractmethod
    async def embeddings(self, model: str, text: str) -> List[float]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pass

    @abstractmethod
    def estimate_latency(self, model: str) -> int:
        pass

    @abstractmethod
    def supports_capability(self, capability: str) -> bool:
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        pass
