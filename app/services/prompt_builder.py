import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

class PromptBuilderService:
    @staticmethod
    def _read_prompt(filename: str) -> str:
        filepath = PROMPTS_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Prompt file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def build_interviewer_prompt(exam: str, candidate_name: str, subject: str, difficulty: str, stage: str, language: str) -> str:
        template = PromptBuilderService._read_prompt("interviewer.txt")
        return template.format(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=stage,
            language=language
        )

    @staticmethod
    def build_followup_prompt(exam: str, candidate_name: str, subject: str, difficulty: str, stage: str, language: str, memory: dict, conversation_history: list) -> str:
        template = PromptBuilderService._read_prompt("followup.txt")
        
        memory_str = "\n".join([f"{k}: {v}" for k, v in memory.items()]) if memory else "No specific memory extracted yet."
        
        # Format conversation history
        history_str = ""
        for turn in reversed(conversation_history):
            history_str += f"{turn['role'].capitalize()}: {turn['content']}\n"
            
        return template.format(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=stage,
            language=language,
            profile=memory_str,
            conversation_history=history_str.strip()
        )

    @staticmethod
    def build_memory_extraction_prompt(current_memory: dict, last_question: str, last_answer: str) -> str:
        template = PromptBuilderService._read_prompt("memory_extraction.txt")
        memory_str = "\n".join([f"{k}: {v}" for k, v in current_memory.items()]) if current_memory else "Empty"
        
        return template.format(
            current_memory=memory_str,
            last_question=last_question,
            last_answer=last_answer
        )

    @staticmethod
    def build_unified_chat_messages(exam: str, subject: str, language: str, experience_level: str, conversation_history: list, candidate_message: str, is_technical: bool, decision_metadata: dict = None, enriched_knowledge: dict = None, candidate_summary: dict = None) -> list:
        from app.services.behaviour_engine import BehaviourEngineService
        
        # Determine if candidate is struggling based on Decision Engine output
        is_struggling = False
        if decision_metadata:
            is_struggling = decision_metadata.get("action") == "next_question" and decision_metadata.get("reason") == "low_score"
            
        # We can extract current stage from history or default to general
        current_stage = "UNKNOWN"
        if conversation_history:
            last_turn = conversation_history[-1]
            if last_turn.get("stage"):
                current_stage = last_turn.get("stage")
                
        behaviour_policy = BehaviourEngineService.get_behaviour_guidelines(
            stage=current_stage,
            is_struggling=is_struggling
        )
        
        knowledge_block = ""
        if enriched_knowledge:
            knowledge_block = f"""
KNOWLEDGE ENGINE (MUST USE THIS FOR GENERATION):
Question/Topic: {enriched_knowledge.get('question', '')}
Keywords: {', '.join(enriched_knowledge.get('keywords', []))}
Expected Concepts: {', '.join(enriched_knowledge.get('expected_concepts', []))}
Follow-up Areas: {', '.join(enriched_knowledge.get('followup_topics', []))}
Difficulty: {enriched_knowledge.get('difficulty', '')}
Bloom's Taxonomy: {enriched_knowledge.get('blooms', '')}
Government Perspective: {enriched_knowledge.get('government_perspective', '')}

Rules for Knowledge Usage:
- NEVER invent new concepts outside of the provided Expected Concepts and Follow-up Areas.
- Use the Government Perspective to frame your tone or responses.
"""

        summary_block = ""
        if candidate_summary:
            summary_block = f"""
CANDIDATE SUMMARY (LIVE ADAPTIVE PROFILE):
Strengths: {', '.join(candidate_summary.get('overall_strengths', []))}
Weaknesses: {', '.join(candidate_summary.get('overall_weaknesses', []))}
Behavior: {', '.join(candidate_summary.get('behavior_flags', []))}
Communication: {candidate_summary.get('communication_level', 'Unknown')}
Subject Readiness: {candidate_summary.get('subject_readiness', 'Unknown')}
Adapt your tone based on the behavior and readiness level.
"""
        
        system_prompt = f"""You are a formal Government Exam Interview panel member. Be professional and respectful.
Conduct interviews exactly like a human interviewer on an official panel.

{behaviour_policy}

{summary_block}

{knowledge_block}

Exam Details:
- Exam: {exam}, Subject: {subject}, Language: {language}, Experience: {experience_level}.
- For "stage", strictly use the EXACT current stage: {current_stage}. Do not output any other stage.

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

        messages = [{"role": "system", "content": system_prompt}]
        
        # Truncate conversation history to last 6 turns (to save token processing time)
        recent_history = conversation_history[-6:] if conversation_history else []
        for turn in recent_history:
            if "role" in turn and "content" in turn:
                # Map roles correctly for LLM APIs
                role = "user" if turn["role"] == "candidate" else ("assistant" if turn["role"] in ["assistant", "interviewer"] else "user")
                messages.append({"role": role, "content": turn["content"]})
                
        # Append latest candidate message if it exists (might be empty on first load)
        if candidate_message and candidate_message.strip():
            messages.append({"role": "user", "content": candidate_message})
            
        if decision_metadata:
            action = decision_metadata.get("action")
            keywords = decision_metadata.get("keywords", [])
            k_str = ", ".join(keywords) if keywords else "the candidate's answer"
            
            if action == "deeper_followup":
                instruction = f"SYSTEM INSTRUCTION (HIDDEN): The Decision Engine has selected ACTION: deeper_followup. You MUST ask exactly ONE deeper conceptual follow-up based on the keyword(s): {k_str}. Focus strictly on the 'Follow-up Areas' provided by the Knowledge Engine. Do NOT move to another question. Set 'asked_follow_up' to true."
            elif action == "clarification_followup":
                instruction = f"SYSTEM INSTRUCTION (HIDDEN): The Decision Engine has selected ACTION: clarification_followup. You MUST ask exactly ONE clarification question about {k_str}. Focus strictly on the 'Expected Concepts' provided by the Knowledge Engine. Do NOT move to another question. Set 'asked_follow_up' to true."
            else:
                instruction = "SYSTEM INSTRUCTION (HIDDEN): The Decision Engine has selected ACTION: next_question. Politely end the topic without embarrassing the candidate. Do NOT ask a follow-up. You MUST ask the exact question provided in the Knowledge Engine: '{0}'. Set 'asked_follow_up' to false.".format(enriched_knowledge.get('question', '')) if enriched_knowledge else "SYSTEM INSTRUCTION (HIDDEN): The Decision Engine has selected ACTION: next_question. Politely end the topic without embarrassing the candidate. Do NOT ask a follow-up. We will move to the next question. Set 'asked_follow_up' to false."
                
            messages.append({"role": "user", "content": instruction})
            
        return messages
