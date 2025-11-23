"""Request schemas for video generation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class VideoGenerationRequest(BaseModel):
    """Schema for video generation request."""
    prompt: str = Field(..., description="Natural language description of the video to generate")
    duration: Optional[float] = Field(
        None,
        description="Desired duration of the video in seconds",
        gt=0,
        le=300  # Max 5 minutes
    )
    resolution: Optional[str] = Field(
        "1920x1080",
        regex=r'^\d+x\d+$',
        description="Output resolution in WxH format (e.g., 1920x1080)"
    )
    format: str = Field(
        "mp4",
        regex='^(mp4|webm|mov)$',
        description="Output video format"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for the video generation"
    )

    class Config:
        schema_extra = {
            "example": {
                "prompt": "A serene beach at sunset with gentle waves",
                "duration": 10.0,
                "resolution": "1920x1080",
                "format": "mp4",
                "metadata": {
                    "style": "cinematic",
                    "mood": "peaceful"
                }
            }
        }
