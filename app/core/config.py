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

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
