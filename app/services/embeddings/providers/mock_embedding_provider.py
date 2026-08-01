from typing import List
from app.services.embeddings.embedding_provider import EmbeddingProvider

class MockEmbeddingProvider(EmbeddingProvider):
    """
    A stubbed provider used until a real provider (e.g. OpenAI) is fully configured.
    Generates dummy vectors of length 1536 for structural testing.
    """
    async def generate_embedding(self, text: str) -> List[float]:
        return [0.0] * 1536

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * 1536 for _ in texts]
