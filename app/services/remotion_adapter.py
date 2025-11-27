# app/services/remotion_adapter.py
import subprocess
from pathlib import Path
from app.core.config import settings
from app.services.errors import RenderError
import shlex
import subprocess

REMOTION_ROOT = settings.REMOTION_DIR

def render_remotion(composition_id: str, output_path: str, job_dir: str) -> None:
    """
    Deterministically renders a Remotion composition with proper registration and build.

    Args:
        composition_id: Unique identifier for the composition (e.g., "Scene_abcd1234")
        output_path: Path to output video file
        job_dir: Relative path to job directory containing GeneratedScene.tsx
    """
    # Step 1: Register the generated component in index.tsx
    index_path = REMOTION_ROOT / "src" / "index.tsx"
    index_content = index_path.read_text(encoding="utf-8")

    # Check if composition is already registered
    if f'id="{composition_id}"' not in index_content:
        # Add import
        import_line = f'import {{ default as {composition_id} }} from "./generated/{job_dir}/GeneratedScene";\n'
        # Insert after MainVideo import
        import_insert_point = index_content.find('import { MainVideo } from "./MainVideo";')
        if import_insert_point != -1:
            import_insert_point += len('import { MainVideo } from "./MainVideo";\n')
            index_content = index_content[:import_insert_point] + import_line + index_content[import_insert_point:]

        # Add composition
        composition_block = f'''
    <Composition
      key="{composition_id}"
      id="{composition_id}"
      component={{{composition_id}}}
      width={{1920}}
      height={{1080}}
      fps={{30}}
      durationInFrames={{30 * 5}}
      defaultProps={{{{}}}}
    />
'''
        # Insert before the closing </> of compositions
        compositions_end = index_content.find('  return <>{compositions}</>;')
        if compositions_end != -1:
            index_content = index_content[:compositions_end] + composition_block + index_content[compositions_end:]

        # Write back
        index_path.write_text(index_content, encoding="utf-8")

    # Step 2: Ensure build includes the new component
    build_cmd = f"npm run build -- --quiet"
    build_proc = subprocess.run(build_cmd, shell=True, cwd=str(REMOTION_ROOT))
    if build_proc.returncode != 0:
        raise RenderError(f"Remotion build failed (code={build_proc.returncode}). Command: {build_cmd}")

    # Step 3: Render the specific composition
    script = REMOTION_ROOT / "scripts" / "render.js"
    if script.exists():
        render_cmd = f"node {shlex.quote(str(script))} --comp {shlex.quote(composition_id)} --out {shlex.quote(output_path)}"
    else:
        # Fallback to direct remotion command
        render_cmd = f"{settings.REMOTION_CMD} render src/index.tsx {composition_id} --codec h264 --output {shlex.quote(output_path)} --overwrite"

    render_proc = subprocess.run(render_cmd, shell=True, cwd=str(REMOTION_ROOT))
    if render_proc.returncode != 0:
        raise RenderError(f"Remotion render failed (code={render_proc.returncode}). Command: {render_cmd}")