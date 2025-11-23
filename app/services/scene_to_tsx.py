# app/services/scene_to_tsx.py
import json
from pathlib import Path
from ..core.config import settings
import shutil
import requests

PUBLIC = settings.REMOTION_DIR / "public"
PUBLIC.mkdir(parents=True, exist_ok=True)

def _fetch_asset(url: str) -> str:
    # returns local public path (relative)
    fname = Path(url).name
    dest = PUBLIC / fname
    if url.startswith("http"):
        r = requests.get(url, stream=True, timeout=15)
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(1024*8):
                fh.write(chunk)
    else:
        src = Path(url)
        if src.exists():
            shutil.copy(src, dest)
    return f"/public/{fname}"

def generate_remotion_from_dsl(dsl: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    # 1) write a simple generated Scene.tsx which imports MotionEngine and passes the DSL as a JSON prop
    scene_path = out_dir / "Scene.tsx"
    # copy assets and rewrite URLs
    for scene in dsl.get("scenes", []):
        for layer in scene.get("layers", []):
            if layer.get("type") == "image":
                url = layer.get("url")
                if url:
                    local = _fetch_asset(url)
                    layer["url"] = local
    # Save the rewritten DSL into generated folder for MotionEngine to import
    dsl_file = out_dir / "dsl.json"
    dsl_file.write_text(json.dumps(dsl, indent=2), encoding="utf-8")

    # Scene.tsx: simple loader that imports MotionEngine
    tsx = f"""
import React from 'react';
import MotionEngine from '../MotionEngine';
import dsl from './dsl.json';

export const GeneratedScene = () => {{
  return <MotionEngine dsl={{dsl}} />;
}};

export default GeneratedScene;
"""
    scene_path.write_text(tsx, encoding="utf-8")

    # 2) Build MainVideo.tsx that wraps GeneratedScene composition as Main
    main_path = settings.REMOTION_DIR / "src" / "MainVideo.tsx"
    main_tsx = """
import React from 'react';
import { GeneratedScene } from './generated/Scene';

export const MainVideo = (props) => {
  return <GeneratedScene />;
};

export default MainVideo;
"""
    main_path.write_text(main_tsx, encoding="utf-8")