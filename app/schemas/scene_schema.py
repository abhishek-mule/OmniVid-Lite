# app/schemas/scene_schema.py
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Union, Literal, Dict, Any

class MetaModel(BaseModel):
    fps: int = 30
    width: int = 1920
    height: int = 1080
    style: Optional[Literal["cinematic","playful","minimal","corporate"]] = "cinematic"
    colorPalette: List[str] = Field(default_factory=lambda: ["#0F0C29","#302B63","#24243E"])
    font: str = "Inter"

class AnimSpec(BaseModel):
    type: str
    duration: int
    easing: Optional[Literal["linear","easeIn","easeOut","spring"]] = "easeOut"
    startFrame: Optional[int] = 0
    distance: Optional[int]
    start: Optional[float]
    end: Optional[float]

    @validator("duration")
    def positive_duration(cls, v):
        if v <= 0:
            raise ValueError("duration must be positive frames")
        return v

class LayerBase(BaseModel):
    id: str
    type: str
    position: Union[str, Dict[str,int]] = "center"
    style: Optional[Dict[str, Any]] = {}
    animation: Optional[Dict[str, AnimSpec]] = {}

class TextLayer(LayerBase):
    type: Literal["text"]
    content: str

class ImageLayer(LayerBase):
    type: Literal["image"]
    url: Union[HttpUrl, str]

class ParticlesLayer(LayerBase):
    type: Literal["particles"]
    preset: Optional[str]
    density: Optional[Literal["low","medium","high"]]

Layer = Union[TextLayer, ImageLayer, ParticlesLayer]

class BackgroundModel(BaseModel):
    type: Literal["solid","gradient","image","video"] = "solid"
    value: Union[str, List[str]] = "#000000"
    animation: Optional[str]

class SceneModel(BaseModel):
    id: str
    duration: int  # frames
    background: Optional[BackgroundModel] = None
    camera: Optional[Dict[str, Any]] = {}
    layers: List[Layer]
    transition: Optional[Dict[str, Any]] = {}
    startFrame: Optional[int] = 0

class DSLModel(BaseModel):
    meta: MetaModel
    scenes: List[SceneModel]

    @validator("scenes")
    def not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError("must provide at least one scene")
        return v