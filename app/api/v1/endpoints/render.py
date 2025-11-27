from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from sqlalchemy import select

from app.core.config import settings
from app.db.models import Job, JobStatus
from app.db.session import get_session
from app.services.redis_pool import get_redis_pool
from app.services.security import require_user
from app.services.job_service import (
    create_job_with_idempotency,
    get_job,
    cancel_job,
    cleanup_old_jobs,
    cleanup_orphaned_files,
)
from app.services.errors import QuotaError
from app.services.logging_service import audit_logger

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
    """Create + queue a render request."""

    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Prompt must be non-empty")

    try:
        job = create_job_with_idempotency(prompt, req.creative, user_id=user.id)
        audit_logger.log_job_event(job.id, "job_created", {"prompt": prompt, "creative": req.creative}, user.id)
    except QuotaError as e:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(e))

    redis = await get_redis_pool()
    if redis:
        await redis.enqueue_job("generate_video", job.id)
        audit_logger.log_job_event(job.id, "job_enqueued", {}, user.id)
    else:
        # For demo mode without Redis, run the pipeline directly
        # In a real app, you'd use background tasks or a different queuing system
        from app.services.pipeline import run_pipeline
        import asyncio
        # Run in background (fire and forget for demo)
        asyncio.create_task(run_pipeline(prompt, job.id, req.creative))
        audit_logger.log_job_event(job.id, "job_started_directly", {}, user.id)

    base = str(request.base_url).rstrip("/")

    return {
        "job_id": job.id,
        "status": job.status.value,
        "poll_url": f"{base}/api/v1/render/status/{job.id}",
        "download_url": f"{base}/api/v1/render/download/{job.id}",
    }


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


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(limit: int = 50, user=Depends(require_user)):

    with get_session() as session:
        stmt = (
            select(Job)
            .where(Job.user_id == user.id)
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        result = session.execute(stmt)
        jobs_db = result.scalars().all()

    return JobListResponse(
        jobs=[
            JobSummary(
                job_id=j.id,
                status=j.status.value,
                output_path=j.output_path,
                created_at=j.created_at.isoformat(),
                updated_at=j.updated_at.isoformat(),
            )
            for j in jobs_db
        ]
    )


@router.post("/cleanup")
def cleanup_system(days_old: int = 7, user=Depends(require_user)):
    """Clean up old jobs and orphaned files (admin operation)"""

    # Basic auth check - in real app, check for admin role
    if user.id != "demo_user":  # Placeholder for admin check
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")

    old_jobs_cleaned = cleanup_old_jobs(days_old)
    orphaned_cleaned = cleanup_orphaned_files()

    return {
        "message": f"Cleanup completed: {old_jobs_cleaned} old jobs, {orphaned_cleaned} orphaned files removed",
        "old_jobs_removed": old_jobs_cleaned,
        "orphaned_files_removed": orphaned_cleaned
    }
