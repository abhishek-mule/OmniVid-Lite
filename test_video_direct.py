#!/usr/bin/env python3
"""
Direct video generation test without Redis/database dependencies.
Bypasses the normal job queue to directly generate a video.
"""

import asyncio
import json
import os
from pathlib import Path

# Mock some dependencies to avoid Redis/DB requirements
class MockJob:
    def __init__(self, prompt):
        self.id = "direct_test_job"
        self.prompt = prompt

async def generate_video_direct(prompt: str):
    """Direct video generation bypassing job queue"""

    from app.services.scene_to_tsx import scene_to_tsx
    from app.services.remotion_adapter import render_remotion

    print(f"🎬 Starting direct video generation for: '{prompt}'")

    job = MockJob(prompt)
    job_dir = Path("remotion_engine/src/generated") / job.id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Use mock scene JSON (skip LLM for now)
        print("🤖 Using mock scene description...")
        dsl = {
            "metadata": {
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "duration": 150,
                "style": "minimal"
            },
            "scenes": [
                {
                    "id": "scene1",
                    "duration": 150,
                    "background": {"type": "color", "color": "#ffffff"},
                    "layers": [
                        {
                            "type": "circle",
                            "id": "blue_circle",
                            "content": {},
                            "style": {
                                "fill": "#3b82f6",
                                "width": 100,
                                "height": 100
                            },
                            "transform": {"x": 0, "y": 540},
                            "animation": {
                                "duration": 150,
                                "from": {"x": 0},
                                "to": {"x": 1820}
                            },
                            "effects": []
                        }
                    ]
                }
            ]
        }
        print(f"✅ Mock scene JSON generated with {len(str(dsl))} characters")

        # Save DSL to job directory
        dsl_path = job_dir / "scene.json"
        dsl_path.write_text(json.dumps(dsl, indent=2), encoding="utf-8")
        print(f"💾 Scene JSON saved to {dsl_path}")

        # Step 2: Generate Remotion TSX file
        print("⚛️ Generating TSX component...")
        tsx_path = job_dir / "GeneratedScene.tsx"
        scene_to_tsx(str(dsl_path), str(tsx_path))
        print(f"✅ TSX component generated: {tsx_path}")

        # Step 3: Render video with Remotion
        print("🎥 Rendering video with Remotion...")
        output_file = Path("remotion_engine/outputs") / f"{job.id}.mp4"
        output_file.parent.mkdir(exist_ok=True)

        success, output_path, logs = await asyncio.to_thread(
            render_remotion, "GeneratedScene", str(output_file), job.id
        )

        if success:
            print(f"🎉 Video rendered successfully!")
            print(f"📁 Output file: {output_path}")
            return output_path
        else:
            print(f"❌ Rendering failed: {logs}")
            return None

    except Exception as e:
        print(f"❌ Error during video generation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test prompt for video generation
    prompt = "A blue circle moves from left to right on a white background for 5 seconds"

    asyncio.run(generate_video_direct(prompt))
