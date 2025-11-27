import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("omnivid")

class AuditLogger:
    """Structured audit logging for job operations"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def log_job_event(self, job_id: str, event: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        """Log a job-related event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": job_id,
            "event": event,
            "user_id": user_id,
            "details": details or {}
        }

        # Write to job-specific log file
        log_file = self.log_dir / f"job_{job_id}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

        # Also log to main audit log
        audit_file = self.log_dir / "audit.log"
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

        # Log to console for development
        logger.info(f"JOB_EVENT: {job_id} - {event} - {details}")

    def get_job_history(self, job_id: str) -> list:
        """Get audit history for a specific job"""
        log_file = self.log_dir / f"job_{job_id}.log"
        if not log_file.exists():
            return []

        history = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    history.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        return history

    def log_api_request(self, endpoint: str, method: str, user_id: Optional[str] = None, job_id: Optional[str] = None):
        """Log API requests"""
        self.log_job_event(
            job_id or "system",
            "api_request",
            {"endpoint": endpoint, "method": method},
            user_id
        )

    def log_pipeline_stage(self, job_id: str, stage: str, status: str, details: Optional[Dict] = None):
        """Log pipeline stage transitions"""
        self.log_job_event(
            job_id,
            "pipeline_stage",
            {"stage": stage, "status": status, **(details or {})},
            None  # Pipeline stages don't have direct user context
        )

    def log_error(self, job_id: str, error_type: str, error_message: str, context: Optional[Dict] = None):
        """Log errors with context"""
        self.log_job_event(
            job_id,
            "error",
            {
                "error_type": error_type,
                "message": error_message,
                "context": context or {}
            }
        )

# Global audit logger instance
audit_logger = AuditLogger()