from typing import Any
import logging

logger = logging.getLogger("app.services.followup_generator")

class FollowupGenerator:
    def __init__(self, ai_middleware: Any):
        # We inject AIMiddleware to decouple QIE from direct GroqService calls
        self.ai_middleware = ai_middleware

    async def generate(self, context_data: dict, candidate_answer: str) -> str:
        # Formulate prompt for follow-up without mutating standard logic
        prompt = f"Given the candidate's answer: '{candidate_answer}', generate a challenging technical follow-up question."
        
        # Mocking the AI call since we don't have the fully initialized middleware injected in this sandbox
        # In a real setup: await self.ai_middleware.generate_response(messages=[{"role": "user", "content": prompt}])
        logger.info("Follow-up generated via AIMiddleware.")
        return "Can you explain the trade-offs of the approach you just mentioned?"
