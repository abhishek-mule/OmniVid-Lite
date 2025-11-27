"""Configuration settings for OmniVid Lite."""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "OmniVid Lite"
    DEBUG: str = "false"
    API_V1_STR: str = "/api/v1"

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    REMOTION_DIR: Path = BASE_DIR / "remotion_engine"
    OUTPUT_DIR: Path = REMOTION_DIR / "outputs"

    # LLM selection
    USE_LOCAL_LLM: bool = Field(default=True, env="USE_LOCAL_LLM")
    OLLAMA_URL: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    OLLAMA_MODEL: str = Field(default="deepseek-r1:7b", env="OLLAMA_MODEL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")

    REMOTION_CMD: str = Field(default="npx remotion", env="REMOTION_CMD")
    REDIS_DSN: str = Field(default="redis://localhost:6379", env="REDIS_DSN")
    REMOTION_TIMEOUT: int = Field(default=300, env="REMOTION_TIMEOUT")  # 5 minutes

    # Authentication settings
    REQUIRE_API_KEY: bool = Field(default=False, env="REQUIRE_API_KEY")
    API_KEY_HEADER: str = Field(default="X-API-Key", env="API_KEY_HEADER")

    # Rate limiting settings
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")

    # CORS settings
    ALLOWED_ORIGINS: list[str] = Field(default=["http://localhost:3000", "http://localhost:8000"], env="ALLOWED_ORIGINS")

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOGS_DIR: str = Field(default="logs", env="LOGS_DIR")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
