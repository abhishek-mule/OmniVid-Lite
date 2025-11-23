"""Job management service for OmniVid Lite."""
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum

class JobStatus(str, Enum):
    """Status of a video generation job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobManager:
    """Manages video generation jobs."""
    
    def __init__(self):
        """Initialize the job manager."""
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def create_job(self, user_id: str, params: Dict[str, Any]) -> str:
        """Create a new video generation job.
        
        Args:
            user_id: ID of the user creating the job
            params: Job parameters
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "user_id": user_id,
            "status": JobStatus.PENDING,
            "params": params,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None,
            "result": None,
            "error": None
        }
        
        async with self._lock:
            self._jobs[job_id] = job
        
        return job_id
    
    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update the status of a job.
        
        Args:
            job_id: ID of the job to update
            status: New status
            result: Job result (if completed successfully)
            error: Error message (if failed)
            
        Returns:
            True if the job was updated, False if not found
        """
        async with self._lock:
            if job_id not in self._jobs:
                return False
                
            self._jobs[job_id]["status"] = status
            self._jobs[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            if result is not None:
                self._jobs[job_id]["result"] = result
            if error is not None:
                self._jobs[job_id]["error"] = error
                
        return True
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID.
        
        Args:
            job_id: ID of the job to retrieve
            
        Returns:
            Job details or None if not found
        """
        async with self._lock:
            return self._jobs.get(job_id)
    
    async def list_user_jobs(self, user_id: str) -> List[Dict[str, Any]]:
        """List all jobs for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of job details
        """
        async with self._lock:
            return [
                job for job in self._jobs.values() 
                if job["user_id"] == user_id
            ]
