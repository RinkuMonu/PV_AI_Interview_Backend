import logging
import traceback
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.core.database import db_instance
from app.schemas.live_interview import (
    GenerateQuestionRequest, 
    GenerateQuestionResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    LiveInterviewChatRequest,
    LiveInterviewChatResponse,
    LiveInterviewStartRequest,
    LiveInterviewStartResponse
)
from app.services.live_interview_ai_service import LiveInterviewAIService
from app.services.speech_to_text_service import SpeechToTextService
from app.services.interview_evaluation_service import InterviewEvaluationService
from app.services.text_to_speech_service import TextToSpeechService
from app.services.interview_engine import InterviewEngineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live-interview", tags=["Live Interview"])


@router.post("/start", response_model=LiveInterviewStartResponse)
async def start_interview(request: LiveInterviewStartRequest):
    """Start a new live interview session."""
    
    # 6. Validate all request body fields
    if not request.exam or request.exam.lower() == "unknown":
        raise HTTPException(status_code=400, detail={"error": "Bad Request", "message": "Exam field is required and cannot be empty or Unknown."})
    if not request.subject or request.subject.lower() == "unknown":
        raise HTTPException(status_code=400, detail={"error": "Bad Request", "message": "Subject field is required and cannot be empty or Unknown."})
    if not request.candidate_name:
        raise HTTPException(status_code=400, detail={"error": "Bad Request", "message": "Candidate name is required."})

    # 9. Check environment variables (and implicitly OpenAI API calls setup)
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is missing.")
        raise HTTPException(status_code=500, detail={"error": "Configuration Error", "message": "OpenAI API Key is not configured."})
        
    # 7. Check MongoDB connection
    try:
        if db_instance.client is None:
            raise Exception("Database client is not initialized")
        await db_instance.client.admin.command('ping')
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise HTTPException(status_code=500, detail={"error": "Database Connection Error", "message": "Failed to connect to database."})

    try:
        # 1. Create session and generate first question
        session_data = await InterviewEngineService.start_session(
            candidate_name=request.candidate_name,
            candidate_email=request.candidate_email,
            exam=request.exam,
            subject=request.subject,
            language=request.language,
            difficulty=request.difficulty,
            interview_mode=request.interview_mode,
            duration=request.duration
        )

        # 2. Generate TTS audio for the first question
        tts_result = TextToSpeechService.generate_speech(
            session_data["first_question"], request.language
        )
        session_data["audio_url"] = tts_result.get("audio_url")

        return LiveInterviewStartResponse(**session_data)
    except ValueError as e:
        logger.warning(f"Validation error in start_interview: {e}")
        raise HTTPException(status_code=400, detail={"error": "Bad Request", "message": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in start_interview")
        # 4. Print the full traceback
        tb = traceback.format_exc()
        logger.error(f"Full traceback: \n{tb}")
        
        # 5. Return meaningful JSON errors instead of generic HTTP 500
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Internal Server Error", 
                "message": str(e),
                "traceback": tb.splitlines()  # Send as list of strings for readable JSON
            }
        )

@router.post("/generate-question", response_model=GenerateQuestionResponse)
async def generate_question(request: GenerateQuestionRequest):
    try:
        question = await LiveInterviewAIService.generate_question(
            exam=request.exam,
            subject=request.subject,
            difficulty=request.difficulty,
            language=request.language
        )
        
        # Phase 4: Generate Speech for the question
        tts_result = TextToSpeechService.generate_speech(question, request.language)
        
        return GenerateQuestionResponse(
            question=question,
            audio_url=tts_result.get("audio_url"),
            question_number=request.question_number,
            voice_supported=tts_result.get("voice_supported"),
            voice=tts_result.get("voice"),
            language=tts_result.get("language")
        )
    except ValueError as e:
        # Validation or configuration error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Internal server error (e.g. OpenAI failure)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe")
async def transcribe(
    interview_id: str = Form(...),
    question_number: int = Form(...),
    audio: UploadFile = File(...)
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
        
    supported_extensions = [".wav", ".mp3", ".webm"]
    if not any(audio.filename.lower().endswith(ext) for ext in supported_extensions):
        raise HTTPException(status_code=400, detail="Unsupported audio type. Please upload .wav, .mp3, or .webm")
        
    try:
        transcript = await SpeechToTextService.transcribe_audio(
            interview_id=interview_id,
            question_number=question_number,
            audio=audio
        )
        return {
            "success": True,
            "transcript": transcript
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate", response_model=EvaluateAnswerResponse)
async def evaluate_answer(request: EvaluateAnswerRequest):
    try:
        evaluation = await InterviewEvaluationService.evaluate_answer(
            interview_id=request.interview_id,
            question_number=request.question_number,
            question=request.question,
            candidate_answer=request.candidate_answer,
            exam=request.exam,
            subject=request.subject,
            difficulty=request.difficulty,
            language=request.language
        )
        
        # Phase 4: Generate Speech for follow-up question if required
        tts_result = {}
        if evaluation.get("follow_up_required") and evaluation.get("follow_up_question"):
            # Default to english for follow-ups since language is not passed in EvaluateAnswerRequest
            tts_result = TextToSpeechService.generate_speech(evaluation["follow_up_question"], request.language)
            
        evaluation["follow_up_audio_url"] = tts_result.get("audio_url")
        evaluation["voice_supported"] = tts_result.get("voice_supported")
        evaluation["voice"] = tts_result.get("voice")
        evaluation["language"] = tts_result.get("language")
        
        return EvaluateAnswerResponse(**evaluation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=LiveInterviewChatResponse)
async def chat(request: LiveInterviewChatRequest):
    try:
        data = await InterviewEngineService.process_chat_answer(
            interview_id=request.interview_id,
            candidate_message=request.candidate_message,
            exam=request.exam,
            subject=request.subject,
            language=request.language,
            experience_level=request.experience_level,
            conversation_history=request.conversation_history
        )
        
        # Generate TTS audio for the AI's response
        tts_result = {}
        if data.get("interviewer_message"):
            tts_result = TextToSpeechService.generate_speech(data["interviewer_message"], request.language)
            
        from app.services.response_builder import ResponseBuilder
        return ResponseBuilder.build_chat_response(data, tts_result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
