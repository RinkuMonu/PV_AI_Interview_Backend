from openai import AsyncOpenAI
from app.core.config import settings
from app.core.voice_config import voice_settings
from app.services.prompt_builder import PromptBuilderService

class LiveQuestionGeneratorService:
    @staticmethod
    async def generate_first_question(exam: str, candidate_name: str, subject: str, difficulty: str, stage: str, language: str) -> str:
        from app.core.config import settings
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY or OPENAI_API_KEY is not configured")
            
        prompt = PromptBuilderService.build_interviewer_prompt(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=stage,
            language=language
        )
        
        base_url = "https://api.groq.com/openai/v1" if settings.GROQ_API_KEY else None
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        model = "llama-3.3-70b-versatile" if settings.GROQ_API_KEY else "gpt-4o-mini"
        
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()

    @staticmethod
    async def generate_json_response(messages: list) -> dict:
        """
        Pure LLM helper. Takes pre-formatted messages array and returns a JSON dictionary.
        Does not know about interview logic or personas.
        """
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY or OPENAI_API_KEY is not configured")
            
        base_url = "https://api.groq.com/openai/v1" if settings.GROQ_API_KEY else None
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        model = "llama-3.3-70b-versatile" if settings.GROQ_API_KEY else "gpt-4o-mini"
        
        try:
            response = await client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=messages,
                temperature=0.7
            )
            
            import json
            result = response.choices[0].message.content.strip()
            return json.loads(result)
        except Exception as e:
            import logging
            logging.error(f"Error generating JSON response from LLM: {e}")
            raise RuntimeError(f"Failed to generate JSON response: {str(e)}")
