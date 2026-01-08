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
    from bypass_logger import get_bypass_logger, BypassLogger
    BYPASS_LOGGER_AVAILABLE = True
except ImportError:
    BYPASS_LOGGER_AVAILABLE = False
    get_bypass_logger = None  # type: ignore[assignment]
    BypassLogger = None  # type: ignore[assignment]
    logger.info("Bypass logger not available")

# Import gamification hero management (optional)
try:
    from gamification import ensure_hero_structure as _ensure_hero_structure
    HERO_MANAGEMENT_AVAILABLE = True
except ImportError:
    HERO_MANAGEMENT_AVAILABLE = False
    _ensure_hero_structure = None  # type: ignore[assignment]

# Windows hosts file path
system_root = os.environ.get('SystemRoot', r'C:\Windows')
HOSTS_PATH = os.path.join(system_root, r"System32\drivers\etc\hosts")
REDIRECT_IP = "127.0.0.1"
MARKER_START = "# === Personal Liberty BLOCK START ==="
MARKER_END = "# === Personal Liberty BLOCK END ==="

# Config file paths
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

CONFIG_PATH = APP_DIR / "config.json"
STATS_PATH = APP_DIR / "stats.json"
GOALS_PATH = APP_DIR / "goals.json"
SESSION_STATE_PATH = APP_DIR / ".session_state.json"  # Crash recovery file


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
        # On Windows, we need to remove the target first if it exists
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


