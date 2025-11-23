from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoGenerationResponse(BaseModel):
    job_id: str
    status: JobStatus
    video_url: Optional[str] = None
    progress: float = 0.0
    estimated_time_remaining: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    estimated_time_remaining: Optional[float] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
