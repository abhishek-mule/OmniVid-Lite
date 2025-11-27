"""
Background worker for processing render jobs
Run this separately: python -m app.worker
"""
import asyncio
import logging
import signal
import sys
import os
import subprocess
import json
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.config import settings
from app.db.session import get_db_session
from app.db.models import Job, JobStatus
from app.services.llm_client import llm_client
from app.services.scene_to_tsx import scene_to_tsx
from app.services.remotion_adapter import render_remotion
from app.services.errors import RenderError
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
        """Get next pending job from database"""
        with get_db_session() as session:
            job = session.query(Job).filter(
                Job.status == JobStatus.PENDING
            ).order_by(Job.created_at).first()

            if job:
                # Mark as processing
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.utcnow()
                session.commit()

            return job

    async def _process_job(self, job):
        """
        Process a single render job

        Args:
            job: Job database object
        """
        logger.info(f"Processing job {job.id}")

        try:
            # Step 1: Generate scene JSON from LLM
            logger.info(f"Generating scene JSON for job {job.id}")
            dsl = await llm_client.generate_dsl(job.prompt)

            # Save DSL to job directory
            job_dir = settings.REMOTION_DIR / "src" / "generated" / job.id
            job_dir.mkdir(parents=True, exist_ok=True)
            dsl_path = job_dir / "scene.json"
            dsl_path.write_text(json.dumps(dsl, indent=2), encoding="utf-8")

            # Step 2: Generate Remotion TSX file
            logger.info(f"Generating TSX file for job {job.id}")
            tsx_path = job_dir / "GeneratedScene.tsx"
            scene_to_tsx(str(dsl_path), str(tsx_path))

            # Step 3: Render video with Remotion
            logger.info(f"Rendering video for job {job.id}")
            output_file = settings.OUTPUT_DIR / f"{job.id}.mp4"

            # Run rendering in thread pool to avoid blocking
            success, output_path, logs = await asyncio.to_thread(
                render_remotion, "GeneratedScene", str(output_file)
            )

            if not success:
                raise RenderError(f"Rendering failed: {logs}")

            # Step 4: Update job with results
            with get_db_session() as session:
                db_job = session.get(Job, job.id)
                if db_job:
                    db_job.status = JobStatus.COMPLETED
                    db_job.output_path = str(output_path)
                    db_job.completed_at = datetime.utcnow()
                    db_job.progress = 100.0
                    session.commit()

            logger.info(f"Job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id} failed: {str(e)}", exc_info=True)

            # Update job as failed
            with get_db_session() as session:
                db_job = session.get(Job, job.id)
                if db_job:
                    db_job.status = JobStatus.FAILED
                    db_job.error = str(e)
                    db_job.completed_at = datetime.utcnow()
                    session.commit()

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