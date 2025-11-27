import os
from app.services.pipeline import run_pipeline
from app.services.job_service import update_job_status, get_job
from app.db.models import JobStatus
from datetime import datetime

def generate_video(ctx, job_id: str):
    """Worker task to generate video for a job"""
    # Get job and mark as processing
    job = get_job(job_id)
    if not job:
        return

    update_job_status(job_id, JobStatus.PROCESSING)

    try:
        # Run pipeline
        result = run_pipeline(job.prompt, job_id, job.creative)

        # Update job based on result
        if result["status"] == "done":
            update_job_status(job_id, JobStatus.COMPLETED)
            # Update output path
            job = get_job(job_id)
            if job:
                job.output_path = result.get("output")
                from app.db.session import get_session
                with get_session() as session:
                    session.add(job)
                    session.commit()
        else:
            update_job_status(job_id, JobStatus.FAILED, result.get("error"))

    except Exception as e:
        # Handle unexpected errors
        update_job_status(job_id, JobStatus.FAILED, str(e))