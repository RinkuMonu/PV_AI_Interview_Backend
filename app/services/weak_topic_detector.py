from app.services.knowledge_graph_repository import KnowledgeGraphRepository
from app.schemas.knowledge_graph import CandidateKnowledgeGraph

class WeakTopicDetector:
    def __init__(self, kg_repo: KnowledgeGraphRepository):
        self.kg_repo = kg_repo

    async def analyze_performance(self, candidate_id: str, subject: str, topic: str, score: float):
        # Retrieve existing node or create
        # Simplified: Upsert an updated node
        graph = CandidateKnowledgeGraph(
            candidate_id=candidate_id,
            subject=subject,
            topic=topic,
            mastery_score=score,
            attempt_count=1
        )
        await self.kg_repo.update_node(graph)
