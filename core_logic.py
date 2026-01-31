"""
Core logic for Personal Liberty - Website Blocker
Separated from UI for better architecture.
"""

import os
import sys
import json
import ctypes
import subprocess
import re
import uuid
import logging
import tempfile
import shutil
from typing import Dict, Optional, Any

try:
    import bcrypt
except ImportError:
    bcrypt = None  # type: ignore[assignment]

from pathlib import Path
from datetime import datetime
from user_manager import UserManager

# Setup logger
logger = logging.getLogger(__name__)

# Import AI modules
try:
    from productivity_ai import ProductivityAnalyzer as _ProductivityAnalyzer  # noqa: F401
    from productivity_ai import GamificationEngine as _GamificationEngine  # noqa: F401
    from productivity_ai import FocusGoals as _FocusGoals  # noqa: F401
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.warning("AI features not available - productivity_ai.py not found")

# GPU-accelerated local AI removed (was experimental, added ~3GB to app size)
# The heavy ML libraries (torch, transformers, sentence-transformers) are no longer bundled.
LOCAL_AI_AVAILABLE = False

# Import bypass logger
try:
    from bypass_logger import get_bypass_logger, BypassLogger, create_bypass_logger_for_user
    BYPASS_LOGGER_AVAILABLE = True
except ImportError:
    BYPASS_LOGGER_AVAILABLE = False
    get_bypass_logger = None  # type: ignore[assignment]
    BypassLogger = None  # type: ignore[assignment]
    create_bypass_logger_for_user = None  # type: ignore[assignment]
    logger.info("Bypass logger not available")

# Import gamification hero management (optional)
try:
    from gamification import ensure_hero_structure as _ensure_hero_structure
    from gamification import get_entity_luck_perks as _get_entity_luck_perks
    HERO_MANAGEMENT_AVAILABLE = True
except ImportError:
    HERO_MANAGEMENT_AVAILABLE = False
    _ensure_hero_structure = None  # type: ignore[assignment]
    _get_entity_luck_perks = None  # type: ignore[assignment]

# Windows hosts file path
system_root = os.environ.get('SystemRoot', r'C:\Windows')
HOSTS_PATH = os.path.join(system_root, r"System32\drivers\etc\hosts")
REDIRECT_IP = "127.0.0.1"
MARKER_START = "# === Personal Liberty BLOCK START ==="
MARKER_END = "# === Personal Liberty BLOCK END ==="

# Config file paths
if getattr(sys, 'frozen', False):
    # When running as executable, use AppData for user-writable files
    APP_DIR = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / "PersonalLiberty"
    APP_DIR.mkdir(parents=True, exist_ok=True)
else:
    APP_DIR = Path(__file__).parent

CONFIG_PATH = APP_DIR / "config.json"
STATS_PATH = APP_DIR / "stats.json"
GOALS_PATH = APP_DIR / "goals.json"
SESSION_STATE_PATH = APP_DIR / ".session_state.json"  # Crash recovery file

# Schema version for config migrations
# Increment when config structure changes in a breaking way
CONFIG_SCHEMA_VERSION = 1

# Auto-backup settings
MAX_AUTO_BACKUPS = 5  # Keep this many periodic backups


