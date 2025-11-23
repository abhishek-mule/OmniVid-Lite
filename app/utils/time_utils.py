"""Time-related utility functions."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

def utc_now() -> datetime:
    """Get current time in UTC.
    
    Returns:
        datetime: Current UTC time
    """
    return datetime.now(timezone.utc)

def format_datetime(dt: Optional[datetime] = None, 
                   format_str: str = "%Y-%m-%dT%H:%M:%S%z") -> Optional[str]:
    """Format a datetime object as a string.
    
    Args:
        dt: Datetime to format. If None, uses current time.
        format_str: Format string. Defaults to ISO 8601 format.
        
    Returns:
        Formatted datetime string, or None if dt is None
    """
    if dt is None:
        dt = utc_now()
    return dt.strftime(format_str)

def parse_datetime(datetime_str: str, 
                  format_str: str = "%Y-%m-%dT%H:%M:%S%z") -> datetime:
    """Parse a datetime string to a datetime object.
    
    Args:
        datetime_str: Datetime string to parse
        format_str: Format string to use for parsing
        
    Returns:
        Parsed datetime object
    """
    return datetime.strptime(datetime_str, format_str)

def time_ago(dt: datetime) -> str:
    """Get a human-readable string representing time elapsed since the given datetime.
    
    Args:
        dt: Past datetime
        
    Returns:
        Human-readable string (e.g., "2 hours ago")
    """
    now = utc_now()
    delta = now - dt if now > dt else dt - now
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    if delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    if delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return "just now"

def add_time(dt: datetime, 
            days: int = 0, 
            hours: int = 0, 
            minutes: int = 0, 
            seconds: int = 0) -> datetime:
    """Add time to a datetime.
    
    Args:
        dt: Base datetime
        days: Days to add
        hours: Hours to add
        minutes: Minutes to add
        seconds: Seconds to add
        
    Returns:
        New datetime with time added
    """
    return dt + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
