"""
Simple video renderer for OmniVid Lite MVP.

Replaces complex Remotion/React approach with basic Python video generation.
Creates simple text animations using MoviePy and Pillow.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Callable
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mp
import numpy as np

logger = logging.getLogger(__name__)


class SimpleVideoRenderer:
    """Simple video renderer for text-to-video generation."""

    def __init__(self):
        self.font_path = self._find_font()
        self.width = 1920
        self.height = 1080
        self.fps = 30
        self.duration = 5  # seconds

    def _find_font(self) -> Optional[str]:
        """Find a system font for text rendering."""
        # Try common font paths
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "C:/Windows/Fonts/arial.ttf",  # Windows
            "C:/Windows/Fonts/Arial.ttf",  # Windows alt
        ]

        for font_path in font_candidates:
            if os.path.exists(font_path):
                return font_path

        logger.warning("No system font found, using default")
        return None

    def create_text_clip(self, text: str, start_time: float = 1.0, duration: float = 3.0) -> mp.TextClip:
        """Create a text clip with fade in/out animation."""
        try:
            # Create text clip
            txt_clip = mp.TextClip(
                text,
                fontsize=80,
                color='white',
                bg_color='black',
                size=(self.width, self.height),
                font=self.font_path or 'Arial-Bold'
            ).set_position('center').set_duration(duration)

            # Add fade in/out
            txt_clip = txt_clip.fadein(0.5).fadeout(0.5)

            # Set start time
            txt_clip = txt_clip.set_start(start_time)

            return txt_clip

        except Exception as e:
            logger.error(f"Failed to create text clip: {e}")
            # Fallback to simple text
            return mp.TextClip(
                text,
                fontsize=60,
                color='white'
            ).set_position('center').set_duration(duration).set_start(start_time)

    def create_background_clip(self) -> mp.ColorClip:
        """Create a background clip."""
        return mp.ColorClip(
            size=(self.width, self.height),
            color=(0, 0, 0),  # Black background
            duration=self.duration
        )

    def create_text_video(self, text: str, output_path: str, progress_callback: Optional[Callable] = None) -> str:
        """
        Create a simple text-to-video.

        Args:
            text: The text to animate
            output_path: Where to save the MP4 file
            progress_callback: Optional callback for progress updates (0-100)

        Returns:
            Path to the created video file
        """
        try:
            logger.info(f"Starting video render for text: '{text}'")

            # Update progress
            if progress_callback:
                progress_callback(10)
                logger.info("Video render: 10% - Initializing")

            # Create background
            background = self.create_background_clip()

            # Update progress
            if progress_callback:
                progress_callback(30)
                logger.info("Video render: 30% - Created background")

            # Create text clip
            text_clip = self.create_text_clip(text)

            # Update progress
            if progress_callback:
                progress_callback(60)
                logger.info("Video render: 60% - Created text animation")

            # Composite clips
            final_clip = mp.CompositeVideoClip([background, text_clip])

            # Update progress
            if progress_callback:
                progress_callback(80)
                logger.info("Video render: 80% - Compositing video")

            # Export to MP4
            final_clip.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec=None,  # No audio
                verbose=False,
                logger=None
            )

            # Update progress
            if progress_callback:
                progress_callback(100)
                logger.info("Video render: 100% - Video rendering complete")

            final_clip.close()
            logger.info(f"Video successfully created: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Video rendering failed: {e}")
            raise Exception(f"Failed to create video: {str(e)}")


def create_text_video(text: str, output_path: str, progress_callback: Optional[Callable] = None) -> str:
    """
    Convenience function to create a text video.

    Args:
        text: The prompt text
        output_path: Output file path
        progress_callback: Optional progress callback

    Returns:
        Path to created video
    """
    renderer = SimpleVideoRenderer()
    return renderer.create_text_video(text, output_path, progress_callback)


# For testing
if __name__ == "__main__":
    # Test the renderer
    renderer = SimpleVideoRenderer()
    output_path = "test_output.mp4"

    def progress_callback(progress: int):
        print(f"Progress: {progress}%")

    try:
        result = renderer.create_text_video("Hello from OmniVid MVP!", output_path, progress_callback)
        print(f"Video created successfully: {result}")
    except Exception as e:
        print(f"Failed to create video: {e}")
