import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "The Lenny Growth Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database: Supports PostgreSQL (Supabase, Railway, Docker) or SQLite fallback
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data/lenny_assistant.db"
    )

    # Local LLM (Ollama) configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_LOCAL_MODEL: str = os.getenv("DEFAULT_LOCAL_MODEL", "qwen2.5:0.5b")
    FALLBACK_LOCAL_MODEL: str = os.getenv("FALLBACK_LOCAL_MODEL", "qwen2.5:0.5b")

    # Cloud LLM configurations
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    DEFAULT_ANTHROPIC_MODEL: str = os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    DEFAULT_OPENAI_MODEL: str = os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4o")

    # Free Cloud Providers (Google AI Studio & Groq)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    DEFAULT_GEMINI_MODEL: str = os.getenv("DEFAULT_GEMINI_MODEL", "gemini-2.5-flash")

    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", None)
    DEFAULT_GROQ_MODEL: str = os.getenv("DEFAULT_GROQ_MODEL", "openai/gpt-oss-120b")

    # Data paths
    TRANSCRIPTS_PATH: str = os.getenv("TRANSCRIPTS_PATH", "data/transcripts")
    INDEX_CACHE_PATH: str = os.getenv("INDEX_CACHE_PATH", "data/index_cache")

    # Server configs
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
