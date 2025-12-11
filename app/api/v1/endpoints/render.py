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
from app.services.video_renderer import create_enhanced_text_video
from app.services.llm_client import llm_client
from app.services.errors import QuotaError
from app.services.logging_service import audit_logger
import uuid
import logging

router = APIRouter()


# ---------------------- MODELS ----------------------

class RenderRequest(BaseModel):
    prompt: str
    creative: Optional[bool] = False
    duration: Optional[int] = 5
    resolution: Optional[str] = "1080p"
    style: Optional[str] = "minimal"
    animation: Optional[str] = "fade"


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

        # Start video rendering in background with enhanced parameters
        asyncio.create_task(process_video_render(job_id, req))

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
async def get_status(job_id: str, user=Depends(require_user)):
    """Return job status."""

    job = await get_job(job_id)
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
async def cancel_job_endpoint(job_id: str, user=Depends(require_user)):
    """Cancel a job."""

    job = await get_job(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    if job.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Unauthorized")

    if not await cancel_job(job_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cannot cancel at this stage")

    audit_logger.log_job_event(job_id, "job_cancelled", {}, user.id)
    return {"message": "Cancellation requested"}


@router.get("/download/{job_id}")
async def download(job_id: str, user=Depends(require_user)):
    """Serve rendered file."""

    job = await get_job(job_id)
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


@router.get("/ai-status")
async def get_ai_status():
    """Check the status of AI services (local LLM and fallback availability)"""
    from app.services.llm_client import llm_client

    ai_status = {
        "local_llm": {
            "enabled": llm_client.use_local,
            "model": llm_client.ollama_model if llm_client.use_local else None,
            "url": llm_client.ollama_url if llm_client.use_local else None,
            "status": "unknown"
        },
        "openai": {
            "enabled": bool(llm_client.openai_key),
            "model": llm_client.openai_model,
            "status": "unknown"
        },
        "overall_status": "checking"
    }

    # Test local LLM if enabled
    if llm_client.use_local:
        try:
            # Quick test with a simple prompt
            test_result = await asyncio.wait_for(
                llm_client.generate_dsl("test", temperature=0.1, max_tokens=50),
                timeout=5.0
            )
            ai_status["local_llm"]["status"] = "available" if test_result else "error"
        except Exception as e:
            ai_status["local_llm"]["status"] = "unavailable"
            ai_status["local_llm"]["error"] = str(e)

    # Test OpenAI if key is available
    if llm_client.openai_key:
        try:
            # Quick test
            test_result = await asyncio.wait_for(
                llm_client.generate_dsl("test", temperature=0.1, max_tokens=50),
                timeout=5.0
            )
            ai_status["openai"]["status"] = "available" if test_result else "error"
        except Exception as e:
            ai_status["openai"]["status"] = "unavailable"
            ai_status["openai"]["error"] = str(e)

    # Determine overall status
    if ai_status["local_llm"]["status"] == "available":
        ai_status["overall_status"] = "ai_available"
        ai_status["message"] = "AI-powered generation available (Local LLM)"
    elif ai_status["openai"]["status"] == "available":
        ai_status["overall_status"] = "ai_available"
        ai_status["message"] = "AI-powered generation available (OpenAI)"
    else:
        ai_status["overall_status"] = "fallback_only"
        ai_status["message"] = "Using intelligent text enhancement (AI offline)"

    return ai_status


# ---------------------- HELPER FUNCTIONS ----------------------

async def enhance_prompt_for_video(prompt: str) -> str:
    """
    Enhance a simple prompt into more engaging, video-friendly text.
    This acts as a fallback when AI generation is not available.
    """
    prompt_lower = prompt.lower().strip()

    # Dictionary of enhancements for common prompts
    enhancements = {
        # Action/Motion prompts
        "a ball is dancing": "🎾 BALL DANCING! ⚡ Bounce • Groove • Spin • ENERGY! 🎾",
        "ball is dancing": "🎾 BALL DANCING! ⚡ Bounce • Groove • Spin • ENERGY! 🎾",
        "i ball is dancing": "🎾 BALL DANCING! ⚡ Bounce • Groove • Spin • ENERGY! 🎾",
        "ball dancing": "🎾 BALL DANCING! ⚡ Bounce • Groove • Spin • ENERGY! 🎾",

        # Technology prompts
        "hello world": "🚀 HELLO WORLD! ⚡ Code • Create • Innovate • FUTURE! 🚀",
        "hello": "🌟 HELLO! ⚡ Welcome • Connect • Discover • MAGIC! 🌟",

        # Creative prompts
        "create something": "🎨 CREATING MAGIC! ⚡ Design • Build • Innovate • ART! 🎨",
        "make art": "🎨 CREATING ART! ⚡ Colors • Shapes • Beauty • EXPRESSION! 🎨",

        # Learning prompts
        "learn coding": "💻 LEARN TO CODE! ⚡ Logic • Create • Build • FUTURE! 💻",
        "study": "📚 STUDY TIME! ⚡ Learn • Grow • Achieve • SUCCESS! 📚",

        # Business prompts
        "start business": "🚀 START YOUR BUSINESS! ⚡ Vision • Action • Growth • SUCCESS! 🚀",
        "entrepreneur": "💼 ENTREPRENEUR LIFE! ⚡ Ideas • Action • Scale • WIN! 💼",

        # Motivation prompts
        "never give up": "💪 NEVER GIVE UP! ⚡ Persist • Fight • Win • CHAMPION! 💪",
        "motivation": "🔥 GET MOTIVATED! ⚡ Action • Drive • Success • ACHIEVE! 🔥",

        # Generic fallbacks
        "test": "🧪 TESTING IN PROGRESS! ⚡ Experiment • Learn • Improve • EVOLVE! 🧪",
        "demo": "🎬 DEMO TIME! ⚡ Showcase • Present • Impress • WOW! 🎬",
    }

    # Check for exact matches first
    if prompt_lower in enhancements:
        return enhancements[prompt_lower]

    # Check for partial matches
    for key, value in enhancements.items():
        if key in prompt_lower:
            return value

    # Generic enhancement based on keywords
    words = prompt_lower.split()

    # Add energy indicators
    energy_words = ["fast", "quick", "speed", "power", "energy", "dynamic", "action"]
    creative_words = ["create", "make", "build", "design", "art", "draw"]
    learning_words = ["learn", "study", "teach", "understand", "know"]
    business_words = ["business", "money", "success", "work", "job"]

    if any(word in prompt_lower for word in energy_words):
        enhanced = f"⚡ {prompt.upper()}! ⚡ ENERGY • POWER • SPEED • ACTION! ⚡"
    elif any(word in prompt_lower for word in creative_words):
        enhanced = f"🎨 {prompt.upper()}! 🎨 CREATE • DESIGN • BUILD • ART! 🎨"
    elif any(word in prompt_lower for word in learning_words):
        enhanced = f"📚 {prompt.upper()}! 📚 LEARN • GROW • ACHIEVE • SUCCESS! 📚"
    elif any(word in prompt_lower for word in business_words):
        enhanced = f"🚀 {prompt.upper()}! 🚀 VISION • ACTION • GROWTH • SUCCESS! 🚀"
    else:
        # Default enhancement with emojis and energy
        enhanced = f"✨ {prompt.upper()}! ⚡ EXCITING • AMAZING • WONDERFUL • MAGIC! ✨"

    return enhanced

async def process_video_render(job_id: str, req: RenderRequest):
    """Process the video rendering in the background with enhanced parameters."""
    import os
    from pathlib import Path

    logger = logging.getLogger(__name__)

    try:
        # Log job started with parameters
        params = {
            "prompt": req.prompt,
            "duration": req.duration,
            "resolution": req.resolution,
            "style": req.style,
            "animation": req.animation,
            "creative": req.creative
        }
        audit_logger.log_job_event(job_id, "job_started", params, "system")
        logger.info(f"🚀 Job {job_id} started processing with enhanced parameters: {params}")

        # Update job status to processing
        await update_job_status(job_id, JobStatus.PROCESSING)
        audit_logger.log_job_event(job_id, "status_changed", {"status": "processing"}, "system")
        logger.info(f"📝 Job {job_id} status changed to PROCESSING")

        # Create storage directory if it doesn't exist
        storage_dir = Path("storage")
        storage_dir.mkdir(exist_ok=True)

        job_dir = storage_dir / "jobs" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        output_path = job_dir / "output.mp4"
        logger.info(f"📁 Job {job_id} storage directory created: {job_dir}")

        # Progress callback
        def progress_callback(progress: int):
            asyncio.create_task(update_job_progress(job_id, progress))
            logger.debug(f"📊 Job {job_id} progress: {progress}%")

        # Step 1: Generate scene DSL using AI
        await update_job_progress(job_id, 5)
        audit_logger.log_job_event(job_id, "ai_generation_started", params, "system")
        logger.info(f"🤖 Job {job_id} starting AI scene generation for prompt: '{req.prompt}'")

        try:
            scene_dsl = await llm_client.generate_dsl(req.prompt)
            logger.info(f"✅ Job {job_id} AI scene generation completed")
        except Exception as e:
            logger.warning(f"⚠️ Job {job_id} AI generation failed ({e}), falling back to enhanced text rendering")
            scene_dsl = None

        # If AI generation failed, enhance the prompt for better text rendering
        if scene_dsl is None:
            req.prompt = await enhance_prompt_for_video(req.prompt)
            logger.info(f"📝 Job {job_id} enhanced prompt for fallback: '{req.prompt}'")

        # Step 2: Create the enhanced video with AI-generated content or fallback
        await update_job_progress(job_id, 10)
        audit_logger.log_job_event(job_id, "render_started", {
            "output_path": str(output_path),
            "ai_generated": scene_dsl is not None,
            **params
        }, "system")
        logger.info(f"🎬 Job {job_id} starting enhanced video render to: {output_path}")

        if scene_dsl:
            # Use AI-generated scene DSL for advanced rendering
            created_path = create_scene_based_video(
                scene_dsl,
                str(output_path),
                progress_callback,
                duration=req.duration,
                resolution=req.resolution,
                style=req.style,
                animation=req.animation
            )
        else:
            # Fallback to enhanced text video
            created_path = create_enhanced_text_video(
                req.prompt,
                str(output_path),
                progress_callback,
                duration=req.duration,
                resolution=req.resolution,
                style=req.style,
                animation=req.animation
            )

        # Verify file was created
        if not os.path.exists(created_path):
            raise Exception("Video file was not created")

        # Update with final path
        await update_job_progress(job_id, 100, created_path)
        await update_job_status(job_id, JobStatus.COMPLETED)

        audit_logger.log_job_event(job_id, "job_completed", {
            "output_path": created_path,
            **params
        }, "system")
        logger.info(f"✅ Job {job_id} COMPLETED successfully with enhanced video, output: {created_path}")

    except Exception as e:
        error_msg = f"Enhanced video rendering failed: {str(e)}"
        logger.error(f"❌ Job {job_id} FAILED: {error_msg}", exc_info=True)
        audit_logger.log_job_event(job_id, "job_failed", {"error": error_msg}, "system")
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
