"""Response schemas for video generation."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .video_request import VideoGenerationRequest

class JobStatus(str, Enum):
    """Status of a video generation job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoGenerationResponse(BaseModel):
    """Schema for video generation response."""
    job_id: str = Field(..., description="Unique identifier for the job")
    status: JobStatus = Field(..., description="Current status of the job")
    request: VideoGenerationRequest = Field(..., description="Original request parameters")
    created_at: datetime = Field(..., description="When the job was created")
    updated_at: Optional[datetime] = Field(None, description="When the job was last updated")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result if completed successfully")
    error: Optional[str] = Field(None, description="Error message if job failed")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "request": {
                    "prompt": "A serene beach at sunset with gentle waves",
                    "duration": 10.0,
                    "resolution": "1920x1080",
                    "format": "mp4"
                },
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }
