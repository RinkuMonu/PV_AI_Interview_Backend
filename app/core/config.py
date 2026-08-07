# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PV AI Interview Backend"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = ["*"]
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_NAME: str = "pv_interview_db"
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    PROMPT_MAX_HISTORY_TURNS: int = 3
    PROMPT_MAX_HISTORY_TOKENS: int = 4000
    SUMMARY_TRIGGER_TURNS: int = 5
    SUMMARY_MAX_WORDS: int = 150
    RECENT_TURNS_TO_KEEP: int = 2
    CACHE_TTL_HOURS: int = 24
    
    # Budget Manager Policy Defaults
    MAX_PROMPT_TOKENS: int = 50000
    MAX_COMPLETION_TOKENS: int = 10000
    MAX_TOTAL_TOKENS: int = 60000
    MAX_INTERVIEW_COST: float = 0.50
    WARNING_THRESHOLD: int = 80
    CRITICAL_THRESHOLD: int = 90
    GRACE_THRESHOLD: int = 100
    STOP_THRESHOLD: int = 110
    
    # Analytics
    ENABLE_ANALYTICS: bool = True
    ENABLE_REPORTS: bool = True
    ENABLE_CSV_EXPORT: bool = True
    ENABLE_EXCEL_EXPORT: bool = True
    ANALYTICS_RETENTION_DAYS: int = 90
    
    # Phase 8 Router Configs
    DEFAULT_PROVIDER: str = "groq"
    DEFAULT_MODEL: str = "llama-3.1-8b-instant"
    ENABLE_ROUTING: bool = True
    ENABLE_FALLBACK: bool = True
    ENABLE_HEALTH_MONITOR: bool = True
    ENABLE_LOAD_BALANCING: bool = True
    DEFAULT_ROUTING_POLICY: str = "balanced"
    MAX_RETRIES: int = 3
    HEALTH_CHECK_INTERVAL: int = 60
    
    # Phase 9 Evaluation Configs
    ENABLE_AI_EVALUATION: bool = True
    ENABLE_COMPETENCY_TRACKING: bool = True
    ENABLE_RECOMMENDATIONS: bool = True
    DEFAULT_RUBRIC: str = "default_rubric"
    PASSING_SCORE: float = 60.0
    CONFIDENCE_THRESHOLD: float = 80.0
    MAX_EVALUATION_RETRIES: int = 3
    
    # Phase 10 Orchestrator & Avatar Configs
    ENABLE_STREAMING: bool = True
    ENABLE_AVATAR: bool = True
    ENABLE_STT: bool = True
    ENABLE_TTS: bool = True
    ENABLE_INTERRUPTION_HANDLING: bool = True
    SESSION_TIMEOUT: int = 3600
    MAX_SILENCE: int = 5000
    HEARTBEAT_INTERVAL: int = 5
    AUTO_RECOVERY: bool = True
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
