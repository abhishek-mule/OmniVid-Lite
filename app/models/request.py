from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class VideoGenerationRequest(BaseModel):
    prompt: str
    style: Optional[str] = None
    duration: Optional[int] = 30
    resolution: Optional[dict] = {"width": 1920, "height": 1080}
    metadata: Optional[Dict[str, Any]] = None

class JobStatusRequest(BaseModel):
    job_id: str