class BlockerCore:
    """Core blocking engine with enhanced features"""

    def __init__(self):
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
        self.priority_checkin_enabled = False
        self.priority_checkin_interval = 30  # minutes
        
        # UI preferences
        self.minimize_to_tray = True  # Close button minimizes to tray
        
        # ADHD Buster gamification
        self.adhd_buster = {"inventory": [], "equipped": {}}
        
        # Weight tracking
        self.weight_entries = []  # List of {"date": "YYYY-MM-DD", "weight": float, "note": str}
        self.weight_unit = "kg"  # or "lbs"
        self.weight_goal = None  # Target weight
        self.weight_milestones = []  # List of achieved milestone IDs
        self.weight_height = None  # Height in cm for BMI calculation
        self.weight_reminder_enabled = False  # Daily reminder
        self.weight_reminder_time = "08:00"  # Reminder time HH:MM
        self.weight_last_reminder_date = None  # Last reminder shown

        # Statistics
        self.stats = self._default_stats()
        
        # Bypass logger
        self.bypass_logger = None
        if BYPASS_LOGGER_AVAILABLE and get_bypass_logger:
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
        }

    def load_config(self) -> None:
        """Load configuration from file"""
        default_blacklist = []
        for sites in SITE_CATEGORIES.values():
            default_blacklist.extend(sites)

        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.blacklist = config.get('blacklist', default_blacklist)
                    self.whitelist = config.get('whitelist', [])
                    self.categories_enabled = config.get(
                        'categories_enabled',
                        {cat: True for cat in SITE_CATEGORIES})
                    self.password_hash = config.get('password_hash')
                    self.pomodoro_work = config.get('pomodoro_work', 25)
                    self.pomodoro_break = config.get('pomodoro_break', 5)
                    self.pomodoro_long_break = config.get('pomodoro_long_break', 15)
                    self.schedules = config.get('schedules', [])
                    self.priorities = config.get('priorities', [])
                    self.show_priorities_on_startup = config.get('show_priorities_on_startup', False)
                    self.priority_checkin_enabled = config.get('priority_checkin_enabled', False)
                    self.priority_checkin_interval = config.get('priority_checkin_interval', 30)
                    self.minimize_to_tray = config.get('minimize_to_tray', True)
                    self.adhd_buster = config.get('adhd_buster', {"inventory": [], "equipped": {}})
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
                    # Initialize/migrate hero management structure
                    if HERO_MANAGEMENT_AVAILABLE and _ensure_hero_structure:
                        _ensure_hero_structure(self.adhd_buster)
            except (json.JSONDecodeError, IOError, OSError):
                self.blacklist = default_blacklist
                self.categories_enabled = {cat: True for cat in SITE_CATEGORIES}
        else:
            self.blacklist = default_blacklist
            self.categories_enabled = {cat: True for cat in SITE_CATEGORIES}
            self.save_config()

    def save_config(self) -> None:
        """Save configuration to file atomically (crash-safe)"""
        try:
            config = {
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
                'priority_checkin_enabled': self.priority_checkin_enabled,
                'priority_checkin_interval': self.priority_checkin_interval,
                'minimize_to_tray': self.minimize_to_tray,
                'adhd_buster': self.adhd_buster,
                'weight_entries': self.weight_entries,
                'weight_unit': self.weight_unit,
                'weight_goal': self.weight_goal,
                'weight_milestones': self.weight_milestones,
                'weight_height': self.weight_height,
                'weight_reminder_enabled': self.weight_reminder_enabled,
                'weight_reminder_time': self.weight_reminder_time,
                'weight_last_reminder_date': self.weight_last_reminder_date,
            }
            atomic_write_json(CONFIG_PATH, config)
        except (IOError, OSError) as e:
            logger.error(f"Could not save config: {e}")

    def load_stats(self):
        """Load statistics from file"""
        if STATS_PATH.exists():
            try:
                with open(STATS_PATH, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.stats = {**self._default_stats(), **loaded}
            except (json.JSONDecodeError, IOError):
                pass

    def save_stats(self):
        """Save statistics to file atomically (crash-safe)"""
        try:
            atomic_write_json(STATS_PATH, self.stats)
        except (IOError, OSError):
            pass

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
            with open(SESSION_STATE_PATH, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except (IOError, OSError) as e:
            logger.warning(f"Could not save session state: {e}")

    def clear_session_state(self) -> None:
        """Remove the session state file (called on clean shutdown)."""
        try:
            if SESSION_STATE_PATH.exists():
                SESSION_STATE_PATH.unlink()
        except (IOError, OSError) as e:
            logger.warning(f"Could not clear session state: {e}")

    def check_orphaned_session(self) -> Optional[Dict[str, Any]]:
        """Check if there's an orphaned session from a crash.
        
        Returns session info if orphaned session found, None otherwise.
        """
        if not SESSION_STATE_PATH.exists():
            return None

        try:
            with open(SESSION_STATE_PATH, 'r', encoding='utf-8') as f:
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
            self.stats["daily_stats"][today] = {"focus_time": 0, "sessions": 0}

        self.stats["daily_stats"][today]["focus_time"] += focus_seconds
        self.stats["daily_stats"][today]["sessions"] += 1

        # Update streak
        if self.stats.get("last_session_date"):
            try:
                last_date = datetime.strptime(self.stats["last_session_date"], "%Y-%m-%d")
                today_date = datetime.strptime(today, "%Y-%m-%d")

                if (today_date - last_date).days == 1:
                    self.stats["streak_days"] = self.stats.get("streak_days", 0) + 1
                elif (today_date - last_date).days > 1:
                    self.stats["streak_days"] = 1
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
                return False
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
        """Add blocked sites to hosts file
        
        Args:
            duration_seconds: Planned session duration for crash recovery
        """
        if not self.is_admin():
            return False, "Administrator privileges required!\\n\\nPlease restart the app as administrator:\\n• Right-click the app → Run as administrator\\n• Or use the 'run_as_admin.bat' script"

        sites_to_block = self.get_effective_blacklist()
        if not sites_to_block:
            return False, "No sites to block! Add some sites in the Sites or Categories tab first."

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

        # 2. Clean hosts file - remove ALL our markers
        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Remove our block section
            if MARKER_START in content and MARKER_END in content:
                start_idx = content.find(MARKER_START)
                end_idx = content.find(MARKER_END) + len(MARKER_END)
                if start_idx < end_idx:
                    content = content[:start_idx] + content[end_idx:]

            # Also clean up any stray entries (just in case)
            lines = content.split('\n')
            clean_lines = []
            for line in lines:
                # Skip lines with our redirect that might be orphaned
                if REDIRECT_IP in line and any(site in line for site in self.blacklist[:10]):
                    continue
                clean_lines.append(line)

            content = '\n'.join(clean_lines)

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
        except Exception:
            return False

    def import_config(self, filepath):
        """Import configuration from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if 'blacklist' in config:
                self.blacklist.extend([s for s in config['blacklist'] if s not in self.blacklist])
            if 'whitelist' in config:
                self.whitelist.extend([s for s in config['whitelist'] if s not in self.whitelist])
            self.save_config()
            return True
        except Exception:
            return False

    def add_schedule(self, days, start_time, end_time):
        """Add a blocking schedule"""
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
        current_time = now.strftime("%H:%M")

        for schedule in self.schedules:
            if not schedule.get('enabled', True):
                continue
            if current_day in schedule.get('days', []):
                start = schedule.get('start_time', '00:00')
                end = schedule.get('end_time', '23:59')

                # Handle overnight schedules (e.g., 22:00 to 06:00)
                if start <= end:
                    # Normal case: same day schedule
                    if start <= current_time <= end:
                        return True
                else:
                    # Overnight case: crosses midnight
                    if current_time >= start or current_time <= end:
                        return True
        return False
