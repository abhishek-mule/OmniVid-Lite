"""Configuration settings for OmniVid Lite."""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    APP_NAME: str = "OmniVid Lite"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./omnivid_lite.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Video generation settings
    MAX_VIDEO_DURATION: int = 300  # 5 minutes in seconds
    SUPPORTED_VIDEO_FORMATS: list[str] = ["mp4", "webm", "mov"]

    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"

    # Code generation settings
    GENERATED_SCENE_DIR: Path = Path("remotion_engine/src/generated")
    DEFAULT_WIDTH: int = 1920
    DEFAULT_HEIGHT: int = 1080
    DEFAULT_FPS: int = 30
    DEFAULT_DURATION: int = 5

    # Rendering settings
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "remotion_engine" / "outputs"
    REMOTION_DIR: Path = BASE_DIR / "remotion_engine"
    REMOTION_SCRIPT: Path = REMOTION_DIR / "scripts" / "render.js"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