def ensure_backup_dir(user_dir: Optional[Path] = None) -> Path:
    """Ensure backup directory exists and return its path."""
    base = user_dir if user_dir else APP_DIR
    backup_dir = base / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def create_auto_backup(config_path: Path, backup_dir: Path, prefix: str = "auto") -> Optional[Path]:
    """
    Create an automatic backup of the config file.
    
    Returns the path to the backup file, or None if backup failed.
    Automatically removes old backups to keep only MAX_AUTO_BACKUPS.
    """
    if not config_path.exists():
        return None
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{prefix}_config_{timestamp}.json"
        shutil.copy2(config_path, backup_path)
        
        # Cleanup old backups - keep only MAX_AUTO_BACKUPS
        backups = sorted(
            backup_dir.glob(f"{prefix}_config_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old_backup in backups[MAX_AUTO_BACKUPS:]:
            try:
                old_backup.unlink()
            except OSError:
                pass
        
        logger.info(f"Created auto-backup: {backup_path.name}")
        return backup_path
    except (IOError, OSError) as e:
        logger.warning(f"Failed to create auto-backup: {e}")
        return None


def get_available_backups(backup_dir: Path) -> list:
    """Get list of available backups sorted by date (newest first)."""
    backups = []
    try:
        for backup_file in backup_dir.glob("*_config_*.json"):
            try:
                stat = backup_file.stat()
                backups.append({
                    "path": backup_file,
                    "name": backup_file.name,
                    "date": datetime.fromtimestamp(stat.st_mtime),
                    "size": stat.st_size,
                })
            except OSError:
                continue
        backups.sort(key=lambda x: x["date"], reverse=True)
    except OSError:
        pass
    return backups


def atomic_write_json(filepath: Path, data: dict) -> None:
    """
    Atomically write JSON data to a file.
    
    Writes to a temporary file first, then renames to target path.
    This prevents data corruption if the app crashes mid-write.
    """
    # Create temp file in the same directory (to ensure same filesystem for rename)
    fd, temp_path = tempfile.mkstemp(
        suffix='.tmp',
        prefix=filepath.stem + '_',
        dir=filepath.parent
    )
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        # Use os.replace for atomic rename (works on Windows and Unix)
        # os.replace is atomic and will overwrite the destination if it exists
        try:
            os.replace(temp_path, filepath)
        except OSError:
            # Fallback for very old Windows or cross-filesystem moves
            if sys.platform == 'win32' and filepath.exists():
                filepath.unlink()
            shutil.move(temp_path, filepath)
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


# Website categories with common distracting sites
SITE_CATEGORIES = {
    "Social Media": [
        "facebook.com", "www.facebook.com",
        "twitter.com", "www.twitter.com", "x.com", "www.x.com",
        "instagram.com", "www.instagram.com",
        "tiktok.com", "www.tiktok.com",
        "snapchat.com", "www.snapchat.com",
        "linkedin.com", "www.linkedin.com",
        "pinterest.com", "www.pinterest.com",
    ],
    "Video Streaming": [
        "youtube.com", "www.youtube.com",
        "netflix.com", "www.netflix.com",
        "hulu.com", "www.hulu.com",
        "disneyplus.com", "www.disneyplus.com",
        "max.com", "www.max.com",
        "primevideo.com", "www.primevideo.com",
        "twitch.tv", "www.twitch.tv",
        "vimeo.com", "www.vimeo.com",
    ],
    "Gaming": [
        "store.steampowered.com", "steampowered.com",
        "epicgames.com", "www.epicgames.com",
        "roblox.com", "www.roblox.com",
        "itch.io", "www.itch.io",
    ],
    "News & Forums": [
        "reddit.com", "www.reddit.com", "old.reddit.com",
        "news.ycombinator.com",
        "9gag.com", "www.9gag.com",
        "imgur.com", "www.imgur.com",
    ],
    "Shopping": [
        "amazon.com", "www.amazon.com",
        "ebay.com", "www.ebay.com",
        "aliexpress.com", "www.aliexpress.com",
        "etsy.com", "www.etsy.com",
    ],
}


class BlockMode:
    """Blocking mode constants"""
    NORMAL = "normal"
    STRICT = "strict"
    POMODORO = "pomodoro"
    SCHEDULED = "scheduled"
    HARDCORE = "hardcore"


class EnforcementMode:
    """Enforcement level for blocking - how aggressively sites are blocked"""
    FULL = "full"      # Uses hosts file - requires admin, fully blocks sites
    LIGHT = "light"    # Monitor-only mode - no admin needed, just notifications


class BlockerCore:
    """Core blocking engine with enhanced features"""

    def __init__(self, username: Optional[str] = None):
        # Initialize paths
        self.user_manager = UserManager(APP_DIR)
        self.username = username  # Store for later validation
        
        if username:
            try:
                self.user_dir = self.user_manager.get_user_dir(username)
                self.user_dir.mkdir(parents=True, exist_ok=True)
                self.config_path = self.user_dir / "config.json"
                self.stats_path = self.user_dir / "stats.json"
                self.goals_path = self.user_dir / "goals.json"
                self.session_state_path = self.user_dir / ".session_state.json"
            except (ValueError, OSError) as e:
                logger.error(f"Failed to initialize user profile '{username}': {e}")
                raise RuntimeError(f"Cannot initialize user profile '{username}'. The user directory may have been deleted or is inaccessible.") from e
        else:
            self.user_dir = None
            self.config_path = CONFIG_PATH
            self.stats_path = STATS_PATH
            self.goals_path = GOALS_PATH
            self.session_state_path = SESSION_STATE_PATH

        self.blacklist = []
        self.whitelist = []
        self.categories_enabled = {}
        self.is_blocking = False
        self.end_time = None
        self.mode = BlockMode.NORMAL
        self.password_hash = None
        self.session_id = None

        # Pomodoro settings
        self.pomodoro_work = 25
        self.pomodoro_break = 5
        self.pomodoro_long_break = 15
        self.pomodoro_sessions_before_long = 4
        self.pomodoro_current_session = 0
        self.is_break = False

        # Schedule
        self.schedules = []
        
        # Priorities (My Priorities feature)
        self.priorities = []
        self.show_priorities_on_startup = False
        self.ask_priority_on_session_start = True  # Ask which priority to work on when starting
        self.priority_checkin_enabled = False
        self.priority_checkin_interval = 30  # minutes
        
        # UI preferences
        self.minimize_to_tray = True  # Close button minimizes to tray
        self.notify_on_complete = True  # Notify when session ends
        self.toggle_hotkey = ""  # Global hotkey for show/hide window
        self.startup_sound_enabled = True  # Play sound when app starts minimized
        self.lottery_sound_enabled = True  # Play win/lose sounds after lottery animations
        
        # Enforcement mode: "full" (hosts file) or "light" (monitor + notifications only)
        self.enforcement_mode = EnforcementMode.FULL
        
        # System permission preferences (for "Don't ask again" dialogs)
        self.system_permissions = {}  # Dict of action -> True/False
        
        # ADHD Buster gamification
        self.adhd_buster = {"inventory": [], "equipped": {}, "coins": 200}
        
        # Weight tracking
        self.weight_entries = []  # List of {"date": "YYYY-MM-DD", "weight": float, "note": str}
        self.weight_unit = "kg"  # or "lbs"
        self.weight_goal = None  # Target weight
        self.weight_milestones = []  # List of achieved milestone IDs
        self.weight_height = None  # Height in cm for BMI calculation
        self.weight_reminder_enabled = False  # Daily reminder
        self.weight_reminder_time = "08:00"  # Reminder time HH:MM
        self.weight_last_reminder_date = None  # Last reminder shown
        
        # User profile for age/sex-specific norms
        self.user_birth_year = None  # Year of birth (e.g., 2010)
        self.user_birth_month = None  # Month of birth (1-12)
        self.user_gender = None  # "M" or "F"
        
        # Activity tracking
        self.activity_entries = []  # List of {"date": "YYYY-MM-DD", "duration": int, "activity_type": str, "intensity": str, "note": str}
        self.activity_milestones = []  # List of achieved milestone IDs
        self.activity_reminder_enabled = False  # Daily reminder
        self.activity_reminder_time = "18:00"  # Reminder time HH:MM
        self.activity_last_reminder_date = None  # Last reminder shown
        
        # Sleep tracking
        self.sleep_entries = []  # List of {"date": "YYYY-MM-DD", "sleep_hours": float, "bedtime": "HH:MM", "wake_time": "HH:MM", "quality": str, "disruptions": list, "score": int, "note": str}
        self.sleep_milestones = []  # List of achieved milestone IDs
        self.sleep_chronotype = "moderate"  # early_bird, moderate, night_owl
        self.sleep_reminder_enabled = False  # Daily reminder
        self.sleep_reminder_time = "21:00"  # Reminder time HH:MM (bedtime reminder)
        self.sleep_last_reminder_date = None  # Last reminder shown
        
        # Hydration tracking
        self.water_entries = []  # List of {"date": "YYYY-MM-DD", "time": "HH:MM", "glasses": 1}
        self.water_reminder_enabled = False  # Periodic hydration reminder
        self.water_reminder_interval = 60  # Minutes between reminders
        self.water_last_reminder_time = None  # Last reminder timestamp
        self.water_lottery_attempts = 0  # Cumulative lottery rolls (win chance +1% per attempt)
        
        # Eye & Breath tracking
        self.eye_reminder_enabled = False  # Periodic eye routine reminder
        self.eye_reminder_interval = 60  # Minutes between reminders (default 1 hour)
        self.eye_last_reminder_time = None  # Last reminder timestamp
        
        # Developer mode (hidden by default)
        self.dev_mode_enabled = False

        # Statistics
        self.stats = self._default_stats()
        
        # Bypass logger - use per-user storage for privacy
        self.bypass_logger = None
        if BYPASS_LOGGER_AVAILABLE:
            if self.user_dir and create_bypass_logger_for_user:
                # User-specific bypass logger for privacy isolation
                self.bypass_logger = create_bypass_logger_for_user(self.user_dir)
            elif get_bypass_logger:
                # Fallback to global singleton
                self.bypass_logger = get_bypass_logger()

        self.load_config()
        self.load_stats()

    def _default_stats(self) -> Dict[str, Any]:
        return {
            "total_focus_time": 0,
            "sessions_completed": 0,
            "sessions_cancelled": 0,
            "daily_stats": {},
            "streak_days": 0,
            "last_session_date": None,
            "best_streak": 0,
            "shutdown_times": [],  # List of {timestamp, type} when computer shuts down
            "startup_times": [],   # List of {timestamp} when app starts
        }

    def load_config(self) -> None:
        """Load configuration from file"""
        default_blacklist = []
        for sites in SITE_CATEGORIES.values():
            default_blacklist.extend(sites)

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.blacklist = config.get('blacklist', default_blacklist)
                    self.whitelist = config.get('whitelist', [])
                    # Merge loaded categories with current defaults (for new categories)
                    default_categories = {cat: True for cat in SITE_CATEGORIES}
                    loaded_categories = config.get('categories_enabled', {})
                    if not isinstance(loaded_categories, dict):
                        loaded_categories = {}
                    self.categories_enabled = {**default_categories, **loaded_categories}
                    self.password_hash = config.get('password_hash')
                    # Validate numeric config values to prevent crashes from corrupted config
                    pomo_work = config.get('pomodoro_work', 25)
                    self.pomodoro_work = pomo_work if isinstance(pomo_work, (int, float)) and pomo_work > 0 else 25
                    pomo_break = config.get('pomodoro_break', 5)
                    self.pomodoro_break = pomo_break if isinstance(pomo_break, (int, float)) and pomo_break > 0 else 5
                    pomo_long = config.get('pomodoro_long_break', 15)
                    self.pomodoro_long_break = pomo_long if isinstance(pomo_long, (int, float)) and pomo_long > 0 else 15
                    self.schedules = config.get('schedules', [])
                    self.priorities = config.get('priorities', [])
                    self.show_priorities_on_startup = config.get('show_priorities_on_startup', False)
                    self.ask_priority_on_session_start = config.get('ask_priority_on_session_start', True)
                    self.priority_checkin_enabled = config.get('priority_checkin_enabled', False)
                    checkin_interval = config.get('priority_checkin_interval', 30)
                    self.priority_checkin_interval = checkin_interval if isinstance(checkin_interval, (int, float)) and checkin_interval > 0 else 30
                    self.minimize_to_tray = config.get('minimize_to_tray', True)
                    self.toggle_hotkey = config.get('toggle_hotkey', "")
                    self.startup_sound_enabled = config.get('startup_sound_enabled', True)
                    self.lottery_sound_enabled = config.get('lottery_sound_enabled', True)
                    # Load enforcement mode (full = hosts file, light = notifications only)
                    enforcement = config.get('enforcement_mode', EnforcementMode.FULL)
                    self.enforcement_mode = enforcement if enforcement in (EnforcementMode.FULL, EnforcementMode.LIGHT) else EnforcementMode.FULL
                    # Load system permission preferences
                    self.system_permissions = config.get('system_permissions', {})
                    if not isinstance(self.system_permissions, dict):
                        self.system_permissions = {}
                    self.adhd_buster = config.get('adhd_buster', {})
                    if not isinstance(self.adhd_buster, dict):
                        self.adhd_buster = {}
                    # Ensure all required adhd_buster fields exist with correct types
                    adhd_defaults = {
                        "inventory": [],
                        "equipped": {},
                        "coins": 200,
                        "total_xp": 0,
                        "xp_history": []
                    }
                    for key, default in adhd_defaults.items():
                        if key not in self.adhd_buster:
                            self.adhd_buster[key] = default
                    # Type validation for critical fields
                    if not isinstance(self.adhd_buster.get("inventory"), list):
                        self.adhd_buster["inventory"] = []
                    if not isinstance(self.adhd_buster.get("equipped"), dict):
                        self.adhd_buster["equipped"] = {}
                    if not isinstance(self.adhd_buster.get("coins"), (int, float)):
                        self.adhd_buster["coins"] = 200
                    if not isinstance(self.adhd_buster.get("total_xp"), (int, float)):
                        self.adhd_buster["total_xp"] = 0
                    # Weight tracking - validate entries on load
                    raw_entries = config.get('weight_entries', [])
                    self.weight_entries = [
                        e for e in raw_entries
                        if isinstance(e, dict) 
                        and e.get("date") 
                        and isinstance(e.get("weight"), (int, float)) 
                        and e.get("weight") > 0
                    ]
                    self.weight_unit = config.get('weight_unit', 'kg')
                    self.weight_goal = config.get('weight_goal', None)
                    self.weight_milestones = config.get('weight_milestones', [])
                    self.weight_height = config.get('weight_height', None)
                    self.weight_reminder_enabled = config.get('weight_reminder_enabled', False)
                    self.weight_reminder_time = config.get('weight_reminder_time', '08:00')
                    self.weight_last_reminder_date = config.get('weight_last_reminder_date', None)
                    # User profile for age/sex-specific norms
                    birth_year = config.get('user_birth_year', None)
                    self.user_birth_year = birth_year if isinstance(birth_year, int) and 1900 <= birth_year <= 2100 else None
                    birth_month = config.get('user_birth_month', None)
                    self.user_birth_month = birth_month if isinstance(birth_month, int) and 1 <= birth_month <= 12 else None
                    gender = config.get('user_gender', None)
                    self.user_gender = gender if gender in ("M", "F") else None
                    # Activity tracking - validate entries on load
                    raw_activity = config.get('activity_entries', [])
                    self.activity_entries = [
                        e for e in raw_activity
                        if isinstance(e, dict)
                        and e.get("date")
                        and isinstance(e.get("duration"), (int, float))
                        and e.get("duration") > 0
                    ]
                    self.activity_milestones = config.get('activity_milestones', [])
                    self.activity_reminder_enabled = config.get('activity_reminder_enabled', False)
                    self.activity_reminder_time = config.get('activity_reminder_time', '18:00')
                    self.activity_last_reminder_date = config.get('activity_last_reminder_date', None)
                    # Sleep tracking - validate entries on load
                    raw_sleep = config.get('sleep_entries', [])
                    self.sleep_entries = [
                        e for e in raw_sleep
                        if isinstance(e, dict)
                        and e.get("date")
                        and isinstance(e.get("sleep_hours"), (int, float))
                        and e.get("sleep_hours") > 0
                    ]
                    self.sleep_milestones = config.get('sleep_milestones', [])
                    self.sleep_chronotype = config.get('sleep_chronotype', 'moderate')
                    self.sleep_reminder_enabled = config.get('sleep_reminder_enabled', False)
                    self.sleep_reminder_time = config.get('sleep_reminder_time', '21:00')
                    self.sleep_last_reminder_date = config.get('sleep_last_reminder_date', None)
                    # Hydration tracking - validate entries on load
                    raw_water = config.get('water_entries', [])
                    self.water_entries = [
                        e for e in raw_water
                        if isinstance(e, dict)
                        and e.get("date")
                    ]
                    self.water_reminder_enabled = config.get('water_reminder_enabled', False)
                    water_interval = config.get('water_reminder_interval', 60)
                    self.water_reminder_interval = water_interval if isinstance(water_interval, (int, float)) and water_interval > 0 else 60
                    self.water_last_reminder_time = config.get('water_last_reminder_time', None)
                    self.water_lottery_attempts = config.get('water_lottery_attempts', 0)
                    # Eye & Breath reminder settings
                    self.eye_reminder_enabled = config.get('eye_reminder_enabled', False)
                    eye_interval = config.get('eye_reminder_interval', 60)
                    self.eye_reminder_interval = eye_interval if isinstance(eye_interval, (int, float)) and eye_interval > 0 else 60
                    self.eye_last_reminder_time = config.get('eye_last_reminder_time', None)
                    self.eye_reminder_notification_type = config.get('eye_reminder_notification_type', 'Toast')
                    self.eye_reminder_message_index = config.get('eye_reminder_message_index', 0)
                    # Hydration reminder notification type
                    self.water_reminder_notification_type = config.get('water_reminder_notification_type', 'Toast')
                    self.water_reminder_message_index = config.get('water_reminder_message_index', 0)
                    # Developer mode (hidden by default, enabled by tapping version 7 times)
                    self.dev_mode_enabled = config.get('dev_mode_enabled', False)
                    # Initialize/migrate hero management structure
                    if HERO_MANAGEMENT_AVAILABLE and _ensure_hero_structure:
                        _ensure_hero_structure(self.adhd_buster)
            except (json.JSONDecodeError, IOError, OSError) as e:
                # Backup corrupted config to aid recovery/debugging
                try:
                    if self.config_path.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_path = self.config_path.with_suffix(f".corrupted.{timestamp}.bak")
                        shutil.copy2(self.config_path, backup_path)
                        logger.error(f"Config corrupted, backed up to {backup_path}")
                except Exception as backup_error:
                    logger.warning(f"Failed to back up corrupted config: {backup_error}")
                
                logger.warning(f"Could not load config ({e}), using defaults")
                self.blacklist = default_blacklist
                self.categories_enabled = {cat: True for cat in SITE_CATEGORIES}
        else:
            self.blacklist = default_blacklist
            self.categories_enabled = {cat: True for cat in SITE_CATEGORIES}
            self.save_config()

    def save_config(self, create_backup: bool = False) -> None:
        """Save configuration to file atomically (crash-safe)
        
        Args:
            create_backup: If True, create an auto-backup before saving.
                          Use for significant events like level-ups or session completion.
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create auto-backup if requested (e.g., on significant changes)
            if create_backup:
                backup_dir = ensure_backup_dir(self.user_dir)
                create_auto_backup(self.config_path, backup_dir)
            
            config = {
                # Schema metadata for future migrations
                '_schema_version': CONFIG_SCHEMA_VERSION,
                '_last_modified': datetime.now().isoformat(),
                # Settings
                'blacklist': self.blacklist,
                'whitelist': self.whitelist,
                'categories_enabled': self.categories_enabled,
                'password_hash': self.password_hash,
                'pomodoro_work': self.pomodoro_work,
                'pomodoro_break': self.pomodoro_break,
                'pomodoro_long_break': self.pomodoro_long_break,
                'schedules': self.schedules,
                'priorities': self.priorities,
                'show_priorities_on_startup': self.show_priorities_on_startup,
                'ask_priority_on_session_start': self.ask_priority_on_session_start,
                'priority_checkin_enabled': self.priority_checkin_enabled,
                'priority_checkin_interval': self.priority_checkin_interval,
                'minimize_to_tray': self.minimize_to_tray,
                'toggle_hotkey': self.toggle_hotkey,
                'startup_sound_enabled': self.startup_sound_enabled,
                'lottery_sound_enabled': self.lottery_sound_enabled,
                'enforcement_mode': self.enforcement_mode,
                'system_permissions': self.system_permissions,
                'adhd_buster': self.adhd_buster,
                'weight_entries': self.weight_entries,
                'weight_unit': self.weight_unit,
                'weight_goal': self.weight_goal,
                'weight_milestones': self.weight_milestones,
                'weight_height': self.weight_height,
                'weight_reminder_enabled': self.weight_reminder_enabled,
                'weight_reminder_time': self.weight_reminder_time,
                'weight_last_reminder_date': self.weight_last_reminder_date,
                'user_birth_year': self.user_birth_year,
                'user_birth_month': self.user_birth_month,
                'user_gender': self.user_gender,
                'activity_entries': self.activity_entries,
                'activity_milestones': self.activity_milestones,
                'activity_reminder_enabled': self.activity_reminder_enabled,
                'activity_reminder_time': self.activity_reminder_time,
                'activity_last_reminder_date': self.activity_last_reminder_date,
                'sleep_entries': self.sleep_entries,
                'sleep_milestones': self.sleep_milestones,
                'sleep_chronotype': self.sleep_chronotype,
                'sleep_reminder_enabled': self.sleep_reminder_enabled,
                'sleep_reminder_time': self.sleep_reminder_time,
                'sleep_last_reminder_date': self.sleep_last_reminder_date,
                'water_entries': self.water_entries,
                'water_reminder_enabled': self.water_reminder_enabled,
                'water_reminder_interval': self.water_reminder_interval,
                'water_last_reminder_time': self.water_last_reminder_time,
                'water_lottery_attempts': self.water_lottery_attempts,
                'eye_reminder_enabled': self.eye_reminder_enabled,
                'eye_reminder_interval': self.eye_reminder_interval,
                'eye_last_reminder_time': self.eye_last_reminder_time,
                'eye_reminder_notification_type': getattr(self, 'eye_reminder_notification_type', 'Toast'),
                'eye_reminder_message_index': getattr(self, 'eye_reminder_message_index', 0),
                'water_reminder_notification_type': getattr(self, 'water_reminder_notification_type', 'Toast'),
                'water_reminder_message_index': getattr(self, 'water_reminder_message_index', 0),
                'dev_mode_enabled': self.dev_mode_enabled,
            }
            atomic_write_json(self.config_path, config)
        except (IOError, OSError) as e:
            logger.error(f"Could not save config: {e}")

    def load_stats(self):
        """Load statistics from file"""
        if self.stats_path.exists():
            try:
                with open(self.stats_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.stats = {**self._default_stats(), **loaded}
            except (json.JSONDecodeError, IOError):
                pass

    def save_stats(self):
        """Save statistics to file atomically (crash-safe)"""
        try:
            atomic_write_json(self.stats_path, self.stats)
        except (IOError, OSError):
            pass

    def export_all_data(self, export_path: Path) -> dict:
        """
        Export all user data to a ZIP file for backup or GDPR compliance.
        
        Args:
            export_path: Path to write the ZIP file
            
        Returns:
            dict with 'success' (bool), 'message' (str), and 'files' (list of exported filenames)
        """
        import zipfile
        
        try:
            export_path = Path(export_path)
            exported_files = []
            
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add metadata
                metadata = {
                    "export_date": datetime.now().isoformat(),
                    "app_version": "PersonalLiberty",
                    "schema_version": CONFIG_SCHEMA_VERSION,
                    "username": self.username or "Default",
                }
                zf.writestr("_export_metadata.json", json.dumps(metadata, indent=2))
                exported_files.append("_export_metadata.json")
                
                # Export config (remove password hash for privacy)
                if self.config_path.exists():
                    try:
                        with open(self.config_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        config_data.pop('password_hash', None)
                        zf.writestr("config.json", json.dumps(config_data, indent=2))
                        exported_files.append("config.json")
                    except Exception:
                        pass
                
                # Export stats
                if self.stats_path.exists():
                    zf.write(self.stats_path, "stats.json")
                    exported_files.append("stats.json")
                
                # Export goals if exists
                if self.goals_path.exists():
                    zf.write(self.goals_path, "goals.json")
                    exported_files.append("goals.json")
                
                # Export backups folder if exists
                backup_dir = ensure_backup_dir(self.user_dir)
                if backup_dir.exists():
                    for backup_file in backup_dir.glob("*.json"):
                        arcname = f"backups/{backup_file.name}"
                        zf.write(backup_file, arcname)
                        exported_files.append(arcname)
                
                # Create human-readable summary
                summary = self._create_export_summary()
                zf.writestr("_summary.txt", summary)
                exported_files.append("_summary.txt")
            
            return {
                "success": True,
                "message": f"Exported {len(exported_files)} files to {export_path.name}",
                "files": exported_files,
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "files": [],
            }

    def _create_export_summary(self) -> str:
        """Create a human-readable summary of exported data."""
        lines = [
            "=" * 60,
            "PERSONAL LIBERTY - DATA EXPORT SUMMARY",
            "=" * 60,
            f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"User Profile: {self.username or 'Default'}",
            "",
            "STATISTICS",
            "-" * 40,
            f"Total Focus Time: {self.stats.get('total_focus_time', 0) // 60} minutes",
            f"Sessions Completed: {self.stats.get('sessions_completed', 0)}",
            f"Best Streak: {self.stats.get('best_streak', 0)} days",
            f"Current Streak: {self.stats.get('streak_days', 0)} days",
            "",
            "HEALTH TRACKING",
            "-" * 40,
            f"Weight Entries: {len(self.weight_entries)}",
            f"Sleep Entries: {len(self.sleep_entries)}",
            f"Activity Entries: {len(self.activity_entries)}",
            f"Water Entries: {len(self.water_entries)}",
            "",
            "GAME DATA",
            "-" * 40,
            f"Coins: {self.adhd_buster.get('coins', 0)}",
            f"Total XP: {self.adhd_buster.get('total_xp', 0)}",
            f"Inventory Items: {len(self.adhd_buster.get('inventory', []))}",
            f"Entities Collected: {len(self.adhd_buster.get('entitidex', {}))}",
            "",
            "=" * 60,
            "This export contains all your Personal Liberty data.",
            "Keep this file safe for backup or data portability.",
            "=" * 60,
        ]
        return "\n".join(lines)

    def record_shutdown_time(self, event_type: str = "shutdown") -> None:
        """Record the current time as a shutdown event.
        
        Args:
            event_type: Type of shutdown - 'shutdown', 'logoff', 'sleep', or 'app_close'
        """
        shutdown_record = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type
        }
        if "shutdown_times" not in self.stats:
            self.stats["shutdown_times"] = []
        self.stats["shutdown_times"].append(shutdown_record)
        # Keep only last 30 shutdown records to avoid bloat
        self.stats["shutdown_times"] = self.stats["shutdown_times"][-30:]
        self.save_stats()

    def record_startup_time(self) -> None:
        """Record the current time as a startup event."""
        startup_record = {
            "timestamp": datetime.now().isoformat()
        }
        if "startup_times" not in self.stats:
            self.stats["startup_times"] = []
        self.stats["startup_times"].append(startup_record)
        # Keep only last 30 startup records to avoid bloat
        self.stats["startup_times"] = self.stats["startup_times"][-30:]
        self.save_stats()

    # === Crash Recovery Methods ===

    def save_session_state(self, duration_seconds: int) -> None:
        """Save current session state for crash recovery.
        
        This file is created when blocking starts and deleted when blocking ends.
        If it exists on startup, the previous session crashed.
        """
        state = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "planned_duration": duration_seconds,
            "mode": self.mode,
            "pid": os.getpid(),
        }
        try:
            atomic_write_json(self.session_state_path, state)
        except (IOError, OSError) as e:
            logger.warning(f"Could not save session state: {e}")

    def clear_session_state(self) -> None:
        """Remove the session state file (called on clean shutdown)."""
        try:
            if self.session_state_path.exists():
                self.session_state_path.unlink()
        except (IOError, OSError) as e:
            logger.warning(f"Could not clear session state: {e}")

    def check_orphaned_session(self) -> Optional[Dict[str, Any]]:
        """Check if there's an orphaned session from a crash.
        
        Returns session info if orphaned session found, None otherwise.
        """
        if not self.session_state_path.exists():
            return None

        try:
            with open(self.session_state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Check if the old process is still running
            old_pid = state.get("pid")
            if old_pid and self._is_process_running(old_pid):
                # Another instance is still running, not orphaned
                return None

            # Check if blocks are actually in hosts file
            if not self._has_active_blocks():
                # No blocks in hosts file, just clean up the state file
                self.clear_session_state()
                return None

            return state

        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.warning(f"Could not read session state: {e}")
            # If we can't read it, check if hosts has blocks
            if self._has_active_blocks():
                return {"unknown": True, "start_time": "unknown"}
            return None

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            # On Windows, check if process exists
            if sys.platform == 'win32':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                SYNCHRONIZE = 0x00100000
                handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                os.kill(pid, 0)
                return True
        except (OSError, PermissionError):
            return False

    def _has_active_blocks(self) -> bool:
        """Check if our block markers exist in the hosts file."""
        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return MARKER_START in content and MARKER_END in content
        except (IOError, OSError):
            return False

    def recover_from_crash(self) -> tuple:
        """Clean up after a crash - remove all blocks.
        
        Returns tuple (success, message)
        """
        # Clear the session state file first
        self.clear_session_state()
        
        # Use emergency cleanup to remove blocks
        return self.emergency_cleanup()

    def update_stats(self, focus_seconds, completed=True):
        """Update session statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        current_hour = datetime.now().hour

        self.stats["total_focus_time"] += focus_seconds

        if completed:
            self.stats["sessions_completed"] += 1
        else:
            self.stats["sessions_cancelled"] += 1

        # Track session types for achievements (AI feature)
        if AI_AVAILABLE:
            # Track early morning sessions (5 AM - 9 AM)
            if 5 <= current_hour < 9:
                self.stats["early_sessions"] = self.stats.get("early_sessions", 0) + 1

            # Track night sessions (9 PM - 1 AM)
            if current_hour >= 21 or current_hour < 1:
                self.stats["night_sessions"] = self.stats.get("night_sessions", 0) + 1

            # Track strict mode sessions
            if self.mode == BlockMode.STRICT:
                self.stats["strict_sessions"] = self.stats.get("strict_sessions", 0) + 1

            # Track pomodoro sessions
            if self.mode == BlockMode.POMODORO:
                self.stats["pomodoro_sessions"] = self.stats.get("pomodoro_sessions", 0) + 1

        if "daily_stats" not in self.stats:
            self.stats["daily_stats"] = {}

        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {"focus_time": 0, "sessions": 0, "hourly": {}}

        self.stats["daily_stats"][today]["focus_time"] += focus_seconds
        self.stats["daily_stats"][today]["sessions"] += 1
        
        # Track hourly focus time distribution (for 24h timeline)
        if "hourly" not in self.stats["daily_stats"][today]:
            self.stats["daily_stats"][today]["hourly"] = {}
        hour_key = str(current_hour)
        if hour_key not in self.stats["daily_stats"][today]["hourly"]:
            self.stats["daily_stats"][today]["hourly"][hour_key] = 0
        self.stats["daily_stats"][today]["hourly"][hour_key] += focus_seconds
        
        # Cap daily_stats to last 365 days to prevent unbounded growth
        MAX_DAILY_STATS_DAYS = 365
        if len(self.stats["daily_stats"]) > MAX_DAILY_STATS_DAYS:
            sorted_dates = sorted(self.stats["daily_stats"].keys())
            for old_date in sorted_dates[:-MAX_DAILY_STATS_DAYS]:
                del self.stats["daily_stats"][old_date]

        # Update streak
        if self.stats.get("last_session_date"):
            try:
                last_date = datetime.strptime(self.stats["last_session_date"], "%Y-%m-%d")
                today_date = datetime.strptime(today, "%Y-%m-%d")
                days_gap = (today_date - last_date).days

                if days_gap == 1:
                    self.stats["streak_days"] = self.stats.get("streak_days", 0) + 1
                elif days_gap > 1:
                    # ✨ ENTITY PERK: Check for streak_save perk (chance to save streak)
                    streak_saved = False
                    if days_gap == 2 and _get_entity_luck_perks and hasattr(self, 'adhd_buster'):
                        luck_perks = _get_entity_luck_perks(self.adhd_buster)
                        streak_save_chance = luck_perks.get("streak_save", 0)
                        if streak_save_chance > 0:
                            import random
                            if random.randint(1, 100) <= streak_save_chance:
                                streak_saved = True
                                self.stats["streak_days"] = self.stats.get("streak_days", 0) + 1
                                self.adhd_buster["entity_streak_saves"] = self.adhd_buster.get("entity_streak_saves", 0) + 1
                                self.stats["entity_streak_saved"] = True  # Flag for UI to show message
                                logger.info(f"[Entity Perks] ✨ Streak saved by Brass Compass! ({streak_save_chance}% chance)")
                    
                    if not streak_saved:
                        self.stats["streak_days"] = 1
                        self.stats["entity_streak_saved"] = False
            except ValueError:
                self.stats["streak_days"] = 1
        else:
            self.stats["streak_days"] = 1

        # Update best streak
        if self.stats["streak_days"] > self.stats.get("best_streak", 0):
            self.stats["best_streak"] = self.stats["streak_days"]

        self.stats["last_session_date"] = today
        self.save_stats()

    def get_stats_summary(self):
        """Get a summary of statistics"""
        total_hours = self.stats["total_focus_time"] / 3600
        return {
            "total_hours": round(total_hours, 1),
            "sessions_completed": self.stats["sessions_completed"],
            "current_streak": self.stats.get("streak_days", 0),
            "best_streak": self.stats.get("best_streak", 0),
        }

    def get_bypass_statistics(self):
        """Get bypass attempt statistics"""
        if self.bypass_logger:
            return self.bypass_logger.get_statistics()
        return None

    def get_bypass_insights(self):
        """Get bypass attempt insights"""
        if self.bypass_logger:
            return self.bypass_logger.get_insights()
        return []

    def set_password(self, password: Optional[str]) -> None:
        """Set a password for strict mode using bcrypt

        Args:
            password: The password to set, or None to remove password
        """
        if password:
            if bcrypt:
                salt = bcrypt.gensalt()
                hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
                self.password_hash = hashed.decode('utf-8')
            else:
                logger.error("bcrypt not found, cannot set secure password")
                return
        else:
            self.password_hash = None
        self.save_config()

    def verify_password(self, password: str) -> bool:
        """Verify the password"""
        if not self.password_hash:
            return True

        try:
            if bcrypt:
                result = bcrypt.checkpw(
                    password.encode('utf-8'),
                    self.password_hash.encode('utf-8')
                )
                return bool(result)
            else:
                # bcrypt not available but password hash exists - this is a problem
                # Log warning but allow access to prevent permanent lockout
                logger.warning(
                    "bcrypt not installed but password hash exists. "
                    "Install bcrypt for password protection: pip install bcrypt"
                )
                return True  # Allow access rather than permanent lockout
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def is_admin(self) -> bool:
        """Check if running with administrator privileges"""
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except (AttributeError, OSError):
            return False

    def _is_valid_hostname(self, hostname):
        """Validate hostname format"""
        if not hostname or len(hostname) > 253:
            return False
        hostname = hostname.rstrip('.').lower()
        if '..' in hostname or '.' not in hostname:
            return False
        labels = hostname.split('.')
        for label in labels:
            if not label or len(label) > 63:
                return False
            if not re.match(r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$|^[a-z0-9]$', label):
                return False
        return True

    def _flush_dns(self) -> None:
        """Flush DNS cache safely"""
        try:
            subprocess.run(['ipconfig', '/flushdns'], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            logger.debug(f"DNS flush failed (non-critical): {e}")

    def get_effective_blacklist(self):
        """Get the effective blacklist considering categories and whitelist"""
        effective = set()

        for category, enabled in self.categories_enabled.items():
            if enabled and category in SITE_CATEGORIES:
                effective.update(SITE_CATEGORIES[category])

        effective.update(self.blacklist)
        effective -= set(self.whitelist)

        return list(effective)

    def block_sites(self, duration_seconds: int = 0):
        """Add blocked sites to hosts file (full mode) or start monitoring (light mode)
        
        Args:
            duration_seconds: Planned session duration for crash recovery
        """
        # State validation: prevent double-blocking
        if self.is_blocking:
            return False, "Already blocking! Stop the current session first."
        
        sites_to_block = self.get_effective_blacklist()
        if not sites_to_block:
            return False, "No sites to block! Add some sites in the Sites or Categories tab first."

        # Light mode: just start session tracking without hosts file modification
        if self.enforcement_mode == EnforcementMode.LIGHT:
            self.is_blocking = True
            self.session_id = str(uuid.uuid4())
            # Save session state for crash recovery
            self.save_session_state(duration_seconds)
            return True, f"🔔 Light Mode: Monitoring {len(sites_to_block)} sites (no blocking)"
        
        # Full mode: requires admin privileges to modify hosts file
        if not self.is_admin():
            return False, "Administrator privileges required!\\n\\nPlease restart the app as administrator:\\n• Right-click the app → Run as administrator\\n• Or use the 'run_as_admin.bat' script\\n\\n💡 Tip: Switch to Light Mode in Settings if you prefer not to run as admin."

        # Request user permission for hosts file modification (GUI only, handled at UI layer)
        # This check is performed in the UI before calling this method
        
        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if MARKER_START in content and MARKER_END in content:
                start_idx = content.find(MARKER_START)
                end_idx = content.find(MARKER_END) + len(MARKER_END)
                if start_idx < end_idx:
                    content = content[:start_idx] + content[end_idx:]

            block_entries = [f"\n{MARKER_START}"]
            for site in sites_to_block:
                clean_site = site.strip().lower()
                if clean_site and self._is_valid_hostname(clean_site):
                    block_entries.append(f"{REDIRECT_IP} {clean_site}")
            block_entries.append(f"{MARKER_END}\n")

            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n' + '\n'.join(block_entries))

            self.is_blocking = True
            self.session_id = str(uuid.uuid4())
            self._flush_dns()
            
            # Start bypass attempt logger
            if self.bypass_logger:
                self.bypass_logger.start_server()
            
            # Save session state for crash recovery
            self.save_session_state(duration_seconds)
            
            return True, f"Blocking {len(sites_to_block)} sites!"

        except PermissionError:
            return False, "Permission denied! Run as Administrator."
        except FileNotFoundError:
            return False, "Hosts file not found!"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def unblock_sites(self, password=None, force=False):
        """Remove blocked sites from hosts file

        Args:
            password: Password for strict mode
            force: If True, bypass password check (used for natural timer completion)
        """
        # Light mode: just clear session state, no hosts file changes
        if self.enforcement_mode == EnforcementMode.LIGHT:
            if self.mode == BlockMode.STRICT and self.is_blocking and not force:
                if self.password_hash and not self.verify_password(password or ""):
                    return False, "Incorrect password!"
            self.is_blocking = False
            self.session_id = None
            self.clear_session_state()
            return True, "Session ended!"
        
        # Full mode: requires admin privileges
        if not self.is_admin():
            return False, "Administrator privileges required!"

        if self.mode == BlockMode.STRICT and self.is_blocking and not force:
            if self.password_hash and not self.verify_password(password or ""):
                return False, "Incorrect password!"

        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if MARKER_START in content and MARKER_END in content:
                start_idx = content.find(MARKER_START)
                end_idx = content.find(MARKER_END) + len(MARKER_END)
                if start_idx < end_idx:
                    content = content[:start_idx] + content[end_idx:]

            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n')

            self.is_blocking = False
            self.session_id = None
            self._flush_dns()
            
            # Stop bypass attempt logger
            if self.bypass_logger:
                self.bypass_logger.stop_server()
            
            # Clear session state (crash recovery no longer needed)
            self.clear_session_state()
            
            return True, "Sites unblocked!"

        except PermissionError:
            return False, "Permission denied!"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def add_site(self, site):
        """Add a site to the blacklist"""
        if not site or not isinstance(site, str):
            return False
        site = site.lower().strip()
        for prefix in ['https://', 'http://', 'www.']:
            if site.startswith(prefix):
                site = site[len(prefix):]
        site = site.split('/')[0].strip()

        if not site or not self._is_valid_hostname(site):
            return False

        added = False
        if site not in self.blacklist:
            self.blacklist.append(site)
            added = True

        if not site.startswith('www.'):
            www_site = f"www.{site}"
            if www_site not in self.blacklist:
                self.blacklist.append(www_site)
                added = True

        if added:
            self.save_config()
        return added

    def remove_site(self, site):
        """Remove a site from the blacklist"""
        if site in self.blacklist:
            self.blacklist.remove(site)
            self.save_config()
            return True
        return False

    def add_to_whitelist(self, site):
        """Add a site to the whitelist"""
        if not site or not isinstance(site, str):
            return False
        site = site.lower().strip()
        for prefix in ['https://', 'http://', 'www.']:
            if site.startswith(prefix):
                site = site[len(prefix):]
        site = site.split('/')[0].strip()

        if site and site not in self.whitelist:
            self.whitelist.append(site)
            if not site.startswith('www.'):
                self.whitelist.append(f"www.{site}")
            self.save_config()
            return True
        return False

    def remove_from_whitelist(self, site):
        """Remove a site from whitelist"""
        if site in self.whitelist:
            self.whitelist.remove(site)
            self.save_config()
            return True
        return False

    def emergency_cleanup(self):
        """
        Emergency system cleanup - removes ALL traces of the app's activity:
        - Removes all blocked sites from hosts file
        - Stops any active session
        - Clears DNS cache
        Returns tuple (success, message)
        """
        if not self.is_admin():
            return False, "Administrator privileges required!"

        errors = []

        # 1. Force stop any active blocking (bypass password)
        self.is_blocking = False
        self.session_id = None
        self.end_time = None

        # 2. Clean hosts file - remove our markers section only
        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Remove our block section (between markers)
            if MARKER_START in content and MARKER_END in content:
                start_idx = content.find(MARKER_START)
                end_idx = content.find(MARKER_END) + len(MARKER_END)
                if start_idx < end_idx:
                    content = content[:start_idx] + content[end_idx:]
            
            # Clean up any extra blank lines left over
            while '\n\n\n' in content:
                content = content.replace('\n\n\n', '\n\n')

            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n')

        except Exception as e:
            errors.append(f"Hosts file: {str(e)}")

        # 3. Flush DNS cache
        try:
            self._flush_dns()
        except Exception as e:
            errors.append(f"DNS flush: {str(e)}")

        if errors:
            return True, f"Cleanup completed with warnings: {'; '.join(errors)}"
        return True, "System cleanup complete! All blocks removed."

    def export_config(self, filepath):
        """Export configuration to file"""
        try:
            config = {
                'blacklist': self.blacklist,
                'whitelist': self.whitelist,
                'categories_enabled': self.categories_enabled,
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except (IOError, OSError, TypeError) as e:
            logger.warning(f"Failed to export config: {e}")
            return False

    def import_config(self, filepath):
        """Import configuration from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if 'blacklist' in config:
                blacklist_data = config['blacklist']
                if isinstance(blacklist_data, list):
                    self.blacklist.extend([s for s in blacklist_data if s not in self.blacklist])
            if 'whitelist' in config:
                whitelist_data = config['whitelist']
                if isinstance(whitelist_data, list):
                    self.whitelist.extend([s for s in whitelist_data if s not in self.whitelist])
            self.save_config()
            return True
        except (IOError, OSError, json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to import config: {e}")
            return False

    def add_schedule(self, days, start_time, end_time):
        """Add a blocking schedule.
        
        Args:
            days: List of weekday integers (0=Monday, 6=Sunday)
            start_time: Start time as "HH:MM" string
            end_time: End time as "HH:MM" string
            
        Returns:
            Schedule ID string, or None if validation fails
        """
        # Validate days
        if not isinstance(days, list) or not days:
            logger.warning("Invalid schedule: days must be a non-empty list")
            return None
        if not all(isinstance(d, int) and 0 <= d <= 6 for d in days):
            logger.warning("Invalid schedule: days must be integers 0-6")
            return None
        
        # Validate time format (HH:MM)
        import re
        time_pattern = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)$')
        if not isinstance(start_time, str) or not isinstance(end_time, str):
            logger.warning("Invalid schedule: start_time/end_time must be strings")
            return None
        if not time_pattern.match(start_time):
            logger.warning(f"Invalid schedule: start_time '{start_time}' not in HH:MM format")
            return None
        if not time_pattern.match(end_time):
            logger.warning(f"Invalid schedule: end_time '{end_time}' not in HH:MM format")
            return None
        
        # Normalize times to zero-padded HH:MM format
        start_parts = start_time.split(':')
        end_parts = end_time.split(':')
        start_time = f"{int(start_parts[0]):02d}:{start_parts[1]}"
        end_time = f"{int(end_parts[0]):02d}:{end_parts[1]}"
        
        schedule = {
            'id': str(uuid.uuid4())[:8],
            'days': days,
            'start_time': start_time,
            'end_time': end_time,
            'enabled': True
        }
        self.schedules.append(schedule)
        self.save_config()
        return schedule['id']

    def remove_schedule(self, schedule_id):
        """Remove a schedule"""
        self.schedules = [s for s in self.schedules if s.get('id') != schedule_id]
        self.save_config()

    def toggle_schedule(self, schedule_id):
        """Toggle a schedule on/off"""
        for s in self.schedules:
            if s.get('id') == schedule_id:
                s['enabled'] = not s.get('enabled', True)
                self.save_config()
                return s['enabled']
        return None

    def is_scheduled_block_time(self):
        """Check if current time is within any active schedule"""
        now = datetime.now()
        current_day = now.weekday()
        yesterday = (current_day - 1) % 7  # Handle Sunday -> Saturday wrap
        current_time = now.strftime("%H:%M")

        for schedule in self.schedules:
            if not schedule.get('enabled', True):
                continue
            
            start = schedule.get('start_time', '00:00')
            end = schedule.get('end_time', '23:59')
            schedule_days = schedule.get('days', [])
            
            # Handle overnight schedules (e.g., 22:00 to 06:00)
            if start <= end:
                # Normal case: same day schedule
                if current_day in schedule_days and start <= current_time <= end:
                    return True
            else:
                # Overnight case: crosses midnight
                # Two conditions to check:
                # 1. Today is in schedule_days AND current_time >= start (pre-midnight portion)
                # 2. Yesterday is in schedule_days AND current_time <= end (post-midnight portion)
                if current_day in schedule_days and current_time >= start:
                    return True
                if yesterday in schedule_days and current_time <= end:
                    return True
        return False
