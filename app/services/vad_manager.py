from app.schemas.speech import AudioChunk

class VADManager:
    def detect_speech(self, chunk: AudioChunk) -> bool:
        # Mock VAD: Assume audio length > 0 is speech for now
        # In production, use WebRTC VAD or Silero VAD
        return len(chunk.audio_data) > 0
