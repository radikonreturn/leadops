from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "LeadOps"
    API_V1_STR: str = "/api"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://leadops:change-me@localhost:5432/leadops",
        description="Database connection URL"
    )

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # AI Configuration
    AI_PROVIDER: str = "openai"  # openai, gemini, anthropic, ollama, mock
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"

    # Lead research / Email defaults
    DEFAULT_EMAIL_STYLE: str = "Professional"
    USER_NAME: str = "Doğukan"
    USER_ROLE: str = "B2B Solutions Consultant"
    DEFAULT_SENDER_NAME: str = "LeadOps Solutions"

    # Web Scraping Security
    SCRAPER_TIMEOUT_SECONDS: int = 12
    SCRAPER_MAX_CONTENT_BYTES: int = 500_000
    SCRAPER_USER_AGENT: str = "LeadOpsBot/1.0 (+https://leadops.app/bot)"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()
