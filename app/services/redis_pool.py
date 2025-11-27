from arq import create_pool
from app.core.config import settings

# Global Redis pool instance
_redis_pool = None

async def get_redis_pool():
    """Get or create Redis connection pool"""
    global _redis_pool
    if _redis_pool is None:
        # For demo purposes, always return None to skip Redis
        print("Running in demo mode without Redis queuing.")
        _redis_pool = None
    return _redis_pool

def get_redis():
    """Sync dependency for FastAPI - returns the pool"""
    # In a real app, you'd use async context manager
    # For demo, we'll handle this in the endpoint
    return None