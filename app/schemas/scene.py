from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional, Union, Literal, Dict, Any


class AnimationSpec(BaseModel):
    type: Literal["fade-in", "fade-out", "slide-up", "slide-down", "slide-left", "slide-right", "zoom-in", "zoom-out", "rotate"]
    from_frame: Optional[int] = Field(None, alias="from")
    to_frame: Optional[int] = Field(None, alias="to")
    easing: Optional[Literal["linear", "easeIn", "easeOut", "spring"]] = "easeOut"
    distance: Optional[int] = None
    start: Optional[float] = None
    end: Optional[float] = None

    @validator("to_frame", always=True)
    def to_must_be_after_from(cls, v, values):
        frm = values.get("from_frame") or 0
        if v is None:
            return frm + 15
        if v <= frm:
            raise ValueError("'to' must be > 'from'")
        return v


class Transform(BaseModel):
    x: Optional[Union[int, Literal["center"]]] = 0
    y: Optional[Union[int, Literal["center"]]] = 0
    scale: Optional[float] = 1.0
    rotation: Optional[float] = 0.0


class StyleText(BaseModel):
    color: Optional[str] = "white"
    fontSize: Optional[int] = 48
    fontWeight: Optional[int] = 600
    fontFamily: Optional[str] = "Inter, sans-serif"


class LayerBase(BaseModel):
    id: Optional[str]
    type: str
    transform: Optional[Transform] = Transform()
    animation: Optional[Dict[str, AnimationSpec]] = None


class TextLayer(LayerBase):
    type: Literal["text"]
    content: str
    style: Optional[StyleText] = StyleText()


class ShapeLayer(LayerBase):
    type: Literal["shape"]
    shapeType: Literal["rect", "circle"]
    style: Dict[str, Any] = {}


class ImageLayer(LayerBase):
    type: Literal["image"]
    src: Union[str, HttpUrl]
    style: Optional[Dict[str, Any]] = {}


SceneLayer = Union[TextLayer, ShapeLayer, ImageLayer]


class SceneModel(BaseModel):
    width: Optional[int] = 1920
    height: Optional[int] = 1080
    fps: Optional[int] = 30
    duration: Optional[int] = 5
    background: Optional[str] = "#000000"
    layers: List[SceneLayer]

    @validator("duration")
    def duration_positive(cls, v):
        if v <= 0:
            raise ValueError("duration must be positive")
        return v