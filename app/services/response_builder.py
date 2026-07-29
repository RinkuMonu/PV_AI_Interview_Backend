from typing import Optional
from app.schemas.speech import VoiceState, StructuredError
from app.schemas.live_interview import VoiceStateResponse, ProcessingMetrics, CandidateProfile, InterviewMetrics

class ResponseBuilder:
    @staticmethod
    def build_chat_response(raw_json: dict, tts_result: dict = None) -> 'LiveInterviewChatResponse':
        from app.schemas.live_interview import LiveInterviewChatResponse
        tts = tts_result or {}
        return LiveInterviewChatResponse(
            stage=raw_json.get("stage", "UNKNOWN"),
            interviewer_message=raw_json.get("interviewer_message", ""),
            next_action=raw_json.get("next_action", "WAIT_FOR_RESPONSE"),
            avatar=raw_json.get("avatar", {}),
            audio_url=tts.get("audio_url"),
            voice_supported=tts.get("voice_supported"),
            voice=tts.get("voice"),
            language=tts.get("language")
        )

    @staticmethod
    def build_voice_state(
        request_id: str,
        session_id: str,
        transcript: str,
        next_question: str,
        audio_url: str,
        metrics: dict,
        profile: dict,
        voice_state: VoiceState,
        turn: int,
        processing: ProcessingMetrics,
        error: Optional[StructuredError] = None
    ) -> VoiceStateResponse:
        
        return VoiceStateResponse(
            request_id=request_id,
            session_id=session_id,
            transcript=transcript,
            next_question=next_question,
            audio_url=audio_url,
            metrics=InterviewMetrics(**metrics),
            candidate_profile=CandidateProfile(**profile),
            voice_state=voice_state,
            turn=turn,
            processing=processing,
            error=error
        )

    @staticmethod
    def build_error(
        request_id: str,
        session_id: str,
        code: str,
        message: str,
        retry: bool = False
    ) -> VoiceStateResponse:
        return VoiceStateResponse(
            request_id=request_id,
            session_id=session_id,
            transcript="",
            next_question="",
            audio_url="",
            metrics=InterviewMetrics(),
            candidate_profile=CandidateProfile(),
            voice_state=VoiceState.ERROR,
            turn=0,
            processing=ProcessingMetrics(),
            error=StructuredError(code=code, message=message, retry=retry)
        )
