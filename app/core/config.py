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

    # Quota settings
    MAX_CONCURRENT_JOBS_PER_USER: int = Field(default=3, env="MAX_CONCURRENT_JOBS_PER_USER")
    MAX_JOBS_PER_USER_PER_DAY: int = Field(default=50, env="MAX_JOBS_PER_USER_PER_DAY")
    MAX_STORAGE_MB_PER_USER: int = Field(default=1024, env="MAX_STORAGE_MB_PER_USER")  # 1GB

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

# Validate configuration on startup
def validate_config():
    """Validate configuration and provide helpful error messages"""
    errors = []

    # Check boolean values
    if not isinstance(settings.DEBUG, bool):
        errors.append(f"DEBUG must be 'true' or 'false', got: {settings.DEBUG}")

    # Check LLM configuration
    if settings.USE_LOCAL_LLM:
        if not settings.OLLAMA_URL:
            errors.append("OLLAMA_URL is required when USE_LOCAL_LLM=true")
        if not settings.OLLAMA_MODEL:
            errors.append("OLLAMA_MODEL is required when USE_LOCAL_LLM=true")
    else:
        if not settings.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when USE_LOCAL_LLM=false")

    # Check rate limiting
    if settings.RATE_LIMIT_PER_MINUTE <= 0:
        errors.append("RATE_LIMIT_PER_MINUTE must be greater than 0")
    if settings.RATE_LIMIT_PER_HOUR <= 0:
        errors.append("RATE_LIMIT_PER_HOUR must be greater than 0")

    # Check timeouts
    if settings.REMOTION_TIMEOUT <= 0:
        errors.append("REMOTION_TIMEOUT must be greater than 0")

    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        error_msg += "\n\nPlease check your .env file and compare with .env.example"
        raise ValueError(error_msg)

# Validate on import
validate_config()

settings = Settings()
