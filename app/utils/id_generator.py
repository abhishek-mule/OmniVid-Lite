"""ID generation utilities."""
import uuid
from typing import Optional

def generate_uuid() -> str:
    """Generate a UUID4 string.
    
    Returns:
        str: A UUID4 string
    """
    return str(uuid.uuid4())

def generate_short_id(prefix: Optional[str] = None) -> str:
    """Generate a short, URL-friendly ID.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        str: A short ID string
    """
    short_id = uuid.uuid4().hex[:8]  # First 8 chars of a UUID
    if prefix:
        return f"{prefix}_{short_id}"
    return short_id
