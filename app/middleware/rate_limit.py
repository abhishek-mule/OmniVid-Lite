# ============= Rate Limiting Middleware =============

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import status
import logging
from typing import Dict
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests"""

    def __init__(self, app):
        super().__init__(app)
        # Store request counts: {client_ip: {minute: count, hour: count}}
        self.request_counts: Dict[str, Dict[str, Dict[datetime, int]]] = defaultdict(
            lambda: {"minute": defaultdict(int), "hour": defaultdict(int)}
        )
        # Last cleanup time
        self.last_cleanup = datetime.utcnow()

    async def dispatch(self, request, call_next):
        """Process request with rate limiting"""

        # Skip rate limiting if disabled
        if not getattr(settings, 'RATE_LIMIT_ENABLED', True):
            return await call_next(request)

        # Skip for public paths
        if request.url.path in ["/", "/api/docs", "/api/redoc", "/api/v1/health"]:
            return await call_next(request)

        # Get client identifier
        client_ip = self._get_client_ip(request)

        # Check rate limits
        is_allowed, wait_time = self._check_rate_limit(client_ip)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Please wait {wait_time} seconds before retrying",
                    "retry_after": wait_time
                },
                headers={"Retry-After": str(wait_time)}
            )

        # Record request
        self._record_request(client_ip)

        # Periodic cleanup
        await self._cleanup_old_entries()

        # Continue processing
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60))
        response.headers["X-RateLimit-Limit-Hour"] = str(getattr(settings, 'RATE_LIMIT_PER_HOUR', 1000))
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60) - self._get_minute_count(client_ip))
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, getattr(settings, 'RATE_LIMIT_PER_HOUR', 1000) - self._get_hour_count(client_ip))
        )

        return response

    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        # Check for forwarded IP (if behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Use direct client IP
        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, client_ip: str) -> tuple[bool, int]:
        """
        Check if client has exceeded rate limit

        Returns:
            (is_allowed, wait_time_seconds)
        """
        now = datetime.utcnow()

        # Check per-minute limit
        minute_count = self._get_minute_count(client_ip)
        if minute_count >= getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60):
            return False, 60

        # Check per-hour limit
        hour_count = self._get_hour_count(client_ip)
        if hour_count >= getattr(settings, 'RATE_LIMIT_PER_HOUR', 1000):
            return False, 3600

        return True, 0

    def _get_minute_count(self, client_ip: str) -> int:
        """Get request count for current minute"""
        now = datetime.utcnow()
        current_minute = now.replace(second=0, microsecond=0)
        return self.request_counts[client_ip]["minute"].get(current_minute, 0)

    def _get_hour_count(self, client_ip: str) -> int:
        """Get request count for current hour"""
        now = datetime.utcnow()
        current_hour = now.replace(minute=0, second=0, microsecond=0)

        # Sum all minutes in current hour
        total = 0
        for minute, count in self.request_counts[client_ip]["minute"].items():
            if minute >= current_hour:
                total += count

        return total

    def _record_request(self, client_ip: str):
        """Record a request from client"""
        now = datetime.utcnow()
        current_minute = now.replace(second=0, microsecond=0)

        self.request_counts[client_ip]["minute"][current_minute] += 1

    async def _cleanup_old_entries(self):
        """Clean up old rate limit entries"""
        now = datetime.utcnow()

        # Only cleanup every 5 minutes
        if (now - self.last_cleanup).total_seconds() < 300:
            return

        self.last_cleanup = now
        cutoff_time = now - timedelta(hours=1)

        # Clean up old entries
        for client_ip in list(self.request_counts.keys()):
            # Remove old minute entries
            old_minutes = [
                minute for minute in self.request_counts[client_ip]["minute"]
                if minute < cutoff_time
            ]
            for minute in old_minutes:
                del self.request_counts[client_ip]["minute"][minute]

            # Remove client if no recent requests
            if not self.request_counts[client_ip]["minute"]:
                del self.request_counts[client_ip]

        logger.info(f"Rate limit cleanup complete. Tracking {len(self.request_counts)} clients")