import uuid
from app.core.database import get_db
from app.schemas.live_interview import LiveInterviewSessionDB, ConversationTurn, CandidateProfile, InterviewMetrics, TimingMetadata
from app.services.session_manager import SessionManagerService
from app.services.candidate_profile_service import CandidateProfileService
from app.services.live_question_generator import LiveQuestionGeneratorService
from app.services.interview_stage_manager import InterviewStageManager
from app.services.difficulty_service import DifficultyService

class InterviewEngineService:
    @staticmethod
    async def start_session(candidate_name: str, candidate_email: str | None, exam: str, subject: str, language: str, difficulty: str, interview_mode: str, duration: int) -> dict:
        session_id = str(uuid.uuid4())
        initial_stage = InterviewStageManager.get_initial_stage()
        
        # 1. Generate First Question
        first_question = await LiveQuestionGeneratorService.generate_first_question(
            exam=exam,
            candidate_name=candidate_name,
            subject=subject,
            difficulty=difficulty,
            stage=initial_stage,
            language=language
        )
        
        # 2. Create Session DB Object
        turn = ConversationTurn(
            role="interviewer", 
            content=first_question,
            stage=initial_stage,
            topic="Introduction",
            difficulty=difficulty
        )
        session_db = LiveInterviewSessionDB(
            session_id=session_id,
            candidate_name=candidate_name,
            exam=exam,
            subject=subject,
            language=language,
            current_difficulty=difficulty,
            interview_mode=interview_mode,
            duration=duration,
            current_stage=initial_stage,
            profile=CandidateProfile(name=candidate_name, target_exam=exam, subject=subject),
            metrics=InterviewMetrics(),
            conversation=[turn]
        )
        
        # 3. Save to DB
        await SessionManagerService.create_session(session_db)
        
        stages_array = [
            {"name": stage, "status": "active" if stage == initial_stage else "pending"}
            for stage in InterviewStageManager.STAGES
        ]
        
        return {
            "session_id": session_id,
            "status": "active",
            "first_question": first_question,
            "current_stage": initial_stage,
            "candidate": {
                "name": candidate_name, 
                "email": candidate_email or "",
                "exam": exam, 
                "subject": subject, 
                "language": language,
                "mode": interview_mode,
                "difficulty": difficulty,
                "duration": duration
            },
            "stages": stages_array
        }

    @staticmethod
    async def _generate_core_intelligence(
        interview_id: str, 
        exam: str, 
        subject: str, 
        language: str, 
        experience_level: str, 
        conversation_history: list, 
        candidate_message: str,
        decision_metadata: dict = None,
        candidate_summary: dict = None
    ) -> dict:
        from app.services.prompt_builder import PromptBuilderService
        from app.services.question_selector_service import QuestionSelectorService
        from app.services.knowledge_engine import KnowledgeEngineService
        
        is_technical = await QuestionSelectorService.is_initialized(interview_id)
        
        # Determine the current stage (from history or default)
        current_stage = "UNKNOWN"
        if conversation_history:
            last_turn = conversation_history[-1]
            if last_turn.get("stage"):
                current_stage = last_turn.get("stage")
                
        # 1. Determine Action
        action = decision_metadata.get("action") if decision_metadata else "next_question"
        asked_follow_up = action in ["deeper_followup", "clarification_followup"]
        
        # 2. Retrieve Question Text
        question_text = ""
        advanced_question = False
        
        if asked_follow_up:
            # Re-enrich the last question asked
            for t in reversed(conversation_history):
                if t.get("role") in ["assistant", "interviewer"]:
                    question_text = t.get("content", "")
                    break
        else:
            # We need a new question if this is a Technical Stage (or Subject Deep Dive etc mapped to QuestionBank)
            if current_stage in ["TECHNICAL", "Subject Fundamentals", "Subject Deep Dive", "Classroom / Practical Scenarios", "Current Affairs", "Behavioural Questions"]:
                if not is_technical:
                    await QuestionSelectorService.initialize_technical_round(interview_id, limit=10)
                    is_technical = True
                
                next_q = await QuestionSelectorService.get_next_question(interview_id)
                if next_q:
                    question_text = next_q
                    advanced_question = True
                    
        # 3. Enrich Knowledge
        enriched_knowledge = KnowledgeEngineService.enrich_question(question_text, subject, current_stage)
        
        # 4. Build Prompts
        messages = PromptBuilderService.build_unified_chat_messages(
            exam=exam,
            subject=subject,
            language=language,
            experience_level=experience_level,
            conversation_history=conversation_history,
            candidate_message=candidate_message,
            is_technical=is_technical,
            decision_metadata=decision_metadata,
            enriched_knowledge=enriched_knowledge,
            candidate_summary=candidate_summary
        )
        
        # 5. Generate Response
        import json
        print("====== PROMPT ======")
        print(json.dumps(messages, indent=2))
        print("====================")
        raw_json = await LiveQuestionGeneratorService.generate_json_response(messages)
        
        # Sync follow-up flag
        raw_json["asked_follow_up"] = asked_follow_up
        
        # Advance the DB index only if we actually generated the response successfully
        if advanced_question:
            await QuestionSelectorService.advance_question(interview_id)
            
        return raw_json

    @staticmethod
    async def process_chat_answer(
        interview_id: str,
        candidate_message: str,
        exam: str,
        subject: str,
        language: str,
        experience_level: str,
        conversation_history: list
    ) -> dict:
        from app.services.decision_engine import DecisionEngineService
        
        last_question = ""
        for t in reversed(conversation_history):
            if t.get("role") == "assistant" or t.get("role") == "interviewer":
                last_question = t.get("content", "")
                break
                
        # Perform stateless evaluation for Chat Endpoint
        from app.schemas.live_interview import CandidateProfile, InterviewMetrics
        from app.services.candidate_profile_service import CandidateProfileService
        
        empty_profile = CandidateProfile(name="Candidate", target_exam=exam, subject=subject)
        empty_metrics = InterviewMetrics()
        
        evaluation = await CandidateProfileService.evaluate_answer_and_update_profile(
            exam=exam,
            current_profile=empty_profile,
            current_metrics=empty_metrics,
            stage="UNKNOWN",
            difficulty=experience_level,
            last_question=last_question,
            last_answer=candidate_message
        )
        
        # Build Candidate Summary
        from app.services.candidate_intelligence import CandidateIntelligenceService
        candidate_summary = CandidateIntelligenceService.build_candidate_summary(
            conversation=conversation_history,
            profile=empty_profile.model_dump(),
            metrics=empty_metrics.model_dump()
        )
        
        decision_metadata = DecisionEngineService.decide_next_action(evaluation, candidate_summary)
        
        # Generate intelligent response
        raw_json = await InterviewEngineService._generate_core_intelligence(
            interview_id=interview_id,
            exam=exam,
            subject=subject,
            language=language,
            experience_level=experience_level,
            conversation_history=conversation_history,
            candidate_message=candidate_message,
            decision_metadata=decision_metadata,
            candidate_summary=candidate_summary
        )
        
        # Save to MongoDB
        import datetime
        db = get_db()
        
        if candidate_message and candidate_message.strip():
            await db["live_interview_chat_history"].insert_one({
                "interview_id": interview_id,
                "role": "candidate",
                "content": candidate_message,
                "language": language,
                "timestamp": datetime.datetime.utcnow()
            })
            
        await db["live_interview_chat_history"].insert_one({
            "interview_id": interview_id,
            "role": "interviewer",
            "content": raw_json.get("interviewer_message", ""),
            "stage": raw_json.get("stage", "UNKNOWN"),
            "next_action": raw_json.get("next_action", "WAIT_FOR_RESPONSE"),
            "avatar": raw_json.get("avatar", {}),
            "keywords": raw_json.get("keywords", []),
            "asked_follow_up": raw_json.get("asked_follow_up", False),
            "language": language,
            "timestamp": datetime.datetime.utcnow()
        })
        import json
        with open("raw_json_dump.txt", "a") as f:
            f.write(json.dumps(raw_json) + "\n")
            
        import logging
        logging.warning(f"DEBUG: raw_json stage is '{raw_json.get('stage')}'")
        if raw_json.get("stage") == "Closing":
            logging.warning(f"DEBUG: Entering Final Report Generation for {interview_id}")
            from app.services.final_report_engine import FinalReportEngine
            report = await FinalReportEngine.generate_final_report(
                interview_id=interview_id,
                exam=exam,
                subject=subject,
                experience_level=experience_level,
                conversation_history=conversation_history,
                candidate_summary=candidate_summary
            )
            logging.warning(f"DEBUG: Report generated for {interview_id}: {report}")
            await db["live_interview_reports"].update_one(
                {"interview_id": interview_id},
                {"$set": {"report": report, "timestamp": datetime.datetime.utcnow()}},
                upsert=True
            )
            logging.warning(f"DEBUG: Report saved to DB for {interview_id}")
            
        return raw_json

    @staticmethod
    async def process_answer(session_id: str, answer_text: str, timing: TimingMetadata = None) -> dict:
        # 1. Fetch Session
        session = await SessionManagerService.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
            
        current_stage = session["current_stage"]
        current_difficulty = session["current_difficulty"]
            
        # 2. Store Candidate Answer
        candidate_turn = ConversationTurn(
            role="candidate", 
            content=answer_text,
            stage=current_stage,
            difficulty=current_difficulty,
            timing=timing
        )
        await SessionManagerService.append_conversation_turn(session_id, candidate_turn)
        session["conversation"].append(candidate_turn.model_dump())
        
        # 3. Extract Memory / Evaluate Answer
        last_question = ""
        for t in reversed(session["conversation"]):
            if t["role"] == "interviewer":
                last_question = t["content"]
                break
                
        current_profile = CandidateProfile(**session.get("profile", {}))
        current_metrics = InterviewMetrics(**session.get("metrics", {}))
        
        evaluation = await CandidateProfileService.evaluate_answer_and_update_profile(
            exam=session["exam"],
            current_profile=current_profile,
            current_metrics=current_metrics,
            stage=current_stage,
            difficulty=current_difficulty,
            last_question=last_question,
            last_answer=answer_text
        )
        
        new_profile = evaluation.get("profile", current_profile.model_dump())
        new_metrics = evaluation.get("metrics", current_metrics.model_dump())
        struggled = evaluation.get("struggled", False)
        
        await SessionManagerService.update_profile_and_metrics(session_id, new_profile, new_metrics)
        session["profile"] = new_profile
        session["metrics"] = new_metrics
        
        # Build Candidate Summary
        from app.services.candidate_intelligence import CandidateIntelligenceService
        candidate_summary = CandidateIntelligenceService.build_candidate_summary(
            conversation=session["conversation"],
            profile=new_profile,
            metrics=new_metrics
        )
        
        # 4. Determine Next Stage and Difficulty
        from app.services.interview_stage_manager import InterviewStageManager
        
        # Calculate current score for adaptive logic
        metrics_dict = new_metrics if isinstance(new_metrics, dict) else new_metrics.dict()
        if metrics_dict:
            current_score = sum(metrics_dict.values()) / max(len(metrics_dict.values()), 1)
        else:
            current_score = 7.0
            
        next_stage = InterviewStageManager.determine_next_stage(
            current_stage=current_stage, 
            conversation=session["conversation"], 
            current_score=current_score,
            candidate_summary=candidate_summary
        )
        
        next_difficulty = DifficultyService.adjust_difficulty(current_difficulty, candidate_summary)
        
        if next_stage != current_stage or next_difficulty != current_difficulty:
            await SessionManagerService.update_stage_and_difficulty(session_id, next_stage, next_difficulty)
            session["current_stage"] = next_stage
            session["current_difficulty"] = next_difficulty

        # 4.5 Check for Completion
        if next_stage == "Closing" and sum(1 for t in session["conversation"] if t["role"] == "interviewer" and t.get("stage") == "Closing") >= 1:
            completion_msg = "Thank you for attending this AI interview. Your interview has been completed successfully. We are now preparing your detailed performance report."
            interviewer_turn = ConversationTurn(
                role="interviewer", 
                content=completion_msg,
                stage="Closing",
                topic="Conclusion",
                difficulty=session["current_difficulty"]
            )
            await SessionManagerService.append_conversation_turn(session_id, interviewer_turn)
            from app.services.final_report_engine import FinalReportEngine
            
            # Generate the final report synchronously
            report = await FinalReportEngine.generate_final_report(
                interview_id=session_id,
                exam=session["exam"],
                subject=session["subject"],
                experience_level=session["current_difficulty"],
                conversation_history=session["conversation"],
                candidate_summary=candidate_summary
            )
            
            db = get_db()
            await db["live_interview_sessions"].update_one(
                {"session_id": session_id},
                {"$set": {
                    "status": "completed",
                    "final_report": report
                }}
            )

            return {
                "session_id": session_id,
                "status": "completed",
                "next_question": completion_msg,
                "current_stage": "Closing",
                "current_difficulty": session["current_difficulty"],
                "candidate_profile": CandidateProfile(**session["profile"]),
                "metrics": InterviewMetrics(**session["metrics"]),
                "conversation_length": len(session["conversation"]) // 2 + 1,
                "avatar": {},
                "keywords": []
            }
            
        # 5. Generate Follow-up Question using Unified Intelligence
        history_for_llm = []
        for turn in session["conversation"]:
            history_for_llm.append({
                "role": "user" if turn["role"] == "candidate" else "assistant",
                "content": turn["content"]
            })
            
        from app.services.decision_engine import DecisionEngineService
        decision_metadata = DecisionEngineService.decide_next_action(evaluation)
            
        raw_json = await InterviewEngineService._generate_core_intelligence(
            interview_id=session_id,
            exam=session["exam"],
            subject=session["subject"],
            language=session["language"],
            experience_level=session["current_difficulty"],
            conversation_history=history_for_llm,
            candidate_message="", # The latest message is already in history_for_llm
            decision_metadata=decision_metadata,
            candidate_summary=candidate_summary
        )
        
        next_question_text = raw_json.get("interviewer_message", "")
        next_topic = "Follow-up" if raw_json.get("asked_follow_up") else "General"
        
        # 6. Store AI Question
        interviewer_turn = ConversationTurn(
            role="interviewer", 
            content=next_question_text,
            stage=raw_json.get("stage", session["current_stage"]),
            topic=next_topic,
            difficulty=session["current_difficulty"],
            follow_up_reason=""
        )
        await SessionManagerService.append_conversation_turn(session_id, interviewer_turn)
        
        return {
            "session_id": session_id,
            "next_question": next_question_text,
            "current_stage": raw_json.get("stage", session["current_stage"]),
            "current_difficulty": session["current_difficulty"],
            "candidate_profile": CandidateProfile(**session["profile"]),
            "metrics": InterviewMetrics(**session["metrics"]),
            "conversation_length": len(session["conversation"]) // 2 + 1,
            "avatar": raw_json.get("avatar", {}),
            "keywords": raw_json.get("keywords", [])
        }
