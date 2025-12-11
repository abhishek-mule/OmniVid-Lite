"""
Simple video renderer for OmniVid Lite MVP.

Replaces complex Remotion/React approach with basic Python video generation.
Creates simple text animations using OpenCV and Pillow.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Callable
import cv2
import numpy as np

# Try to import PIL, fallback to OpenCV-only rendering if not available
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("WARNING: Pillow not available, using OpenCV-only text rendering")

logger = logging.getLogger(__name__)


class EnhancedVideoRenderer:
    """Enhanced video renderer with advanced text effects and motion graphics."""

    def __init__(self, width=1920, height=1080, fps=30, duration=5):
        self.font_path = self._find_font()
        self.width = width
        self.height = height
        self.fps = fps
        self.duration = duration
        self.total_frames = int(duration * fps)

        # Animation parameters
        self.animation_style = 'fade'  # fade, slide, bounce, typewriter, color_wave
        self.visual_style = 'minimal'  # minimal, vibrant, cinematic, abstract
        self.text_animation = 'fade'  # fade, slide, bounce, typewriter

    def set_parameters(self, duration=None, resolution=None, style=None, animation=None):
        """Set video generation parameters."""
        if duration:
            self.duration = duration
            self.total_frames = int(duration * self.fps)

        if resolution:
            if resolution == '720p':
                self.width, self.height = 1280, 720
            elif resolution == '1080p':
                self.width, self.height = 1920, 1080
            elif resolution == '4k':
                self.width, self.height = 3840, 2160

        if style:
            self.visual_style = style

        if animation:
            self.text_animation = animation

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

    def create_background(self, frame_number: int) -> np.ndarray:
        """Create animated background based on visual style."""
        if self.visual_style == 'minimal':
            # Clean black background
            return np.zeros((self.height, self.width, 3), dtype=np.uint8)

        elif self.visual_style == 'vibrant':
            # Color gradient background
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            # Create a moving color gradient
            time_factor = frame_number / self.total_frames
            for y in range(self.height):
                for x in range(self.width):
                    r = int(128 + 127 * np.sin(time_factor * 4 + x * 0.01))
                    g = int(128 + 127 * np.sin(time_factor * 4 + y * 0.01 + 2))
                    b = int(128 + 127 * np.sin(time_factor * 4 + (x + y) * 0.005 + 4))
                    frame[y, x] = [r, g, b]
            return frame

        elif self.visual_style == 'cinematic':
            # Dark cinematic look with subtle animation
            base_color = 20  # Very dark
            frame = np.full((self.height, self.width, 3), base_color, dtype=np.uint8)
            # Add subtle vignette effect
            center_y, center_x = self.height // 2, self.width // 2
            y_coords, x_coords = np.ogrid[:self.height, :self.width]
            dist_from_center = np.sqrt((y_coords - center_y)**2 + (x_coords - center_x)**2)
            max_dist = np.sqrt(center_y**2 + center_x**2)
            vignette = 1 - (dist_from_center / max_dist) * 0.3
            frame = (frame * vignette[:, :, np.newaxis]).astype(np.uint8)
            return frame

        elif self.visual_style == 'abstract':
            # Abstract geometric patterns
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            time_factor = frame_number / self.total_frames

            # Create moving geometric shapes
            for i in range(5):
                center_x = int(self.width * (0.2 + 0.6 * np.sin(time_factor * 2 + i)))
                center_y = int(self.height * (0.2 + 0.6 * np.cos(time_factor * 1.5 + i)))
                radius = int(50 + 30 * np.sin(time_factor * 3 + i))
                color = [int(100 + 155 * np.sin(time_factor + i)),
                        int(100 + 155 * np.sin(time_factor + i + 2)),
                        int(100 + 155 * np.sin(time_factor + i + 4))]
                cv2.circle(frame, (center_x, center_y), radius, color, -1)

            return frame

        else:
            return np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def apply_text_animation(self, text: str, frame_number: int, base_frame: np.ndarray) -> np.ndarray:
        """Apply text animation effects based on animation style."""
        frame = base_frame.copy()

        if not HAS_PILLOW:
            return self._apply_opencv_text_animation(text, frame_number, frame)

        # Use PIL for better text rendering
        pil_image = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_image)

        # Load font
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, 100 if self.visual_style == 'cinematic' else 80)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Animation progress (0 to 1)
        progress = frame_number / self.total_frames

        if self.text_animation == 'fade':
            # Fade in/out effect
            fade_frames = int(0.5 * self.fps)
            if frame_number < fade_frames:
                alpha = frame_number / fade_frames
            elif frame_number > self.total_frames - fade_frames:
                alpha = (self.total_frames - frame_number) / fade_frames
            else:
                alpha = 1.0

            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2
            color = self._get_text_color(alpha)
            draw.text((x, y), text, fill=color, font=font)

        elif self.text_animation == 'slide':
            # Slide in from left
            slide_frames = int(0.8 * self.fps)
            if frame_number < slide_frames:
                slide_progress = frame_number / slide_frames
                x = int(-text_width + (self.width // 2 + text_width // 2) * slide_progress)
            else:
                x = (self.width - text_width) // 2

            y = (self.height - text_height) // 2
            alpha = 1.0
            color = self._get_text_color(alpha)
            draw.text((x, y), text, fill=color, font=font)

        elif self.text_animation == 'bounce':
            # Bouncing text effect
            bounce_frames = int(0.6 * self.fps)
            if frame_number < bounce_frames:
                bounce_progress = frame_number / bounce_frames
                # Create a bouncing effect using sine wave
                bounce_offset = int(50 * np.sin(bounce_progress * np.pi * 4) * (1 - bounce_progress))
                y = (self.height - text_height) // 2 + bounce_offset
            else:
                y = (self.height - text_height) // 2

            x = (self.width - text_width) // 2
            alpha = 1.0
            color = self._get_text_color(alpha)
            draw.text((x, y), text, fill=color, font=font)

        elif self.text_animation == 'typewriter':
            # Typewriter effect
            type_frames = int(2.0 * self.fps)  # 2 seconds for typing
            if frame_number < type_frames:
                chars_to_show = int((frame_number / type_frames) * len(text))
                display_text = text[:chars_to_show]
            else:
                display_text = text

            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2
            alpha = 1.0
            color = self._get_text_color(alpha)
            draw.text((x, y), display_text, fill=color, font=font)

        else:  # Default fade
            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2
            alpha = 1.0
            color = self._get_text_color(alpha)
            draw.text((x, y), text, fill=color, font=font)

        return np.array(pil_image)

    def _get_text_color(self, alpha: float) -> tuple:
        """Get text color based on visual style."""
        if self.visual_style == 'minimal':
            return tuple(int(255 * alpha) for _ in range(3))
        elif self.visual_style == 'vibrant':
            return (int(255 * alpha), int(200 * alpha), int(100 * alpha))  # Orange tint
        elif self.visual_style == 'cinematic':
            return (int(220 * alpha), int(220 * alpha), int(255 * alpha))  # Slight blue tint
        elif self.visual_style == 'abstract':
            return (int(255 * alpha), int(255 * alpha), int(255 * alpha))  # White
        else:
            return tuple(int(255 * alpha) for _ in range(3))

    def _apply_opencv_text_animation(self, text: str, frame_number: int, frame: np.ndarray) -> np.ndarray:
        """Fallback OpenCV text animation."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 3
        thickness = 4

        # Simple fade effect
        fade_frames = int(0.5 * self.fps)
        if frame_number < fade_frames:
            alpha = frame_number / fade_frames
        elif frame_number > self.total_frames - fade_frames:
            alpha = (self.total_frames - frame_number) / fade_frames
        else:
            alpha = 1.0

        color = (int(255 * alpha), int(255 * alpha), int(255 * alpha))

        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

        # Center text
        x = (self.width - text_width) // 2
        y = (self.height + text_height) // 2

        # Draw text
        cv2.putText(frame, text, (x, y), font, font_scale, color, thickness)

        return frame

    def create_text_frame(self, text: str, frame_number: int) -> np.ndarray:
        """Create a single frame with text overlay and background."""
        # Create animated background
        frame = self.create_background(frame_number)

        # Apply text animation
        frame = self.apply_text_animation(text, frame_number, frame)

        return frame


    def create_text_video(self, text: str, output_path: str, progress_callback: Optional[Callable] = None) -> str:
        """
        Create an enhanced text-to-video with advanced effects.

        Args:
            text: The text to animate
            output_path: Where to save the MP4 file
            progress_callback: Optional callback for progress updates (0-100)

        Returns:
            Path to the created video file
        """
        try:
            logger.info(f"Starting enhanced video render for text: '{text}' with style: {self.visual_style}, animation: {self.text_animation}")

            # Update progress
            if progress_callback:
                progress_callback(10)
                logger.info("Video render: 10% - Initializing enhanced renderer")

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))

            if not video_writer.isOpened():
                raise Exception("Failed to initialize video writer")

            # Update progress
            if progress_callback:
                progress_callback(20)
                logger.info("Video render: 20% - Video writer initialized")

            # Generate frames with enhanced effects
            for frame_num in range(self.total_frames):
                # Create frame with enhanced text animation and background
                frame = self.create_text_frame(text, frame_num)

                # Write frame
                video_writer.write(frame)

                # Update progress
                if progress_callback and frame_num % (self.total_frames // 10) == 0:
                    progress = 20 + int((frame_num / self.total_frames) * 70)
                    progress_callback(progress)
                    logger.info(f"Video render: {progress}% - Rendering frame {frame_num}/{self.total_frames}")

            # Update progress
            if progress_callback:
                progress_callback(90)
                logger.info("Video render: 90% - Finalizing enhanced video")

            # Release video writer
            video_writer.release()

            # Update progress
            if progress_callback:
                progress_callback(100)
                logger.info("Video render: 100% - Enhanced video rendering complete")

            logger.info(f"Enhanced video successfully created: {output_path} ({self.width}x{self.height}, {self.duration}s, {self.fps}fps)")

            return output_path

        except Exception as e:
            logger.error(f"Enhanced video rendering failed: {e}")
            raise Exception(f"Failed to create enhanced video: {str(e)}")


def create_enhanced_text_video(text: str, output_path: str, progress_callback: Optional[Callable] = None,
                              duration: int = 5, resolution: str = '1080p',
                              style: str = 'minimal', animation: str = 'fade') -> str:
    """
    Convenience function to create an enhanced text video with customizable parameters.

    Args:
        text: The prompt text
        output_path: Output file path
        progress_callback: Optional progress callback
        duration: Video duration in seconds (3-15)
        resolution: Video resolution ('720p', '1080p', '4k')
        style: Visual style ('minimal', 'vibrant', 'cinematic', 'abstract')
        animation: Text animation style ('fade', 'slide', 'bounce', 'typewriter')

    Returns:
        Path to created video
    """
    renderer = EnhancedVideoRenderer()
    renderer.set_parameters(duration=duration, resolution=resolution, style=style, animation=animation)
    return renderer.create_text_video(text, output_path, progress_callback)


def create_scene_based_video(scene_dsl: dict, output_path: str, progress_callback: Optional[Callable] = None,
                           duration: int = 5, resolution: str = '1080p',
                           style: str = 'minimal', animation: str = 'fade') -> str:
    """
    Create a video based on AI-generated scene DSL with multiple layers and effects.

    Args:
        scene_dsl: AI-generated scene description in DSL format
        output_path: Output file path
        progress_callback: Optional progress callback
        duration: Override duration from DSL
        resolution: Video resolution
        style: Visual style override
        animation: Animation style override

    Returns:
        Path to created video
    """
    renderer = SceneBasedRenderer()
    renderer.set_parameters(duration=duration, resolution=resolution, style=style, animation=animation)
    return renderer.create_scene_video(scene_dsl, output_path, progress_callback)


class SceneBasedRenderer(EnhancedVideoRenderer):
    """Renderer for AI-generated scene DSL with multiple layers and effects."""

    def create_scene_video(self, scene_dsl: dict, output_path: str, progress_callback: Optional[Callable] = None) -> str:
        """
        Create video from scene DSL with multiple scenes, layers, and effects.
        """
        try:
            logger.info(f"Starting scene-based video render with DSL: {scene_dsl.keys()}")

            # Update progress
            if progress_callback:
                progress_callback(10)
                logger.info("Scene render: 10% - Initializing scene renderer")

            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))

            if not video_writer.isOpened():
                raise Exception("Failed to initialize video writer")

            # Update progress
            if progress_callback:
                progress_callback(20)
                logger.info("Scene render: 20% - Video writer initialized")

            # Process each scene in the DSL
            scenes = scene_dsl.get('scenes', [])
            if not scenes:
                # Fallback: create a simple scene from metadata
                scenes = [self._create_fallback_scene(scene_dsl)]

            total_frames = self.total_frames
            frame_num = 0

            while frame_num < total_frames:
                # Determine which scene this frame belongs to
                scene_frame = frame_num
                current_scene = scenes[0]  # For now, use first scene

                # Create frame for current scene
                frame = self.create_scene_frame(current_scene, scene_frame, current_scene.get('duration', self.duration))

                # Write frame
                video_writer.write(frame)

                frame_num += 1

                # Update progress
                if progress_callback and frame_num % (total_frames // 10) == 0:
                    progress = 20 + int((frame_num / total_frames) * 70)
                    progress_callback(progress)
                    logger.info(f"Scene render: {progress}% - Rendering frame {frame_num}/{total_frames}")

            # Update progress
            if progress_callback:
                progress_callback(90)
                logger.info("Scene render: 90% - Finalizing scene video")

            # Release video writer
            video_writer.release()

            # Update progress
            if progress_callback:
                progress_callback(100)
                logger.info("Scene render: 100% - Scene-based video rendering complete")

            logger.info(f"Scene-based video successfully created: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Scene-based video rendering failed: {e}")
            raise Exception(f"Failed to create scene-based video: {str(e)}")

    def _create_fallback_scene(self, scene_dsl: dict) -> dict:
        """Create a fallback scene when DSL doesn't have scenes."""
        return {
            'id': 'fallback',
            'duration': scene_dsl.get('metadata', {}).get('duration', self.duration),
            'background': scene_dsl.get('metadata', {}).get('background', '#000000'),
            'layers': [{
                'type': 'text',
                'id': 'fallback_text',
                'content': scene_dsl.get('text', 'Generated Video'),
                'style': {
                    'color': scene_dsl.get('metadata', {}).get('text_color', '#ffffff'),
                    'font_size': scene_dsl.get('metadata', {}).get('font_size', 48)
                },
                'animation': {'type': 'fade'}
            }]
        }

    def create_scene_frame(self, scene: dict, frame_number: int, scene_duration: float) -> np.ndarray:
        """Create a frame for a specific scene with all its layers."""
        # Start with background
        background_color = scene.get('background', '#000000')
        frame = self._hex_to_bgr(background_color)

        # Apply scene-specific background effects
        frame = self.apply_scene_background_effects(frame, scene, frame_number)

        # Render each layer
        layers = scene.get('layers', [])
        for layer in layers:
            frame = self.render_layer(frame, layer, frame_number, scene_duration)

        return frame

    def apply_scene_background_effects(self, frame: np.ndarray, scene: dict, frame_number: int) -> np.ndarray:
        """Apply background effects like gradients, particles, etc."""
        # For now, just return the base frame
        # Could be extended with particle systems, gradients, etc.
        return frame

    def render_layer(self, frame: np.ndarray, layer: dict, frame_number: int, scene_duration: float) -> np.ndarray:
        """Render a single layer onto the frame."""
        layer_type = layer.get('type', 'text')

        if layer_type == 'text':
            return self.render_text_layer(frame, layer, frame_number, scene_duration)
        elif layer_type == 'image':
            return self.render_image_layer(frame, layer, frame_number, scene_duration)
        elif layer_type == 'shape':
            return self.render_shape_layer(frame, layer, frame_number, scene_duration)
        else:
            logger.warning(f"Unknown layer type: {layer_type}")
            return frame

    def render_text_layer(self, frame: np.ndarray, layer: dict, frame_number: int, scene_duration: float) -> np.ndarray:
        """Render a text layer with animations."""
        content = layer.get('content', 'Text')
        style = layer.get('style', {})
        animation = layer.get('animation', {})

        # Convert frame to PIL for text rendering
        pil_image = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_image)

        # Load font
        try:
            font_size = style.get('font_size', 48)
            if self.font_path:
                font = ImageFont.truetype(self.font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # Get text dimensions
        bbox = draw.textbbox((0, 0), content, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position and animation
        x, y = self.calculate_text_position(layer, frame_number, scene_duration, text_width, text_height)

        # Get color
        color_hex = style.get('color', '#ffffff')
        color_rgb = self._hex_to_rgb(color_hex)

        # Apply animation effects
        alpha = self.calculate_layer_alpha(layer, frame_number, scene_duration)
        color_rgba = (*color_rgb, int(255 * alpha))

        # Draw text
        draw.text((x, y), content, fill=color_rgba, font=font)

        return np.array(pil_image)

    def calculate_text_position(self, layer: dict, frame_number: int, scene_duration: float,
                              text_width: int, text_height: int) -> tuple:
        """Calculate text position with animation."""
        transform = layer.get('transform', {})
        position = transform.get('position', 'center')

        base_x = (self.width - text_width) // 2
        base_y = (self.height - text_height) // 2

        # Apply animation
        animation = layer.get('animation', {})
        anim_type = animation.get('type', 'static')

        if anim_type == 'slide':
            progress = frame_number / (scene_duration * self.fps)
            if position == 'left':
                base_x = int(-text_width + (self.width // 2 + text_width // 2) * progress)
            elif position == 'right':
                base_x = int(self.width - (self.width // 2 + text_width // 2) * progress)

        elif anim_type == 'bounce':
            progress = frame_number / (scene_duration * self.fps)
            bounce_offset = int(50 * np.sin(progress * np.pi * 4) * (1 - progress))
            base_y += bounce_offset

        return base_x, base_y

    def calculate_layer_alpha(self, layer: dict, frame_number: int, scene_duration: float) -> float:
        """Calculate layer opacity for fade effects."""
        animation = layer.get('animation', {})
        anim_type = animation.get('type', 'static')

        if anim_type == 'fade':
            total_frames = scene_duration * self.fps
            fade_frames = int(0.5 * self.fps)  # 0.5 second fade

            if frame_number < fade_frames:
                return frame_number / fade_frames
            elif frame_number > total_frames - fade_frames:
                return (total_frames - frame_number) / fade_frames
            else:
                return 1.0

        return 1.0

    def render_image_layer(self, frame: np.ndarray, layer: dict, frame_number: int, scene_duration: float) -> np.ndarray:
        """Render an image layer (placeholder for future implementation)."""
        # For now, just return the frame unchanged
        # Could be extended to load and composite images
        return frame

    def render_shape_layer(self, frame: np.ndarray, layer: dict, frame_number: int, scene_duration: float) -> np.ndarray:
        """Render a shape layer (placeholder for future implementation)."""
        # For now, just return the frame unchanged
        # Could be extended to draw geometric shapes
        return frame

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _hex_to_bgr(self, hex_color: str) -> np.ndarray:
        """Convert hex color to BGR frame."""
        r, g, b = self._hex_to_rgb(hex_color)
        return np.full((self.height, self.width, 3), (b, g, r), dtype=np.uint8)


# Backward compatibility
def create_text_video(text: str, output_path: str, progress_callback: Optional[Callable] = None) -> str:
    """
    Legacy convenience function for basic text video creation.
    """
    return create_enhanced_text_video(text, output_path, progress_callback)


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
