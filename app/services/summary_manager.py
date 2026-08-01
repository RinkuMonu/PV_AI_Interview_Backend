import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.schemas.conversation_summary import ConversationSummary
from app.schemas.ai_request_context import AIRequestContext
from app.core.database import get_db

logger = logging.getLogger("app.services.summary_manager")

class SummaryManager:
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db if self._db is not None else get_db()
        
    @property
    def collection(self):
        return self.db["conversation_summaries"]

    def should_summarize(self, context: AIRequestContext, total_turns: int = 0) -> bool:
        """
        Trigger summary if removed_history exists OR conversation exceeds trigger turns.
        Ready for future BudgetManager triggers.
        """
        if context.removed_history and len(context.removed_history) > 0:
            return True
            
        if total_turns > getattr(settings, "SUMMARY_TRIGGER_TURNS", 5):
            return True
            
        return False

    async def get_latest_summary(self, interview_id: str) -> Optional[ConversationSummary]:
        if not interview_id:
            return None
        doc = await self.collection.find_one(
            {"interview_id": interview_id},
            sort=[("summary_version", -1)]
        )
        if doc:
            return ConversationSummary(**doc)
        return None

    async def create_summary(self, summary_data: ConversationSummary) -> ConversationSummary:
        doc = summary_data.model_dump()
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
        await self.collection.insert_one(doc)
        return summary_data

    async def update_summary(self, summary_data: ConversationSummary) -> ConversationSummary:
        summary_data.summary_version += 1
        summary_data.updated_at = datetime.utcnow()
        doc = summary_data.model_dump()
        
        await self.collection.update_one(
            {"interview_id": summary_data.interview_id, "summary_version": summary_data.summary_version - 1},
            {"$set": doc},
            upsert=True
        )
        return summary_data

    def prepare_summary_request(self, latest_summary: Optional[ConversationSummary], removed_history: List[Dict[str, Any]]) -> dict:
        """
        Prepares the LLM request to generate a summary incrementally.
        Does NOT execute the request.
        """
        system_prompt = (
            "You are an AI Interview Summary Manager.\n"
            "Your task is to summarize the provided conversation history into a structured JSON format.\n"
            f"Maximum summary length for the summary_text field is {getattr(settings, 'SUMMARY_MAX_WORDS', 150)} words.\n\n"
            "You MUST preserve:\n"
            "- Candidate strengths\n"
            "- Candidate weaknesses\n"
            "- Topics already covered\n"
            "- Important mistakes\n"
            "- Interview stage\n"
            "- Evaluation notes\n"
            "- Confidence level\n\n"
            "Do NOT include unnecessary conversation or pleasantries.\n"
            "Respond ONLY with valid JSON matching this schema:\n"
            "{\n"
            '  "summary_text": "...",\n'
            '  "candidate_strengths": "...",\n'
            '  "candidate_weaknesses": "...",\n'
            '  "covered_topics": "...",\n'
            '  "pending_topics": "...",\n'
            '  "interview_stage": "...",\n'
            '  "evaluation_notes": "...",\n'
            '  "confidence_score": 85\n'
            "}"
        )

        user_content = "Please summarize the following interview history.\n\n"
        
        if latest_summary:
            user_content += f"PREVIOUS SUMMARY:\n{latest_summary.summary_text}\n\n"
            user_content += f"PREVIOUS STRENGTHS:\n{latest_summary.candidate_strengths}\n\n"
            user_content += f"PREVIOUS WEAKNESSES:\n{latest_summary.candidate_weaknesses}\n\n"
            
        user_content += "NEW CONVERSATION TO MERGE:\n"
        for msg in removed_history:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            user_content += f"{role}: {content}\n\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        return {
            "model": "llama-3.3-70b-versatile", # or whatever default is required
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }

    def process_summary_response(self, context: AIRequestContext, response_text: str, latest_summary: Optional[ConversationSummary], turns_added: int) -> ConversationSummary:
        """
        Parses the JSON response from Groq and constructs the updated ConversationSummary.
        """
        try:
            data = json.loads(response_text)
        except Exception as e:
            logger.error(f"Failed to parse summary JSON: {e}")
            data = {"summary_text": "Failed to parse summary."}

        new_version = (latest_summary.summary_version + 1) if latest_summary else 1
        total_turns = (latest_summary.summarized_turns + turns_added) if latest_summary else turns_added

        summary = ConversationSummary(
            interview_id=context.interview_id or "unknown",
            session_id=context.session_id,
            candidate_id=context.candidate_id,
            subject=context.subject,
            interview_stage=context.interview_stage,
            summary_version=new_version,
            summary_text=data.get("summary_text", ""),
            candidate_strengths=data.get("candidate_strengths"),
            candidate_weaknesses=data.get("candidate_weaknesses"),
            covered_topics=data.get("covered_topics"),
            pending_topics=data.get("pending_topics"),
            evaluation_notes=data.get("evaluation_notes"),
            confidence_score=data.get("confidence_score"),
            summarized_turns=total_turns
        )
        return summary
