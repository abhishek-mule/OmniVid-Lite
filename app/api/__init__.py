"""API package for OmniVid Lite."""
from fastapi import APIRouter

api_router = APIRouter()

# Import and include all API versions
from . import v1  # noqa