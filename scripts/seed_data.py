"""Script to seed the database with initial data."""
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.video_job import VideoJob, JobStatus

def seed_database():
    """Seed the database with initial data."""
    db = SessionLocal()
    
    try:
        # Check if we already have data
        if db.query(VideoJob).count() > 0:
            print("Database already has data, skipping seeding.")
            return
        
        # Create some test jobs
        jobs = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "user_id": "test_user_1",
                "status": JobStatus.COMPLETED,
                "params": {"prompt": "A beautiful sunset over mountains"},
                "result": {"video_url": "/videos/sunset.mp4"},
                "created_at": datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2023, 1, 1, 12, 5, tzinfo=timezone.utc)
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "user_id": "test_user_1",
                "status": JobStatus.FAILED,
                "params": {"prompt": "A rainy day in the city"},
                "error": "Failed to generate video: timeout",
                "created_at": datetime(2023, 1, 2, 10, 0, tzinfo=timezone.utc),
                "updated_at": datetime(2023, 1, 2, 10, 2, tzinfo=timezone.utc)
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "user_id": "test_user_2",
                "status": JobStatus.PROCESSING,
                "params": {"prompt": "A forest with a river"},
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        ]
        
        # Add jobs to database
        for job_data in jobs:
            job = VideoJob(**job_data)
            db.add(job)
        
        db.commit()
        print(f"Successfully seeded {len(jobs)} video jobs.")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
