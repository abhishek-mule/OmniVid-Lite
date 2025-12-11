"""
API Integration Tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
import asyncio

client = TestClient(app)

# Test API key for testing
TEST_API_KEY = "test-api-key-" + "x" * 32

@pytest.fixture
def auth_headers():
    """Get authentication headers"""
    return {settings.API_KEY_HEADER: TEST_API_KEY}

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "OmniVid-Lite API"
    assert data["version"] == "2.0.0"

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]

def test_render_without_auth():
    """Test render endpoint without authentication"""
    if not settings.REQUIRE_API_KEY:
        pytest.skip("API key not required in current config")

    response = client.post(
        "/api/v1/render",
        json={"prompt": "Test video with text"}
    )
    assert response.status_code == 401

def test_render_with_invalid_prompt(auth_headers):
    """Test render with invalid prompt"""
    response = client.post(
        "/api/v1/render",
        headers=auth_headers,
        json={"prompt": "short"}  # Too short
    )
    assert response.status_code == 400

def test_render_success(auth_headers):
    """Test successful render job creation"""
    response = client.post(
        "/api/v1/render",
        headers=auth_headers,
        json={
            "prompt": "Create a video with text 'Hello World' that fades in",
            "creative": True
        }
    )
    assert response.status_code == 202  # Accepted for async processing
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert "poll_url" in data
    assert "download_url" in data
    return data["job_id"]

def test_status_not_found():
    """Test status endpoint with non-existent job"""
    response = client.get("/api/v1/status/invalid-job-id")
    assert response.status_code == 404

def test_status_success(auth_headers):
    """Test status endpoint with valid job"""
    # First create a job
    create_response = client.post(
        "/api/v1/render",
        headers=auth_headers,
        json={"prompt": "Test video for status check"}
    )
    job_id = create_response.json()["job_id"]

    # Check status
    response = client.get(f"/api/v1/status/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert "status" in data
    assert "progress" in data

def test_cancel_job(auth_headers):
    """Test job cancellation"""
    # Create a job
    create_response = client.post(
        "/api/v1/render",
        headers=auth_headers,
        json={"prompt": "Test video for cancellation"}
    )
    job_id = create_response.json()["job_id"]

    # Cancel it
    response = client.patch(
        f"/api/v1/render/cancel/{job_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Cancellation requested"

def test_list_jobs(auth_headers):
    """Test listing user jobs"""
    # Create a couple jobs
    job_ids = []
    for i in range(2):
        response = client.post(
            "/api/v1/render",
            headers=auth_headers,
            json={"prompt": f"Test video {i}"}
        )
        job_ids.append(response.json()["job_id"])

    # List jobs
    response = client.get("/api/v1/render/jobs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert len(data["jobs"]) >= 2

    # Check job structure
    job = data["jobs"][0]
    assert "job_id" in job
    assert "status" in job
    assert "created_at" in job
    assert "updated_at" in job


def test_download_job_not_ready(auth_headers):
    """Test downloading a job that isn't ready"""
    # Create a job
    response = client.post(
        "/api/v1/render",
        headers=auth_headers,
        json={"prompt": "Test video for download"}
    )
    job_id = response.json()["job_id"]

    # Try to download before completion
    response = client.get(f"/api/v1/render/download/{job_id}", headers=auth_headers)
    assert response.status_code == 425  # Too Early


def test_rate_limiting():
    """Test rate limiting"""
    if not settings.RATE_LIMIT_ENABLED:
        pytest.skip("Rate limiting not enabled")

    # Make many requests quickly
    for i in range(settings.RATE_LIMIT_PER_MINUTE + 5):
        response = client.get("/api/v1/health")
        if response.status_code == 429:
            # Got rate limited as expected
            return

    # If we get here, rate limiting didn't work
    pytest.fail("Rate limiting did not trigger")