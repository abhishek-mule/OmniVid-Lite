from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Any

class Layer(BaseModel):
    type: str
    id: str
    content: Optional[str] = None
    style: Optional[Dict[str, Any]] = None
    transform: Optional[Dict[str, Any]] = None
    animation: Optional[Dict[str, Any]] = None
    effects: Optional[List[Dict[str, Any]]] = None

class Scene(BaseModel):
    id: str
    duration: float
    background: Dict[str, Any]
    layers: List[Layer]

class Metadata(BaseModel):
    width: int
    height: int
    fps: int
    duration: float
    style: Optional[str] = None

class VideoDSL(BaseModel):
    metadata: Metadata
    scenes: List[Scene]