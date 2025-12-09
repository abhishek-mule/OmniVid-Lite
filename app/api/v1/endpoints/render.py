from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from app.core.config import settings
from app.services.security import require_user
from app.services.job_store import (
    create_job,
    get_job,
    update_job_status,
    update_job_progress,
    list_jobs,
    cancel_job,
    cleanup_old_jobs,
    JobStatus,
    Job
)
from app.services.video_renderer import create_text_video
from app.services.errors import QuotaError
from app.services.logging_service import audit_logger
import uuid
import logging

router = APIRouter()


# ---------------------- MODELS ----------------------

class RenderRequest(BaseModel):
    prompt: str
    creative: Optional[bool] = False


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    output_path: Optional[str]
    error: Optional[str]
    created_at: str
    updated_at: str


class JobSummary(BaseModel):
    job_id: str
    status: str
    output_path: Optional[str]
    created_at: str
    updated_at: str


class JobListResponse(BaseModel):
    jobs: List[JobSummary]


# ---------------------- ROUTES ----------------------

@router.post("/render", status_code=202)
async def start_render(req: RenderRequest, user=Depends(require_user), request: Request = None):
    """Create + start a video render request."""

    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Prompt must be non-empty")

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    try:
        # Create job in store
        job = await create_job(job_id, req.prompt, user.id, req.creative)
        audit_logger.log_job_event(job.id, "job_created", {"prompt": prompt, "creative": req.creative}, user.id)

        # Start video rendering in background (MVP implementation)
        asyncio.create_task(process_video_render(job_id, req.prompt))

        base = str(request.base_url).rstrip("/")

        return {
            "job_id": job.id,
            "status": job.status.value,
            "poll_url": f"{base}/api/v1/render/status/{job.id}",
            "download_url": f"{base}/api/v1/render/download/{job.id}",
        }

    except Exception as e:
        audit_logger.log_job_event("unknown", "job_creation_failed", {"error": str(e)}, user.id)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create job: {str(e)}")


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str, user=Depends(require_user)):
    """Return job status."""

    job = get_job(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    if job.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Unauthorized")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        output_path=job.output_path,
        error=job.error,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )


@router.patch("/cancel/{job_id}")
def cancel_job_endpoint(job_id: str, user=Depends(require_user)):
    """Cancel a job."""

    job = get_job(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    if job.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Unauthorized")

    if not cancel_job(job_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot cancel at this stage")

    audit_logger.log_job_event(job_id, "job_cancelled", {}, user.id)
    return {"message": "Cancellation requested"}


@router.get("/download/{job_id}")
def download(job_id: str, user=Depends(require_user)):
    """Serve rendered file."""

    job = get_job(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    if job.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Unauthorized")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status.HTTP_425_TOO_EARLY, f"Job not ready: {job.status.value}")

    if not job.output_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Output missing")

    path = Path(job.output_path)
    if not path.exists():
        raise HTTPException(status.HTTP_410_GONE, "File expired")

    def stream(chunk=8192):
        with open(path, "rb") as f:
            while data := f.read(chunk):
                yield data

    audit_logger.log_job_event(job_id, "file_downloaded", {"filename": path.name}, user.id)

    return StreamingResponse(
        stream(),
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename={path.name}"}
    )


@router.post("/cleanup")
async def cleanup_system(days_old: int = 7, user=Depends(require_user)):
    """Clean up old jobs and orphaned files (admin operation)"""

    # Basic auth check - in real app, check for admin role
    if user.id != "demo_user":  # Placeholder for admin check
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")

    old_jobs_cleaned = await cleanup_old_jobs(days_old)
    # Note: orphaned file cleanup not implemented in simple version

    return {
        "message": f"Cleanup completed: {old_jobs_cleaned} old jobs removed",
        "old_jobs_removed": old_jobs_cleaned,
        "orphaned_files_removed": 0
    }


# ---------------------- HELPER FUNCTIONS ----------------------

async def process_video_render(job_id: str, prompt: str):
    """Process the video rendering in the background."""
    import os
    from pathlib import Path

    try:
        logger = logging.getLogger(__name__)

        # Update job status to processing
        await update_job_status(job_id, JobStatus.PROCESSING)
        logger.info(f"Started processing job {job_id} with prompt: '{prompt}'")

        # Create storage directory if it doesn't exist
        storage_dir = Path("storage")
        storage_dir.mkdir(exist_ok=True)

        job_dir = storage_dir / "jobs" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        output_path = job_dir / "output.mp4"

        # Progress callback
        def progress_callback(progress: int):
            asyncio.create_task(update_job_progress(job_id, progress))

        # Create the video
        await update_job_progress(job_id, 10)
        created_path = create_text_video(prompt, str(output_path), progress_callback)

        # Verify file was created
        if not os.path.exists(created_path):
            raise Exception("Video file was not created")

        # Update with final path
        await update_job_progress(job_id, 100, created_path)
        await update_job_status(job_id, JobStatus.COMPLETED)

        logger.info(f"Successfully completed job {job_id}, output: {created_path}")

    except Exception as e:
        error_msg = f"Video rendering failed: {str(e)}"
        logger.error(f"Job {job_id} failed: {error_msg}")
        await update_job_status(job_id, JobStatus.FAILED, error_msg)


# Update the list_jobs endpoint to use the new job store
@router.get("/jobs", response_model=JobListResponse)
async def list_user_jobs(limit: int = 50, user=Depends(require_user)):
    """List jobs for the authenticated user."""

    user_jobs = await list_jobs(user.id, limit)

    return JobListResponse(
        jobs=[
            JobSummary(
                job_id=job.id,
                status=job.status.value,
                output_path=job.output_path,
                created_at=job.created_at.isoformat(),
                updated_at=job.updated_at.isoformat(),
            )
            for job in user_jobs
        ]
    )
