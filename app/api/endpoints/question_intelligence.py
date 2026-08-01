from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.schemas.interview_state import InterviewState
from app.schemas.interview_question import InterviewQuestion
from app.schemas.followup_question import FollowupQuestion
from app.services.question_engine import QuestionEngine
from app.services.followup_generator import FollowupGenerator
from app.services.strategies.adaptive_strategy import AdaptiveStrategy
from app.services.semantic_search import SemanticSearch
from app.services.duplicate_detector import DuplicateDetector
from app.services.difficulty_manager import DifficultyManager
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.question_repository import QuestionRepository
from app.services.history_repository import HistoryRepository

router = APIRouter()

def get_question_engine() -> QuestionEngine:
    # Dependency Injection assembly
    embedding_svc = EmbeddingService()
    q_repo = QuestionRepository()
    h_repo = HistoryRepository()
    
    strategy = AdaptiveStrategy()
    semantic_search = SemanticSearch(q_repo, embedding_svc)
    duplicate_detector = DuplicateDetector(h_repo)
    difficulty_manager = DifficultyManager()
    
    return QuestionEngine(
        strategy=strategy,
        semantic_search=semantic_search,
        duplicate_detector=duplicate_detector,
        difficulty_manager=difficulty_manager
    )

def get_followup_generator() -> FollowupGenerator:
    # Mocking AIMiddleware injection for routes
    class MockAIMiddleware:
        pass
    return FollowupGenerator(ai_middleware=MockAIMiddleware())

@router.post("/next", response_model=InterviewQuestion)
async def get_next_question(
    state: InterviewState,
    engine: QuestionEngine = Depends(get_question_engine)
):
    question = await engine.get_next_question(state)
    if not question:
        raise HTTPException(status_code=404, detail="Could not determine next question or interview complete.")
    return question

@router.post("/followup", response_model=Dict[str, str])
async def generate_followup(
    candidate_answer: str,
    generator: FollowupGenerator = Depends(get_followup_generator)
):
    followup_text = await generator.generate(context_data={}, candidate_answer=candidate_answer)
    return {"followup": followup_text}

@router.get("/recommend")
async def recommend_questions(
    topic: str,
    engine: QuestionEngine = Depends(get_question_engine)
):
    return await engine.semantic_search.recommend_questions(topic)
