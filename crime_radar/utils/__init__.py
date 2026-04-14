"""Utility functions for Crime Radar."""

from datetime import datetime, timedelta
from typing import Optional
import hashlib


def generate_incident_hash(data: dict) -> str:
    """Generate a hash for deduplication of incidents."""
    key_fields = f"{data.get('latitude')}{data.get('longitude')}{data.get('reported_at')}"
    return hashlib.md5(key_fields.encode()).hexdigest()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula."""
    import math
    
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime for display."""
    dt = dt or datetime.utcnow()
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def parse_time_range(range_str: str) -> tuple[datetime, datetime]:
    """Parse a time range string like '24h', '7d', '30d'."""
    now = datetime.utcnow()
    
    if range_str.endswith('h'):
        hours = int(range_str[:-1])
        return now - timedelta(hours=hours), now
    elif range_str.endswith('d'):
        days = int(range_str[:-1])
        return now - timedelta(days=days), now
    elif range_str.endswith('w'):
        weeks = int(range_str[:-1])
        return now - timedelta(weeks=weeks), now
    
    return now - timedelta(hours=24), now
