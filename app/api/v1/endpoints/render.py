from pathlib import Path
import json
import uuid
import logging
import os
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.services.pipeline import run_pipeline

logger = logging.getLogger("omnivid.api.render")
router = APIRouter()

JOBS_DIR = settings.BASE_DIR / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------- MODELS ----------------------

class RenderRequest(BaseModel):
    prompt: str
    creative: Optional[bool] = False


class JobStatus(BaseModel):
    job_id: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    logs: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class JobSummary(BaseModel):
    job_id: str
    status: str
    output: Optional[str]
    time: float


class JobListResponse(BaseModel):
    jobs: List[JobSummary]


# ---------------------- UTILS ----------------------

def _job_file_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


async def _write_job_status(job_id: str, payload: Dict[str, Any]):
    _job_file_path(job_id).write_text(json.dumps(payload, indent=2))


# ---------------------- BACKGROUND WORKER ----------------------

async def _background_worker(prompt: str, job_id: str, creative: bool):
    logger.info("Job %s started", job_id)

    await _write_job_status(job_id, {
        "job_id": job_id,
        "status": "running",
        "output": None,
        "error": None,
    })

    try:
        result = await run_pipeline(prompt=prompt, job_id=job_id, creative=creative)

        final = {
            "job_id": job_id,
            "status": result.get("status", "done"),
            "output": result.get("output"),
            "logs": result.get("logs"),
            "raw": result
        }

        await _write_job_status(job_id, final)
        logger.info("Job %s finished", job_id)

    except Exception as e:
        await _write_job_status(job_id, {
            "job_id": job_id,
            "status": "error",
            "output": None,
            "error": str(e)
        })
        logger.exception("Job %s failed", job_id)


# ---------------------- ROUTES ----------------------

@router.post("/render", status_code=202)
async def start_render(req: RenderRequest, background_tasks: BackgroundTasks):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(400, "Prompt must be non-empty")

    job_id = str(uuid.uuid4())

    await _write_job_status(job_id, {
        "job_id": job_id,
        "status": "queued",
        "output": None,
        "error": None
    })

    background_tasks.add_task(_background_worker, prompt, job_id, req.creative)

    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/api/v1/render/status/{job_id}",
        "download_url": f"/api/v1/render/download/{job_id}",
    }


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    p = _job_file_path(job_id)
    if not p.exists():
        raise HTTPException(404, "job not found")

    data = json.loads(p.read_text())
    return JobStatus(**data)


@router.get("/download/{job_id}")
async def download_result(job_id: str):
    p = _job_file_path(job_id)
    if not p.exists():
        raise HTTPException(404, "job not found")

    meta = json.loads(p.read_text())

    if meta.get("status") != "done":
        raise HTTPException(400, f"job not finished: {meta.get('status')}")

    output = meta.get("output")
    if not output:
        raise HTTPException(404, "no output recorded")

    out_path = Path(output)
    if not out_path.exists():
        candidate = settings.OUTPUT_DIR / out_path.name
        if candidate.exists():
            out_path = candidate
        else:
            raise HTTPException(404, "rendered file not found")

    return FileResponse(out_path, filename=out_path.name, media_type="video/mp4")


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(limit: int = 50):
    files = sorted(JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    jobs = []

    for p in files[:limit]:
        try:
            data = json.loads(p.read_text())
            jobs.append(JobSummary(
                job_id=data.get("job_id"),
                status=data.get("status"),
                output=data.get("output"),
                time=p.stat().st_mtime
            ))
        except:
            continue

    return JobListResponse(jobs=jobs)
