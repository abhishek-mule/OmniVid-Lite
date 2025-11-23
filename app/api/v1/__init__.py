"""API v1 routes package."""
from fastapi import APIRouter
from . import routes_video, routes_status
from .endpoints import render

router = APIRouter()
router.include_router(routes_video.router, prefix="/video", tags=["video"])
router.include_router(routes_status.router, prefix="/video", tags=["status"])
router.include_router(render.router, prefix="/render", tags=["render"])