"""API v1 routes package."""
from fastapi import APIRouter
from .endpoints.render import router as render_router

router = APIRouter()
router.include_router(render_router, tags=["render"])