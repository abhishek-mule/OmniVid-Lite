# app/api/v1/endpoints/render.py
import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.core.config import settings

# Import pipeline orchestrator
from app.services.pipeline import run_pipeline

logger = logging.getLogger("omnivid.api.render")
router = APIRouter()

# Jobs directory (simple filesystem based job store)
JOBS_DIR = settings.BASE_DIR / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)


class RenderRequest(BaseModel):
    prompt: str
    creative: Optional[bool] = False
    # you can add more options here (style, template, resolution override, etc.)


def _job_file_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


async def _write_job_status(job_id: str, payload: Dict[str, Any]):
    p = _job_file_path(job_id)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


async def _background_worker(prompt: str, job_id: str, creative: bool):
    """
    Background task: runs the pipeline then writes final job status.
    This function is intentionally robust and captures exceptions.
    """
    logger.info("Job %s queued (background)", job_id)
    # initial state
    initial = {"job_id": job_id, "status": "running", "prompt": prompt, "creative": creative, "output": None, "error": None}
    await _write_job_status(job_id, initial)

    try:
        # run_pipeline is async and returns a dict (status, output, logs)
        result = await run_pipeline(prompt=prompt, job_id=job_id, creative=creative)
        # result expected to contain at least keys: job_id, status, output, logs
        final = {
            "job_id": job_id,
            "status": result.get("status", "done"),
            "output": str(result.get("output")) if result.get("output") else None,
            "logs": result.get("logs"),
            "raw": result,
        }
        await _write_job_status(job_id, final)
        logger.info("Job %s finished (status=%s)", job_id, final["status"])
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        error_payload = {
            "job_id": job_id,
            "status": "error",
            "output": None,
            "error": str(exc),
        }
        await _write_job_status(job_id, error_payload)


@router.post("/render", status_code=status.HTTP_202_ACCEPTED)
async def start_render(req: RenderRequest, background_tasks: BackgroundTasks):
    """
    Kick off a render job in the background. Returns job_id and status URL immediately.
    """
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt must be non-empty")

    job_id = str(uuid.uuid4())
    job_file = _job_file_path(job_id)

    # write initial queued status
    queued = {"job_id": job_id, "status": "queued", "prompt": prompt, "creative": req.creative, "output": None, "error": None}
    job_file.write_text(json.dumps(queued, indent=2), encoding="utf-8")

    # schedule background worker
    background_tasks.add_task(_background_worker, prompt, job_id, req.creative)

    base_url = os.getenv("API_BASE_URL", "")  # optional, for constructing full URLs
    status_url = f"/api/v1/render/status/{job_id}"
    download_url = f"/api/v1/render/download/{job_id}"

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "job_id": job_id,
            "status": "queued",
            "status_url": status_url,
            "download_url": download_url,
        },
    )


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Return job status JSON.
    """
    p = _job_file_path(job_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="job not found")

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.exception("Failed to read job file %s", job_id)
        raise HTTPException(status_code=500, detail="failed to read job file")

    return JSONResponse(content=data)


@router.get("/download/{job_id}")
async def download_result(job_id: str):
    """
    If job completed successfully and output file exists, return it as a FileResponse.
    Otherwise return 404 with helpful message.
    """
    p = _job_file_path(job_id)
    if not p.exists():
        raise HTTPException(status_code=404, detail="job not found")

    try:
        meta = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="failed to read job file")

    if meta.get("status") != "done":
        raise HTTPException(status_code=400, detail=f"job not finished: status={meta.get('status')}")

    output = meta.get("output")
    if not output:
        raise HTTPException(status_code=404, detail="no output path recorded for job")

    out_path = Path(output)
    # If your pipeline stored relative paths under project root, make absolute
    if not out_path.exists():
        # try relative to BASE_DIR or REMOTION outputs directory
        candidate = settings.OUTPUT_DIR / Path(output).name
        if candidate.exists():
            out_path = candidate
        else:
            raise HTTPException(status_code=404, detail="rendered file not found on disk")

    return FileResponse(path=str(out_path), filename=out_path.name, media_type="video/mp4")


@router.get("/jobs")
async def list_jobs(limit: int = 50):
    """
    List recent job summaries (reads job json files from jobs/).
    """
    files = sorted(JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for p in files[:limit]:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            items.append({
                "job_id": data.get("job_id"),
                "status": data.get("status"),
                "output": data.get("output"),
                "time": p.stat().st_mtime
            })
        except Exception:
            continue

    return JSONResponse(content={"jobs": items})