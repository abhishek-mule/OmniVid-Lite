"""Tests for the video API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.core.config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database tables
Base.metadata.create_all(bind=engine)

# Dependency to override the get_db dependency in the main app
def override_get_db():
    """Override the get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Set up test client
client = TestClient(app)

def test_generate_video():
    """Test video generation endpoint."""
    test_data = {
        "prompt": "A serene beach at sunset",
        "duration": 5.0,
        "resolution": "1920x1080",
        "format": "mp4"
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/video/generate",
        json=test_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"

def test_get_video_status():
    """Test video status endpoint."""
    # First create a job
    test_data = {
        "prompt": "A test video",
        "duration": 5.0
    }
    
    create_response = client.post(
        f"{settings.API_V1_STR}/video/generate",
        json=test_data
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]
    
    # Now check the status
    status_response = client.get(
        f"{settings.API_V1_STR}/video/{job_id}/status"
    )
    
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["job_id"] == job_id
    assert "status" in data
    assert "progress" in data

def test_invalid_video_format():
    """Test video generation with invalid format."""
    test_data = {
        "prompt": "A test video",
        "format": "invalid_format"  # Invalid format
    }
    
    response = client.post(
        f"{settings.API_V1_STR}/video/generate",
        json=test_data
    )
    
    assert response.status_code == 422  # Validation error

# Clean up after tests
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Clean up after tests."""
    yield
    # Clean up test database
    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("test.db"):
        os.remove("test.db")
