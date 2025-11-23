import asyncio
import json
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse

import requests

from ..core.config import settings
from .code_generator import CodeGenerator

import logging
logger = logging.getLogger("omnivid.renderer")
logger.setLevel(logging.INFO)

# ensure output dir exists on import
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.GENERATED_SCENE_DIR.mkdir(parents=True, exist_ok=True)

PUBLIC_DIR = settings.REMOTION_DIR / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

code_generator = CodeGenerator()


async def _ensure_assets(scene: Dict[str, Any]):
    """Copy local files or download remote images into remotion/public."""
    for layer in scene.get("layers", []):
        if layer.get("type") == "image":
            src = layer.get("src")
            if not src:
                continue
            parsed = urlparse(src)
            dest = PUBLIC_DIR / Path(parsed.path).name
            if parsed.scheme in ("http", "https"):
                # download
                r = requests.get(src, stream=True, timeout=15)
                if r.status_code == 200:
                    with open(dest, "wb") as fh:
                        for chunk in r.iter_content(1024 * 8):
                            fh.write(chunk)
            else:
                # local file: copy
                src_path = Path(src)
                if src_path.exists():
                    shutil.copy(src_path, dest)
    return PUBLIC_DIR


async def _run_subprocess(cmd: list, cwd: Optional[Path] = None, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """
    Run a subprocess asynchronously and capture stdout/stderr.
    Returns (returncode, stdout, stderr)
    """
    logger.info("Running subprocess: %s (cwd=%s)", " ".join(cmd), cwd)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd) if cwd else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError("Render subprocess timed out")

    stdout = stdout_bytes.decode(errors="ignore") if stdout_bytes else ""
    stderr = stderr_bytes.decode(errors="ignore") if stderr_bytes else ""
    return proc.returncode, stdout, stderr


async def render_scene_dict(scene: Dict[str, Any], job_id: Optional[str] = None, timeout: int = 300) -> Path:
    """
    Main entrypoint: takes a scene dict, generates TSX, runs Remotion render, returns Path to MP4.

    Args:
        scene: scene JSON as Python dict (matching the schema)
        job_id: optional job identifier (used to name output file). If not provided, a uuid will be used.
        timeout: seconds to wait for the render subprocess

    Returns:
        Path to generated mp4 (absolute)
    """
    job_id = job_id or str(uuid.uuid4())
    # 1) Write scene JSON to storage (helpful for debugging)
    scene_path = settings.BASE_DIR / "storage" / "scenes"
    scene_path.mkdir(parents=True, exist_ok=True)
    scene_file = scene_path / f"{job_id}.json"
    scene_file.write_text(json.dumps(scene, indent=2), encoding="utf-8")
    logger.info("Wrote scene JSON: %s", scene_file)

    # 2) Ensure assets are available
    await _ensure_assets(scene)
    logger.info("Ensured assets are available")

    # 3) Save scene JSON for Remotion
    scene_config_path = settings.REMOTION_DIR / "scene_config.json"
    scene_config_path.write_text(json.dumps(scene, indent=2), encoding="utf-8")
    logger.info("Saved scene config at: %s", scene_config_path)

    # 4) Ensure outputs dir exists
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_mp4 = settings.OUTPUT_DIR / f"{job_id}.mp4"

    # 5) Build command to call the remotion render script (node <script> --config <scene_config_path>)
    remotion_script = settings.REMOTION_SCRIPT
    if not remotion_script.exists():
        raise FileNotFoundError(f"Remotion render script not found: {remotion_script}")

    cmd = ["node", str(remotion_script), "--config", str(scene_config_path), "--out", str(out_mp4)]

    # The render script expects to be called from the remotion project directory
    remotion_cwd = settings.REMOTION_DIR

    # 5) Run subprocess (with timeout)
    rc, stdout, stderr = await _run_subprocess(cmd, cwd=remotion_cwd, timeout=timeout)
    logger.info("Render exited with code %s", rc)
    if stdout:
        logger.info("Render stdout: %s", stdout[:2000])  # truncate in logs
    if stderr:
        logger.error("Render stderr: %s", stderr[:2000])

    if rc != 0 or not out_mp4.exists():
        raise RuntimeError(f"Render failed (rc={rc}). stderr: {stderr[:2000]}")

    logger.info("Render succeeded, output: %s", out_mp4_abs)
    return out_mp4_abs


# Convenience sync wrapper (if you want to call from sync code)
def render_scene_dict_sync(scene: Dict[str, Any], job_id: Optional[str] = None, timeout: int = 300) -> Path:
    return asyncio.get_event_loop().run_until_complete(render_scene_dict(scene, job_id=job_id, timeout=timeout))
