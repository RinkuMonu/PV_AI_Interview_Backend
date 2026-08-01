from app.services.history_repository import HistoryRepository
from app.schemas.interview_question import InterviewQuestion

class DuplicateDetector:
    def __init__(self, history_repo: HistoryRepository):
        self.history_repo = history_repo

    async def is_duplicate(self, interview_id: str, question: InterviewQuestion) -> bool:
        # Check exact ID duplicate
        if await self.history_repo.has_been_asked(interview_id, question.question_id):
            return True
            
        # In a full production setup, this would also run a similarity check 
        # against recent history using SemanticSearch to catch rephrased duplicates.
        return False
