from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional

class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Job(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    user_id: Optional[str] = None
    prompt: str
    creative: bool = False
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    retries: int = 0
    max_retries: int = 3
    progress: float = 0.0
    output_path: Optional[str] = None
    error: Optional[str] = None
    request_hash: Optional[str] = None