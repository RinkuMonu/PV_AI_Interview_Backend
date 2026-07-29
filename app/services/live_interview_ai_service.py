import json
import logging
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger("live_interview_ai")

class LiveInterviewAIService:
    @staticmethod
    async def generate_question(exam: str, subject: str, difficulty: str, language: str) -> str:
        """
        Generates a single live interview question using GPT-4o-mini (GPT-5 mini mapping).
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")
            
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = """You are an experienced interviewer.
Generate only ONE interview question.

Rules:
- Ask only one question.
- Do not generate answers.
- Do not explain.
- Do not number the question.
- Difficulty must match the requested level.
- Language must match the requested language.
- Make the question suitable for a real interview.

Interview Language:
{language}

Rules for Language:
If language is Hindi:
- Speak only Hindi.
- Use natural spoken Hindi.
- Avoid unnecessary English words.
- Do not translate literally.
- Speak like a real Indian interviewer.

If language is English:
- Use fluent English.
- Make the question suitable for a real interview.
"""
        
        user_prompt = f"""Exam:
{exam}

Subject:
{subject}

Difficulty:
{difficulty}

Language:
{language}

Return JSON:
{{
   "question":"..."
}}"""
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Mapping to GPT-5 mini spec request
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            result_content = response.choices[0].message.content
            data = json.loads(result_content)
            
            question = data.get("question")
            if not question:
                raise ValueError("AI did not return a valid question field in JSON.")
                
            return question
            
        except Exception as e:
            logger.exception(f"Error generating live interview question: {e}")
            raise RuntimeError(f"Failed to generate question: {str(e)}")

    @staticmethod
    async def generate_chat_response(
        interview_id: str,
        candidate_message: str,
        exam: str,
        subject: str,
        language: str,
        experience_level: str,
        conversation_history: list
    ) -> dict:
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("API Key is not configured (Provide GROQ_API_KEY or OPENAI_API_KEY)")
            
        base_url = "https://api.groq.com/openai/v1" if settings.GROQ_API_KEY else None
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        model_name = "llama-3.3-70b-versatile" if settings.GROQ_API_KEY else "gpt-4o-mini"
        
        system_prompt = f"""You are a formal Government Exam Interview panel member. Be professional and respectful.
Conduct interviews exactly like a human interviewer on an official panel.

Rules:
- Speak naturally but formally. Use phrases like: Thank you, I understand, Please explain further, Let us move to the next question.
- NEVER use casual words like: Awesome, Great, Cool, Nice, Fantastic.
- Keep responses concise (1-3 sentences).
- Ask one question at a time.
- React professionally to answers. If short, ask for explanation; if weak, move on.
- Extract up to 3 important keywords from candidate's answer and return in "keywords". Use these for follow-ups in non-technical stages.
- Never repeat questions. Do not reveal answers.
- Exam: {exam}, Subject: {subject}, Language: {language}, Experience: {experience_level}.
- For "stage", strictly use: GREETING, INTRODUCTION, HR, PROJECT, TECHNICAL, SCENARIO, CLOSING.

Language Rules:
If Hindi: Speak natural spoken Hindi like an Indian interviewer.
If English: Fluent English.

Avatar Values (based on context):
- emotion: neutral, smile, happy, serious, thinking, listening, encouraging, surprised, confident
- animation: idle, greeting, speaking, listening, thinking, nod, agree, closing
- gesture: wave, hand_open, point, none
- head_direction: candidate, notes, away (default to candidate)
- eye_contact: true or false
- posture: professional, relaxed, leaning_forward
- speaking_speed: normal, slow, fast

Examples:
Greeting -> emotion=smile, animation=greeting, gesture=wave
Technical Question -> emotion=serious, animation=speaking, gesture=hand_open
Candidate gives good answer -> emotion=encouraging, animation=nod
Closing -> emotion=smile, animation=closing, gesture=wave

Return EXACTLY valid JSON matching:
{{
   "stage":"INTRODUCTION",
   "interviewer_message":"...",
   "keywords":["BCA", "FastAPI"],
   "asked_follow_up":false,
   "next_action":"WAIT_FOR_RESPONSE",
   "avatar": {{
       "emotion": "smile",
       "animation": "greeting",
       "gesture": "wave",
       "head_direction": "candidate",
       "eye_contact": true,
       "posture": "professional",
       "speaking_speed": "normal"
   }}
}}"""

        # Format conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Truncate conversation history to last 6 turns (to save token processing time)
        recent_history = conversation_history[-6:] if conversation_history else []
        for turn in recent_history:
            if "role" in turn and "content" in turn:
                messages.append({"role": turn["role"], "content": turn["content"]})
                
        # Append latest candidate message if it exists (might be empty on first load)
        if candidate_message and candidate_message.strip():
            messages.append({"role": "user", "content": candidate_message})
            
        from app.services.question_selector_service import QuestionSelectorService
        
        is_technical = await QuestionSelectorService.is_initialized(interview_id)
        if is_technical:
            messages.append({"role": "system", "content": "The candidate just answered a technical question. Evaluate the candidate's answer. If the answer is strong, you may ask exactly ONE contextual follow-up question and set 'asked_follow_up' to true. If the answer is weak, or you have already asked a follow-up for this topic, do NOT ask a follow-up and set 'asked_follow_up' to false."})
            
        try:
            response = await client.chat.completions.create(
                model=model_name,
                response_format={"type": "json_object"},
                messages=messages,
                temperature=0.7
            )
            
            result_content = response.choices[0].message.content
            data = json.loads(result_content)
            
            # Post-process for TECHNICAL stage
            if data.get("stage") == "TECHNICAL":
                if not is_technical:
                    # Initialize it now
                    await QuestionSelectorService.initialize_technical_round(interview_id, limit=5)
                    data["interviewer_message"] = "Let us move to the technical round. "
                
                # Check if GPT asked a follow-up
                asked_follow_up = data.get("asked_follow_up", False)
                
                if not asked_follow_up:
                    next_q = await QuestionSelectorService.get_next_question(interview_id)
                    if next_q:
                        if is_technical:
                            data["interviewer_message"] += f"\n\nHere is your next question: {next_q}"
                        else:
                            data["interviewer_message"] += f"{next_q}"
                        await QuestionSelectorService.advance_question(interview_id)
                    else:
                        data["stage"] = "CLOSING"
                        data["interviewer_message"] += "\n\nThat concludes our technical round. Let us wrap up the interview."
            
            # Save to MongoDB
            from app.core.database import get_db
            import datetime
            db = get_db()
            
            # Save candidate's message if present
            if candidate_message and candidate_message.strip():
                await db["live_interview_chat_history"].insert_one({
                    "interview_id": interview_id,
                    "role": "candidate",
                    "content": candidate_message,
                    "language": language,
                    "timestamp": datetime.datetime.utcnow()
                })
                
            # Save AI's response
            await db["live_interview_chat_history"].insert_one({
                "interview_id": interview_id,
                "role": "interviewer",
                "content": data.get("interviewer_message", ""),
                "stage": data.get("stage", "UNKNOWN"),
                "next_action": data.get("next_action", "WAIT_FOR_RESPONSE"),
                "avatar": data.get("avatar", {}),
                "keywords": data.get("keywords", []),
                "asked_follow_up": data.get("asked_follow_up", False),
                "language": language,
                "timestamp": datetime.datetime.utcnow()
            })
            
            return data
            
        except Exception as e:
            logger.exception(f"Error generating chat response: {e}")
            raise RuntimeError(f"Failed to generate chat response: {str(e)}")
