"""Tests for the video API endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

# Set up test client
client = TestClient(app)

def test_generate_video():
    """Test video generation endpoint."""
    test_data = {
        "prompt": "A serene beach at sunset",
        "creative": False
    }

    response = client.post(
        f"{settings.API_V1_STR}/render",
        json=test_data
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"

def test_get_video_status():
    """Test video status endpoint."""
    # First create a job
    test_data = {
        "prompt": "A test video",
        "creative": True
    }

    create_response = client.post(
        f"{settings.API_V1_STR}/render",
        json=test_data
    )
    assert create_response.status_code == 202
    job_id = create_response.json()["job_id"]

    # Now check the status
    status_response = client.get(
        f"{settings.API_V1_STR}/render/status/{job_id}"
    )

    assert status_response.status_code == 200
    data = status_response.json()
    assert data["job_id"] == job_id
    assert "status" in data

def test_invalid_prompt():
    """Test video generation with invalid prompt."""
    test_data = {
        "prompt": "",  # Empty prompt
        "creative": False
    }

    response = client.post(
        f"{settings.API_V1_STR}/render",
        json=test_data
    )

    assert response.status_code == 400  # Bad request

# Clean up after tests
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Clean up after tests."""
    yield
    # Clean up test job files
    import os
    import shutil
    if os.path.exists("jobs"):
        shutil.rmtree("jobs")
