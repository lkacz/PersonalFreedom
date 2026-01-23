"""
Common utility functions for PersonalLiberty application.
Provides cross-platform and PyInstaller-compatible helpers.
"""

import sys
import os
from pathlib import Path


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
