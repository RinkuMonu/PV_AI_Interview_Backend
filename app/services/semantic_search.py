from typing import List
from app.schemas.interview_question import InterviewQuestion
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.question_repository import QuestionRepository

class SemanticSearch:
    def __init__(self, repo: QuestionRepository, embedding_service: EmbeddingService):
        self.repo = repo
        self.embedding_service = embedding_service

    async def recommend_questions(self, topic: str, limit: int = 10) -> List[InterviewQuestion]:
        # Simple lookup by topic
        return await self.repo.search_by_topic(topic, limit=limit)

    async def search_by_similarity(self, query: str, limit: int = 10) -> List[InterviewQuestion]:
        query_embedding = await self.embedding_service.get_embedding(query)
        return await self.repo.vector_search(query_embedding, limit=limit)
