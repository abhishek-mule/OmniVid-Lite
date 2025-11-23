"""Script to clean up old or failed jobs from the database."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.video_job import VideoJob, JobStatus

def clean_old_jobs(days_old: int = 30) -> int:
    """Remove completed or failed jobs older than the specified number of days.
    
    Args:
        days_old: Remove jobs older than this many days
        
    Returns:
        int: Number of jobs deleted
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        # Find jobs to delete
        jobs_to_delete = db.query(VideoJob).filter(
            and_(
                VideoJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
                VideoJob.updated_at < cutoff_date
            )
        ).all()
        
        count = len(jobs_to_delete)
        
        # Delete the jobs
        for job in jobs_to_delete:
            db.delete(job)
        
        db.commit()
        return count
        
    except Exception as e:
        print(f"Error cleaning up jobs: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def clean_failed_jobs() -> int:
    """Remove all failed jobs.
    
    Returns:
        int: Number of jobs deleted
    """
    db = SessionLocal()
    try:
        # Find all failed jobs
        failed_jobs = db.query(VideoJob).filter(
            VideoJob.status == JobStatus.FAILED
        ).all()
        
        count = len(failed_jobs)
        
        # Delete the jobs
        for job in failed_jobs:
            db.delete(job)
        
        db.commit()
        return count
        
    except Exception as e:
        print(f"Error cleaning up failed jobs: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up old or failed jobs.")
    parser.add_argument(
        "--days", 
        type=int, 
        default=30,
        help="Remove completed/failed jobs older than this many days"
    )
    parser.add_argument(
        "--failed",
        action="store_true",
        help="Remove all failed jobs regardless of age"
    )
    
    args = parser.parse_args()
    
    if args.failed:
        count = clean_failed_jobs()
        print(f"Removed {count} failed jobs.")
    else:
        count = clean_old_jobs(args.days)
        print(f"Removed {count} jobs older than {args.days} days.")
