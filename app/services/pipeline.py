# app/services/pipeline.py
import json, uuid
from pathlib import Path
from typing import Dict, Any
from .llm_parser import llm_parser
from ..schemas.scene_schema import DSLModel
from .scene_to_tsx import generate_remotion_from_dsl
from .remotion_executor import remotion_executor
from ..core.config import settings

JOBS_DIR = settings.BASE_DIR / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

async def run_pipeline(prompt: str, job_id: str = None, creative: bool = False) -> Dict[str, Any]:
    job_id = job_id or str(uuid.uuid4())
    job_file = JOBS_DIR / f"{job_id}.json"
    # 1) Ask LLM (use stronger model if creative requested)
    model = None
    temperature = 0.35 if not creative else 0.6
    dsl_raw = await llm_parser.generate_dsl(prompt, temperature=temperature, model=model)
    # 2) Validate DSL
    dsl = DSLModel.parse_obj(dsl_raw)
    # 3) compute startFrame for each scene
    cursor = 0
    for s in dsl.scenes:
        s.startFrame = cursor
        cursor += s.duration
    # save dsl to jobs folder for debugging
    dsl_path = JOBS_DIR / f"{job_id}_dsl.json"
    dsl_path.write_text(dsl.json(indent=2), encoding="utf-8")
    # 4) generate remotion TSX files
    generated_dir = settings.GENERATED_SCENE_DIR
    generate_remotion_from_dsl(dsl.dict(), out_dir=generated_dir)
    # 5) ensure assets copied (scene_to_tsx should have arranged assets)
    # 6) call remotion
    success, out_path, logs = remotion_executor.render_sync(comp_id="Main", job_id=job_id)
    # 7) write job status
    status = {"job_id": job_id, "status": "done" if success else "error", "output": str(out_path) if out_path else None, "logs": logs}
    job_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status