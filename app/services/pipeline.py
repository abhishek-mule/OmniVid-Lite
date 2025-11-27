# app/services/pipeline.py
import asyncio
import json
import uuid
from pathlib import Path
from datetime import datetime
from enum import Enum
from pydantic import ValidationError
from app.core.config import settings
from app.services.llm_client import llm_client
from app.services.scene_to_tsx import scene_to_tsx
from app.services.remotion_adapter import render_remotion
from app.schemas.dsl_schema import VideoDSL
from app.services.errors import LLMError, DSLTransformError, RenderError

OUTPUT_DIR = settings.OUTPUT_DIR
GENERATED_SRC = settings.REMOTION_DIR / "src" / "generated"
GENERATED_SRC.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class PipelineStage(Enum):
    START = "start"
    LLM = "llm"
    VALIDATED = "validated"
    TSX = "tsx"
    RENDERED = "rendered"

def log_entry(stage: str, message: str):
    return {
        "time": datetime.now().isoformat(),
        "stage": stage,
        "message": message
    }

def save_status(job_dir: Path, stage: PipelineStage, logs: list):
    status_path = job_dir / "status.json"
    status_data = {
        "stage": stage.value,
        "updated_at": datetime.now().isoformat(),
        "logs": logs
    }
    status_path.write_text(json.dumps(status_data, indent=2), encoding="utf-8")

def load_status(job_dir: Path):
    status_path = job_dir / "status.json"
    if status_path.exists():
        return json.loads(status_path.read_text(encoding="utf-8"))
    return {"stage": PipelineStage.START.value, "logs": []}

async def run_pipeline(prompt: str, job_id: str, creative: bool = False):
    job_dir = GENERATED_SRC / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    status = load_status(job_dir)
    current_stage = PipelineStage(status.get("stage", "start"))
    logs = status.get("logs", [])

    try:
        # LLM Stage
        if current_stage.value == PipelineStage.START.value:
            logs.append(log_entry("llm", "🧠 Calling LLM..."))
            raw_dsl = await llm_client.generate_dsl(prompt)
            save_status(job_dir, PipelineStage.LLM, logs)
            current_stage = PipelineStage.LLM

        # Validation Stage
        if current_stage.value in [PipelineStage.LLM.value, PipelineStage.START.value]:
            logs.append(log_entry("validation", "🔍 Validating DSL..."))
            dsl = VideoDSL(**raw_dsl).dict()
            save_status(job_dir, PipelineStage.VALIDATED, logs)
            current_stage = PipelineStage.VALIDATED

        # TSX Generation Stage
        if current_stage.value in [PipelineStage.VALIDATED.value, PipelineStage.LLM.value, PipelineStage.START.value]:
            dsl_path = job_dir / "scene.json"
            dsl_path.write_text(json.dumps(dsl, indent=2), encoding="utf-8")

            logs.append(log_entry("tsx", "🛠 Converting DSL → TSX..."))
            tsx_path = GENERATED_SRC / "GeneratedScene.tsx"  # Fixed location for Remotion
            scene_to_tsx(str(dsl_path), str(tsx_path))
            save_status(job_dir, PipelineStage.TSX, logs)
            current_stage = PipelineStage.TSX

        # Rendering Stage
        if current_stage.value in [PipelineStage.TSX.value, PipelineStage.VALIDATED.value, PipelineStage.LLM.value, PipelineStage.START.value]:
            logs.append(log_entry("render", "🎬 Rendering..."))
            composition_id = f"Scene_{job_id}"
            output_file = OUTPUT_DIR / f"{job_id}.mp4"
            await asyncio.to_thread(render_remotion, composition_id, str(output_file), job_id)
            save_status(job_dir, PipelineStage.RENDERED, logs)

        logs.append(log_entry("done", "✅ Done."))
        return {"status": "done", "output": str(output_file), "logs": logs}

    except ValidationError as e:
        logs.append(log_entry("validation", f"❌ DSL Validation Error: {e}"))
        save_status(job_dir, current_stage, logs)
        return {"status": "failed", "stage": "validation", "error": str(e), "logs": logs}

    except RenderError as e:
        logs.append(log_entry("render", f"❌ Rendering failed: {e}"))
        save_status(job_dir, current_stage, logs)
        return {"status": "failed", "stage": "render", "error": str(e), "logs": logs}

    except Exception as e:
        logs.append(log_entry("unknown", f"❌ Fatal: {e}"))
        save_status(job_dir, current_stage, logs)
        return {"status": "failed", "stage": "unknown", "error": str(e), "logs": logs}