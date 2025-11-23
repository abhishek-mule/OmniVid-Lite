from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

class AnimationType(str, Enum):
    FADE_IN = "fade-in"
    FADE_OUT = "fade-out"
    SLIDE_UP = "slide-up"
    SLIDE_DOWN = "slide-down"
    SLIDE_LEFT = "slide-left"
    SLIDE_RIGHT = "slide-right"
    ZOOM_IN = "zoom-in"
    ZOOM_OUT = "zoom-out"

class EasingType(str, Enum):
    EASE = "ease"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    LINEAR = "linear"

class AnimationConfig(BaseModel):
    type: AnimationType
    from_frame: int = Field(..., alias="from")
    to_frame: int = Field(..., alias="to")
    easing: EasingType = EasingType.EASE_OUT
    distance: Optional[float] = None
    scale: Optional[float] = None

class LayerBase(BaseModel):
    id: str
    type: str
    style: Dict[str, Any] = {}
    transform: Dict[str, Any] = {}
    animation: Optional[Dict[Literal["in", "out"], Optional[Dict[str, Any]]]] = None
    start_frame: int = 0
    end_frame: Optional[int] = None

class TextLayer(LayerBase):
    type: Literal["text"] = "text"
    content: str
    style: Dict[str, Any] = {
        "color": "white",
        "fontSize": 40,
        "fontFamily": "Arial, sans-serif"
    }

class ShapeLayer(LayerBase):
    type: Literal["shape"] = "shape"
    shapeType: Literal["rectangle", "circle", "triangle"]
    style: Dict[str, Any] = {
        "backgroundColor": "#ffffff"
    }

class ImageLayer(LayerBase):
    type: Literal["image"] = "image"
    src: str
    alt: str = ""

class VideoLayer(LayerBase):
    type: Literal["video"] = "video"
    src: str
    loop: bool = True

Layer = Union[TextLayer, ShapeLayer, ImageLayer, VideoLayer]

class Scene(BaseModel):
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: int  # in frames
    background: str = "#000000"
    layers: List[Layer] = []
    metadata: Dict[str, Any] = {}

    @validator('layers')
    def validate_layers(cls, v):
        # Ensure all layer IDs are unique
        layer_ids = [layer.id for layer in v]
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("All layer IDs must be unique")
        return v

    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Get a layer by its ID."""
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        return None
