"""ReelIQ Backend — Configuration Module"""
from pydantic_settings import BaseSettings
from functools import lru_cache

DEFAULT_GROQ_API_KEY = "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"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ─── App ───
    APP_NAME: str = "ReelIQ"
    DEBUG: bool = True
    BACKEND_SECRET_KEY: str = "dev-secret-key-change-in-production"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    # ─── Database ───
    DATABASE_URL: str = "sqlite+aiosqlite:///./reeliq.db"
    DATABASE_URL_SYNC: str = "sqlite:///./reeliq.db"

    # ─── Redis ───
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── S3-Compatible Storage ───
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin123"
    S3_BUCKET_VIDEOS: str = "reeliq-videos"
    S3_BUCKET_THUMBNAILS: str = "reeliq-thumbnails"
    S3_PUBLIC_URL: str = "http://localhost:9000"
    LOCAL_STORAGE_DIR: str = "storage"
    LOCAL_STORAGE_PUBLIC_URL: str = "http://localhost:8000/static"

    # ─── AI ───
    GROQ_API_KEY: str = DEFAULT_GROQ_API_KEY
    GROQ_TEXT_MODEL: str = "llama-3.3-70b-specdec"
    GROQ_VISION_MODEL: str = "llama-3.2-11b-vision-preview"

    # ─── Instagram OAuth ───
    INSTAGRAM_APP_ID: str = "1763647945017258"
    INSTAGRAM_APP_SECRET: str = "eb14470b5498e052ad2f5a5dd155cd25"

    # ─── Local TTS ───
    COQUI_TTS_MODEL: str = "tts_models/en/ljspeech/tacotron2-DDC"

    # ─── Auth ───
    NEXTAUTH_SECRET: str = "dev-secret"
    NEXTAUTH_URL: str = "http://localhost:3000"
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
