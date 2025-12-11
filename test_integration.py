#!/usr/bin/env python3
"""
Integration test for OmniVid Lite MVP
Tests the complete flow: render → status → download
"""

import requests
import time
import json
import os
from pathlib import Path

API_BASE = "http://localhost:8001"

def test_full_flow():
    """Test the complete video generation flow"""

    print("Testing OmniVid Lite MVP Integration")
    print("=" * 50)

    # Step 1: Create a video render job
    print("\n1. Creating video render job...")
    render_payload = {
        "prompt": "Create a video with the text 'Hello MVP!'",
        "creative": False
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/v1/render",
            json=render_payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 202:
            print(f"FAILED to create job: {response.status_code} - {response.text}")
            return False

        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"SUCCESS: Job created: {job_id}")
        print(f"   Status URL: {job_data['poll_url']}")
        print(f"   Download URL: {job_data['download_url']}")

    except Exception as e:
        print(f"FAILED to create job: {e}")
        return False

    # Step 2: Poll for status until completion
    print("\n2. Polling job status...")
    max_polls = 30  # 30 seconds max
    poll_count = 0

    while poll_count < max_polls:
        try:
            response = requests.get(f"{API_BASE}/api/v1/render/status/{job_id}")

            if response.status_code == 200:
                status_data = response.json()
                progress = status_data.get("progress", 0)
                status = status_data.get("status", "unknown")

                print(f"   Status: {status} ({progress}%)")

                if status == "completed":
                    print("SUCCESS: Job completed!")
                    output_path = status_data.get("output_path")
                    print(f"   Output: {output_path}")
                    break
                elif status == "failed":
                    print(f"FAILED: Job failed: {status_data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"FAILED: Status check failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"FAILED: Status check error: {e}")
            return False

        poll_count += 1
        if poll_count < max_polls:
            time.sleep(1)

    if poll_count >= max_polls:
        print("FAILED: Job did not complete within timeout")
        return False

    # Step 3: Download the video
    print("\n3. Downloading video...")
    try:
        response = requests.get(f"{API_BASE}/api/v1/render/download/{job_id}")

        if response.status_code == 200:
            # Save the video
            download_dir = Path("test_downloads")
            download_dir.mkdir(exist_ok=True)
            video_path = download_dir / f"{job_id}.mp4"

            with open(video_path, "wb") as f:
                f.write(response.content)

            file_size = len(response.content)
            print(f"SUCCESS: Video downloaded: {video_path} ({file_size} bytes)")

            # Verify it's a valid MP4 file (basic check)
            if file_size > 1000:  # Should be at least 1KB
                print("SUCCESS: Video file appears valid")
            else:
                print("WARNING: Video file seems too small")
                return False

        else:
            print(f"FAILED: Download failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"FAILED: Download error: {e}")
        return False

    print("\n" + "=" * 50)
    print("SUCCESS: MVP Integration Test PASSED!")
    print("Video generation pipeline working end-to-end")
    return True

if __name__ == "__main__":
    success = test_full_flow()
    exit(0 if success else 1)