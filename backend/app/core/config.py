"""
backend/app/core/config.py

All configuration loaded from environment variables.
Never hardcode secrets — they all live in .env
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    VERSION: str = "0.1.0"

    # Anthropic — swap this in when you get credits
    ANTHROPIC_API_KEY: str = ""

    # Groq — used for scenario generation (free at console.groq.com)
    GROQ_API_KEY: str = ""

    # Database — used in Week 2 when we persist results
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agenteval"

    # Redis — used in Week 2 for the job queue
    REDIS_URL: str = "redis://localhost:6379"

    # CORS — allow the Next.js dashboard and local dev
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # How long (seconds) to wait for an agent response per step
    DEFAULT_AGENT_TIMEOUT: int = 30

    # Maximum steps we will ever allow regardless of what the test config says
    HARD_MAX_STEPS: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()