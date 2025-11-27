from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: Optional[str] = "demo_user"  # Default demo user for development

def require_user():
    """Mock user dependency for demo purposes"""
    return User(id="demo_user")