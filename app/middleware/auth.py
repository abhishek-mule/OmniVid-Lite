"""
Authentication and Rate Limiting Middleware
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============= Authentication Middleware =============

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""

    # Public endpoints that don't require authentication
    PUBLIC_PATHS = [
        "/",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/health",
        "/api/v1/render/templates",
        "/api/v1/render/templates/categories",
        "/api/v1/render/ai-status"
    ]

    async def dispatch(self, request: Request, call_next):
        """Process request with authentication"""

        # Skip auth for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth if not required
        if not settings.REQUIRE_API_KEY:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get(settings.API_KEY_HEADER)

        if not api_key:
            logger.warning(
                f"Missing API key from {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Missing API key",
                    "message": f"Please provide API key in {settings.API_KEY_HEADER} header"
                }
            )

        # Validate API key (in production, check against database)
        if not self._validate_api_key(api_key):
            logger.warning(
                f"Invalid API key from {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid API key"}
            )

        # Add user info to request state
        request.state.api_key = api_key
        request.state.user_id = self._get_user_id(api_key)

        # Continue processing
        response = await call_next(request)
        return response

    def _validate_api_key(self, api_key: str) -> bool:
        """
        Validate API key against database

        In production, this should query the database.
        For MVP, we'll use a simple validation.
        """
        # For development: accept any key that's at least 32 chars
        if settings.DEBUG:
            return len(api_key) >= 32

        # TODO: Implement actual database validation
        # from app.database import SessionLocal
        # from app.models import APIKey
        # db = SessionLocal()
        # key = db.query(APIKey).filter(
        #     APIKey.key == api_key,
        #     APIKey.is_active == True
        # ).first()
        # db.close()
        # return key is not None

        return True

    def _get_user_id(self, api_key: str) -> str:
        """Get user ID from API key"""
        # For development: hash the API key
        if settings.DEBUG:
            return hashlib.md5(api_key.encode()).hexdigest()[:8]

        # TODO: Implement actual database lookup
        return "user_123"