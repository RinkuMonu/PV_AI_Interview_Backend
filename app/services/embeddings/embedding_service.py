from app.services.embeddings.embedding_provider import EmbeddingProvider
from app.services.embeddings.providers.mock_embedding_provider import MockEmbeddingProvider

class EmbeddingService:
    def __init__(self, provider: EmbeddingProvider = None):
        # Default to a mock provider until configuration injection is implemented
        self.provider = provider or MockEmbeddingProvider()

    async def get_embedding(self, text: str) -> list[float]:
        return await self.provider.generate_embedding(text)

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        return await self.provider.generate_embeddings(texts)
