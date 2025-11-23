# app/services/remotion_executor.py
import subprocess
import uuid
from pathlib import Path
from ..core.config import settings
import shutil

class RemotionExecutor:
    def __init__(self):
        self.remotion_dir = settings.REMOTION_DIR
        self.script = self.remotion_dir / "scripts" / "render.js"
        settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg","-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except Exception:
            raise RuntimeError("FFmpeg not found")

    def render_sync(self, comp_id: str = "Main", job_id: str = None) -> tuple:
        job_id = job_id or str(uuid.uuid4())
        out = settings.OUTPUT_DIR / f"{job_id}.mp4"
        self._check_ffmpeg()
        cmd = ["node", str(self.script), "--config", str(settings.BASE_DIR / "jobs" / f"{job_id}_dsl.json"), "--out", str(out), "--comp", comp_id]
        proc = subprocess.Popen(cmd, cwd=self.remotion_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate()
        logs = stdout + "\n" + stderr
        if proc.returncode != 0:
            return False, None, logs
        if not out.exists():
            return False, None, "Render finished but output missing"
        return True, out.resolve(), logs

remotion_executor = RemotionExecutor()