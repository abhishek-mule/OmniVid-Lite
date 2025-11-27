import os
import asyncio
import time
from typing import Dict, Any
from app.services.pipeline import run_pipeline
from app.services.job_service import update_job_status, get_job
from app.db.models import JobStatus
from datetime import datetime

async def generate_video(ctx, job_id: str):
    """Worker task to generate video for a job with retry logic"""
    max_retries = 3
    base_delay = 1.0  # seconds

    for attempt in range(max_retries):
        try:
            # Get job and mark as processing
            job = get_job(job_id)
            if not job:
                return

            update_job_status(job_id, JobStatus.PROCESSING)

            # Run pipeline
            result = await run_pipeline(job.prompt, job_id, job.creative)

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
                break  # Success, exit retry loop
            else:
                # Check if this is a retryable error
                error_msg = result.get("error", "")
                if _is_retryable_error(error_msg) and attempt < max_retries - 1:
                    # Exponential backoff
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final failure
                    update_job_status(job_id, JobStatus.FAILED, result.get("error"))
                    break

        except Exception as e:
            error_msg = str(e)
            if _is_retryable_error(error_msg) and attempt < max_retries - 1:
                # Retry on transient errors
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            else:
                # Handle unexpected errors
                update_job_status(job_id, JobStatus.FAILED, error_msg)
                break

def _is_retryable_error(error_msg: str) -> bool:
    """Determine if an error is retryable"""
    retryable_patterns = [
        "connection", "timeout", "temporary", "rate limit",
        "network", "unavailable", "busy", "lock"
    ]
    error_lower = error_msg.lower()
    return any(pattern in error_lower for pattern in retryable_patterns)