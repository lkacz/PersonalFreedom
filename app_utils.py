"""
Common utility functions for PersonalLiberty application.
Provides cross-platform and PyInstaller-compatible helpers.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# The hour at which daily counters reset (5 AM = activities can span past midnight)
DAILY_RESET_HOUR = 5


def get_activity_date(dt: Optional[datetime] = None) -> str:
    """
    Get the 'activity date' for daily counters, using a 5 AM cutoff.
    
    This means if it's 2:00 AM, the activity date is still 'yesterday' because
    the user's day hasn't ended yet. The new day starts at 5 AM, not midnight.
    
    This is useful for tracking daily activities like water intake, exercise,
    focus time, etc. that may span past midnight.
    
    Args:
        dt: The datetime to calculate for (defaults to now)
        
    Returns:
        Date string in YYYY-MM-DD format representing the activity day
    """
    if dt is None:
        dt = datetime.now()
    
    # If before 5 AM, treat as previous day's activity
    if dt.hour < DAILY_RESET_HOUR:
        dt = dt - timedelta(days=1)
    
    return dt.strftime("%Y-%m-%d")


def get_activity_day_start(dt: Optional[datetime] = None) -> datetime:
    """
    Get the start of the current 'activity day' (5 AM cutoff).
    
    Args:
        dt: The datetime to calculate for (defaults to now)
        
    Returns:
        datetime representing 5 AM of the current activity day
    """
    if dt is None:
        dt = datetime.now()
    
    if dt.hour < DAILY_RESET_HOUR:
        # Before 5 AM - day started at 5 AM yesterday
        day_start = dt.replace(hour=DAILY_RESET_HOUR, minute=0, second=0, microsecond=0) - timedelta(days=1)
    else:
        # After 5 AM - day started at 5 AM today
        day_start = dt.replace(hour=DAILY_RESET_HOUR, minute=0, second=0, microsecond=0)
    
    return day_start


def get_app_dir() -> Path:
    """
    Get the application directory, handling both development and PyInstaller bundle modes.
    
    In development: Returns the directory containing the source files.
    In PyInstaller bundle: Returns sys._MEIPASS where bundled resources are extracted.
    
    Use this for accessing bundled resources like icons, voices, sounds, etc.
    
    Returns:
        Path to the application's resource directory
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle - use _MEIPASS for bundled resources
        return Path(sys._MEIPASS)
    else:
        # Running in development mode - use directory of this file
        return Path(__file__).parent


def get_resource_path(*path_parts) -> Path:
    """
    Get full path to a bundled resource file.
    
    Example:
        icon_path = get_resource_path("icons", "entities", "creature.svg")
        voice_path = get_resource_path("voices", "en_US-lessac-medium.onnx")
    
    Args:
        *path_parts: Path components relative to app directory
        
    Returns:
        Full Path to the resource
    """
    return get_app_dir().joinpath(*path_parts)


def resource_exists(*path_parts) -> bool:
    """
    Check if a bundled resource exists.
    
    Args:
        *path_parts: Path components relative to app directory
        
    Returns:
        True if the resource file exists
    """
    return get_resource_path(*path_parts).exists()
