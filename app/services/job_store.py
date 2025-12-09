"""
Simple in-memory job store for OmniVid Lite MVP.

Provides basic job state management and progress tracking.
Replaces database dependency for demo purposes.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Job data structure."""
    id: str
    prompt: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    user_id: str = "demo_user"
    creative: bool = False


class InMemoryJobStore:
    """Simple in-memory job storage for MVP."""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, job_id: str, prompt: str, user_id: str = "demo_user", creative: bool = False) -> Job:
        """Create a new job."""
        async with self._lock:
            job = Job(
                id=job_id,
                prompt=prompt,
                user_id=user_id,
                creative=creative,
                status=JobStatus.PENDING
            )
            self.jobs[job_id] = job
            logger.info(f"Created job {job_id} with prompt: {prompt}")
            return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        async with self._lock:
            return self.jobs.get(job_id)

    async def update_job_status(self, job_id: str, status: JobStatus, error: Optional[str] = None) -> bool:
        """Update job status."""
        async with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            job.status = status
            job.error = error
            job.updated_at = datetime.now()

            logger.info(f"Updated job {job_id} status to {status.value}")
            if error:
                logger.error(f"Job {job_id} failed with error: {error}")

            return True

    async def update_job_progress(self, job_id: str, progress: int, output_path: Optional[str] = None) -> bool:
        """Update job progress."""
        async with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            job.progress = min(100, max(0, progress))
            if output_path:
                job.output_path = output_path
            job.updated_at = datetime.now()

            logger.info(f"Updated job {job_id} progress to {progress}%")
            if output_path:
                logger.info(f"Job {job_id} output: {output_path}")

            return True

    async def list_jobs(self, user_id: str, limit: int = 50) -> list[Job]:
        """List jobs for a user."""
        async with self._lock:
            user_jobs = [job for job in self.jobs.values() if job.user_id == user_id]
            # Sort by creation time, most recent first
            user_jobs.sort(key=lambda j: j.created_at, reverse=True)
            return user_jobs[:limit]

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if possible."""
        async with self._lock:
            job = self.jobs.get(job_id)
            if not job or job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return False

            job.status = JobStatus.CANCELLED
            job.updated_at = datetime.now()
            logger.info(f"Cancelled job {job_id}")
            return True

    async def cleanup_old_jobs(self, days_old: int = 7) -> int:
        """Cleanup old completed/failed jobs."""
        cutoff_date = datetime.now()
        async with self._lock:
            to_remove = []
            for job_id, job in self.jobs.items():
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    # Simplified cleanup - just remove old jobs
                    to_remove.append(job_id)

            for job_id in to_remove:
                del self.jobs[job_id]

            logger.info(f"Cleaned up {len(to_remove)} old jobs")
            return len(to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Get job statistics."""
        total = len(self.jobs)
        completed = sum(1 for j in self.jobs.values() if j.status == JobStatus.COMPLETED)
        processing = sum(1 for j in self.jobs.values() if j.status == JobStatus.PROCESSING)
        failed = sum(1 for j in self.jobs.values() if j.status == JobStatus.FAILED)

        return {
            "total_jobs": total,
            "completed_jobs": completed,
            "processing_jobs": processing,
            "failed_jobs": failed
        }


# Global job store instance
job_store = InMemoryJobStore()


# Convenience functions for backward compatibility
async def create_job(job_id: str, prompt: str, user_id: str = "demo_user", creative: bool = False) -> Job:
    """Create a new job."""
    return await job_store.create_job(job_id, prompt, user_id, creative)


async def get_job(job_id: str) -> Optional[Job]:
    """Get job by ID."""
    return await job_store.get_job(job_id)


async def update_job_status(job_id: str, status: JobStatus, error: Optional[str] = None) -> bool:
    """Update job status."""
    return await job_store.update_job_status(job_id, status, error)


async def update_job_progress(job_id: str, progress: int, output_path: Optional[str] = None) -> bool:
    """Update job progress."""
    return await job_store.update_job_progress(job_id, progress, output_path)


async def list_jobs(user_id: str, limit: int = 50) -> list[Job]:
    """List jobs for a user."""
    return await job_store.list_jobs(user_id, limit)


async def cancel_job(job_id: str) -> bool:
    """Cancel a job."""
    return await job_store.cancel_job(job_id)


async def cleanup_old_jobs(days_old: int = 7) -> int:
    """Cleanup old jobs."""
    return await job_store.cleanup_old_jobs(days_old)


if __name__ == "__main__":
    # Test the job store
    async def test():
        # Create a job
        job = await create_job("test123", "Test prompt")
        print(f"Created job: {job.id}, status: {job.status.value}")

        # Update progress
        await update_job_progress("test123", 50)
        job = await get_job("test123")
        print(f"Updated progress: {job.progress}%")

        # Complete the job
        await update_job_status("test123", JobStatus.COMPLETED)
        job = await get_job("test123")
        print(f"Final status: {job.status.value}")

        # Stats
        stats = job_store.get_stats()
        print(f"Stats: {stats}")

    asyncio.run(test())
