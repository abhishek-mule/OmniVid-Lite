"""
Background worker for processing render jobs using simple video renderer
Run this separately: python -m app.worker
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from app.core.config import settings
from app.services.job_store import job_store, JobStatus
from app.services.video_renderer import create_text_video
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class RenderWorker:
    """Background worker for processing render jobs"""

    def __init__(self):
        self.running = False
        self.current_job_id: Optional[str] = None

    async def start(self):
        """Start the worker"""
        logger.info("Starting render worker...")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = True
        logger.info("Worker started successfully")

        # Main processing loop
        await self._process_loop()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def _process_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Check for pending jobs in database
                job = await self._get_next_job()

                if not job:
                    # No jobs available, wait a bit
                    await asyncio.sleep(2)
                    continue

                # Process the job
                self.current_job_id = job.id
                await self._process_job(job)
                self.current_job_id = None

            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}", exc_info=True)
                await asyncio.sleep(5)

        logger.info("Processing loop ended")

    async def _get_next_job(self):
        """Get next pending job from job store"""
        # Find the oldest pending job
        pending_jobs = [
            job for job in job_store.jobs.values()
            if job.status == JobStatus.PENDING
        ]
        if not pending_jobs:
            return None

        # Sort by creation time and get the oldest
        pending_jobs.sort(key=lambda j: j.created_at)
        job = pending_jobs[0]

        # Mark as processing
        await job_store.update_job_status(job.id, JobStatus.PROCESSING)
        logger.info(f"Marked job {job.id} as processing")
        return job

    async def _process_job(self, job):
        """
        Process a single render job using simple video renderer

        Args:
            job: Job object from job store
        """
        logger.info(f"Processing job {job.id} with prompt: '{job.prompt}'")

        try:
            # Update progress to 10%
            await job_store.update_job_progress(job.id, 10)

            # Create storage directory
            import os
            from pathlib import Path
            storage_dir = Path("storage")
            storage_dir.mkdir(exist_ok=True)
            job_dir = storage_dir / "jobs" / job.id
            job_dir.mkdir(parents=True, exist_ok=True)
            output_path = job_dir / "output.mp4"

            # Progress callback for renderer
            def progress_callback(progress: int):
                asyncio.create_task(job_store.update_job_progress(job.id, progress))

            # Update progress to 20%
            await job_store.update_job_progress(job.id, 20)

            # Render video using simple renderer
            logger.info(f"Rendering video for job {job.id}")
            created_path = create_text_video(job.prompt, str(output_path), progress_callback)

            # Verify file was created
            if not os.path.exists(created_path):
                raise Exception("Video file was not created")

            # Update job as completed
            await job_store.update_job_status(job.id, JobStatus.COMPLETED)
            await job_store.update_job_progress(job.id, 100, created_path)

            logger.info(f"Job {job.id} completed successfully, output: {created_path}")

        except Exception as e:
            error_msg = f"Video rendering failed: {str(e)}"
            logger.error(f"Job {job.id} failed: {error_msg}", exc_info=True)
            await job_store.update_job_status(job.id, JobStatus.FAILED, error_msg)

    async def stop(self):
        """Stop the worker gracefully"""
        logger.info("Stopping worker...")
        self.running = False

        # Wait for current job to finish
        if self.current_job_id:
            logger.info(f"Waiting for current job {self.current_job_id} to finish...")
            # Give it 30 seconds to finish
            for _ in range(30):
                if not self.current_job_id:
                    break
                await asyncio.sleep(1)

        logger.info("Worker stopped")


async def main():
    """Main entry point"""
    worker = RenderWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())