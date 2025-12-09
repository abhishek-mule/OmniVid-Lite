# app/services/remotion_adapter.py
import subprocess
from pathlib import Path
from app.core.config import settings
from app.services.errors import RenderError

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
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={150}
      defaultProps={{{{}}}}
    />
'''
        # Insert before the closing </> of compositions
        compositions_end = index_content.find('  return <>{compositions}</>;')
        if compositions_end != -1:
            index_content = index_content[:compositions_end] + composition_block + index_content[compositions_end:]

        # Write back
        index_path.write_text(index_content, encoding="utf-8")

    # Step 2: Skip build - render script handles bundling

    # Step 3: Render the specific composition
    script = REMOTION_ROOT / "scripts" / "render.js"
    if script.exists() and script.is_file():
        # Use the Node.js render script with the composition name
        config_file = Path(output_path).parent / "dsl.json"
        # render.js expects either --config or --comp, we're using --comp
        render_cmd = f'node "{script}" --comp {composition_id} --out "{output_path}"'
    else:
        # Fallback to direct remotion command
        render_cmd = f'npx remotion render "src/index.tsx" {composition_id} --codec h264 --output "{output_path}" --overwrite'

    try:
        render_proc = subprocess.run(
            render_cmd,
            cwd=str(REMOTION_ROOT),
            timeout=settings.REMOTION_TIMEOUT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            shell=True
        )
        if render_proc.returncode != 0:
            error_msg = f"Remotion render failed (code={render_proc.returncode})"
            if render_proc.stderr:
                error_msg += f"\nSTDERR: {render_proc.stderr}"
            if render_proc.stdout:
                error_msg += f"\nSTDOUT: {render_proc.stdout}"
            raise RenderError(error_msg)
    except subprocess.TimeoutExpired:
        raise RenderError(f"Remotion render timed out after {settings.REMOTION_TIMEOUT} seconds")
    except FileNotFoundError as e:
        raise RenderError(f"Remotion command not found: {settings.REMOTION_CMD} - {e}")
