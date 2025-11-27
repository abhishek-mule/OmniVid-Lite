import hashlib
import json
from typing import Optional
from sqlalchemy import select
from app.db.models import Job, JobStatus
from app.db.session import get_session
import uuid
from datetime import datetime

def compute_request_hash(payload: dict) -> str:
    """Compute hash for request deduplication"""
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

def create_job_with_idempotency(
    prompt: str,
    creative: bool = False,
    user_id: Optional[str] = None
) -> Job:
    """Create a job with idempotency based on request content"""
    request_payload = {
        "prompt": prompt,
        "creative": creative,
        "user_id": user_id
    }
    request_hash = compute_request_hash(request_payload)

    with get_session() as session:
        # Check for existing job with same hash
        stmt = select(Job).where(Job.request_hash == request_hash)
        result = session.execute(stmt)
        existing_job = result.scalar_one_or_none()

        if existing_job and existing_job.status not in [JobStatus.FAILED, JobStatus.CANCELLED]:
            # Return existing job if it's still active
            return existing_job

        # Create new job
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            user_id=user_id,
            prompt=prompt,
            creative=creative,
            status=JobStatus.PENDING,
            request_hash=request_hash
        )

        session.add(job)
        session.commit()
        session.refresh(job)

        return job

def get_job(job_id: str) -> Optional[Job]:
    """Get job by ID"""
    with get_session() as session:
        return session.get(Job, job_id)

def update_job_status(job_id: str, status: JobStatus, error: Optional[str] = None):
    """Update job status"""
    with get_session() as session:
        job = session.get(Job, job_id)
        if job:
            job.status = status
            job.updated_at = datetime.utcnow()
            if error:
                job.error = error
            session.commit()

def cancel_job(job_id: str) -> bool:
    """Cancel a job if possible"""
    with get_session() as session:
        job = session.get(Job, job_id)
        if job and job.status in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING]:
            job.status = JobStatus.CANCELLED
            job.updated_at = datetime.utcnow()
            session.commit()
            return True
        return False

def cleanup_old_jobs(days_old: int = 7) -> int:
    """Clean up jobs and files older than specified days"""
    from datetime import datetime, timedelta
    from pathlib import Path
    import shutil

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    cleaned_count = 0

    with get_session() as session:
        # Find old jobs
        old_jobs = session.query(Job).filter(
            Job.created_at < cutoff_date,
            Job.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED])
        ).all()

        for job in old_jobs:
            # Remove output file if it exists
            if job.output_path:
                output_path = Path(job.output_path)
                if output_path.exists():
                    try:
                        output_path.unlink()
                    except Exception:
                        pass  # Ignore cleanup errors

            # Remove job directory
            job_dir = Path("remotion_engine/src/generated") / job.id
            if job_dir.exists():
                try:
                    shutil.rmtree(job_dir)
                except Exception:
                    pass  # Ignore cleanup errors

            # Delete job record
            session.delete(job)
            cleaned_count += 1

        session.commit()

    return cleaned_count

def cleanup_orphaned_files() -> int:
    """Clean up orphaned files not associated with any job"""
    from pathlib import Path
    import shutil

    cleaned_count = 0
    generated_dir = Path("remotion_engine/src/generated")
    output_dir = Path("remotion_engine/outputs")

    if not generated_dir.exists():
        return 0

    # Get all job IDs from database
    with get_session() as session:
        job_ids = {str(job.id) for job in session.query(Job.id).all()}

    # Clean generated directories
    for item in generated_dir.iterdir():
        if item.is_dir() and item.name not in job_ids:
            try:
                shutil.rmtree(item)
                cleaned_count += 1
            except Exception:
                pass

    # Clean output files
    if output_dir.exists():
        for item in output_dir.iterdir():
            if item.is_file() and item.suffix == '.mp4':
                # Extract job ID from filename
                job_id = item.stem
                if job_id not in job_ids:
                    try:
                        item.unlink()
                        cleaned_count += 1
                    except Exception:
                        pass

    return cleaned_count