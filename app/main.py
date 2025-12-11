"""
OmniVid-Lite Enhanced Backend
Main FastAPI application with production-ready features
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from typing import Optional

from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.endpoints.render import router as render_router
from app.api.v1.endpoints.render import router as status_router  # status routes are in render.py
from app.api.v1.endpoints.render import router as download_router  # download routes are in render.py
from app.core.config import settings
from app.core.logging_config import setup_logging

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting OmniVid-Lite application...")
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down OmniVid-Lite application...")
    logger.info("Application shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="OmniVid-Lite API",
    description="AI-powered text-to-video generation API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Custom Middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging"""
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

# Include routers
app.include_router(render_router, prefix="/api/v1", tags=["Video Generation"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OmniVid-Lite API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "OmniVid-Lite API",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
