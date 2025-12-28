"""
System Tray version of Personal Freedom - Focus Blocker
Runs minimized in the system tray for unobtrusive operation.

Usage:
    python tray_blocker.py

Will automatically request admin privileges if needed.
"""

import threading
import time
import os
import sys
import json
import ctypes
import subprocess
import re
from pathlib import Path

# Check for required packages
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("Required packages not found. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pystray", "Pillow"], check=True)
    import pystray
    from PIL import Image, ImageDraw

# Windows hosts file path - use environment variable for flexibility
system_root = os.environ.get('SystemRoot', r'C:\Windows')
HOSTS_PATH = os.path.join(system_root, r"System32\drivers\etc\hosts")
REDIRECT_IP = "127.0.0.1"
MARKER_START = "# === PERSONAL FREEDOM BLOCK START ==="
MARKER_END = "# === PERSONAL FREEDOM BLOCK END ==="

# Config file path
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
SESSION_STATE_PATH = SCRIPT_DIR / ".session_state.json"  # Crash recovery file

# Import bypass logger if available
try:
    from bypass_logger import get_bypass_logger
    BYPASS_LOGGER_AVAILABLE = True
except ImportError:
    BYPASS_LOGGER_AVAILABLE = False
    get_bypass_logger = None

# Default sites to block
DEFAULT_BLACKLIST = [
    "facebook.com", "www.facebook.com",
    "youtube.com", "www.youtube.com",
    "twitter.com", "www.twitter.com",
    "x.com", "www.x.com",
    "instagram.com", "www.instagram.com",
    "tiktok.com", "www.tiktok.com",
    "reddit.com", "www.reddit.com",
    "netflix.com", "www.netflix.com",
    "twitch.tv", "www.twitch.tv",
]


def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, OSError):
        return False


def request_admin_and_restart():
    """Restart the script with administrator privileges"""
    script = os.path.abspath(sys.argv[0])

    # Handle both .py and .exe
    if script.endswith('.py'):
        params = f'"{script}"'
        executable = sys.executable
    else:
        params = ""
        executable = script

    print(f"Requesting admin privileges...")
    print(f"Executable: {executable}")
    print(f"Params: {params}")

    # Request elevation
    result = ctypes.windll.shell32.ShellExecuteW(
        None,           # hwnd
        "runas",        # operation
        executable,     # file
        params,         # parameters
        str(SCRIPT_DIR), # directory
        1               # show window
    )

    # If result > 32, it succeeded
    return result > 32


class TrayBlocker:
    def __init__(self):
        self.blacklist = []
        self.is_blocking = False
        self.remaining_seconds = 0
        self.timer_thread = None
        self.icon = None
        self._stop_event = threading.Event()
        self.session_start_time = None
        self.load_config()
        self.stats = self._load_stats()
        
        # Initialize bypass logger
        self.bypass_logger = None
        if BYPASS_LOGGER_AVAILABLE and get_bypass_logger:
            self.bypass_logger = get_bypass_logger()
        
        # Check for crash recovery on startup
        self.check_crash_recovery()
    
    def _load_stats(self):
        """Load statistics from file"""
        stats_path = SCRIPT_DIR / "stats.json"
        default_stats = {
            "total_focus_time": 0,
            "sessions_completed": 0,
            "sessions_cancelled": 0,
            "daily_stats": {},
            "streak_days": 0,
            "last_session_date": None,
            "best_streak": 0,
        }
        if stats_path.exists():
            try:
                with open(stats_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    return {**default_stats, **loaded}
            except (json.JSONDecodeError, IOError):
                pass
        return default_stats
    
    def _save_stats(self):
        """Save statistics to file"""
        stats_path = SCRIPT_DIR / "stats.json"
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2)
        except (IOError, OSError) as e:
            print(f"Warning: Could not save stats: {e}")
    
    def _update_stats(self, focus_seconds, completed=True):
        """Update session statistics"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        self.stats["total_focus_time"] += focus_seconds
        
        if completed:
            self.stats["sessions_completed"] += 1
        else:
            self.stats["sessions_cancelled"] += 1
        
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
        self._save_stats()
        print(f"📊 Stats updated: {focus_seconds // 60} min session, streak: {self.stats['streak_days']} days")

    def load_config(self):
        """Load configuration from file"""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    loaded_list = config.get('blacklist', [])
                    if isinstance(loaded_list, list) and loaded_list:
                        self.blacklist = loaded_list
                    else:
                        self.blacklist = DEFAULT_BLACKLIST.copy()
            except (json.JSONDecodeError, IOError, OSError):
                self.blacklist = DEFAULT_BLACKLIST.copy()
        else:
            self.blacklist = DEFAULT_BLACKLIST.copy()

        print(f"Loaded {len(self.blacklist)} sites to block")

    # === Crash Recovery Methods ===

    def save_session_state(self, duration_seconds: int) -> None:
        """Save session state for crash recovery."""
        from datetime import datetime
        state = {
            "session_id": str(id(self)),
            "start_time": datetime.now().isoformat(),
            "planned_duration": duration_seconds,
            "mode": "tray",
            "pid": os.getpid(),
        }
        try:
            with open(SESSION_STATE_PATH, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except (IOError, OSError) as e:
            print(f"Warning: Could not save session state: {e}")

    def clear_session_state(self) -> None:
        """Remove the session state file."""
        try:
            if SESSION_STATE_PATH.exists():
                SESSION_STATE_PATH.unlink()
        except (IOError, OSError) as e:
            print(f"Warning: Could not clear session state: {e}")

    def check_crash_recovery(self) -> None:
        """Check for orphaned sessions from a crash."""
        if not SESSION_STATE_PATH.exists():
            return

        try:
            with open(SESSION_STATE_PATH, 'r', encoding='utf-8') as f:
                state = json.load(f)

            old_pid = state.get("pid")
            if old_pid and self._is_process_running(old_pid):
                return  # Another instance is running

            # Check if blocks exist in hosts file
            if self._has_active_blocks():
                print("⚠️  Detected orphaned blocks from a previous crash!")
                print("    Cleaning up automatically...")
                self.unblock_sites()
                self.clear_session_state()
                print("✓  Crash recovery complete - blocks removed")
            else:
                self.clear_session_state()

        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"Warning: Could not check crash recovery: {e}")
            if self._has_active_blocks():
                print("    Found blocks in hosts file - cleaning up...")
                self.unblock_sites()

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            if sys.platform == 'win32':
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

    def _flush_dns(self):
        """Flush DNS cache safely"""
        try:
            subprocess.run(
                ['ipconfig', '/flushdns'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception:
            pass

    def create_icon_image(self, blocking=False):
        """Create a simple icon image"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        if blocking:
            # Red circle when blocking
            draw.ellipse([4, 4, size-4, size-4], fill='#e74c3c', outline='#c0392b', width=2)
            # Lock symbol
            draw.rectangle([20, 30, 44, 50], fill='white')
            draw.arc([24, 18, 40, 34], 0, 180, fill='white', width=4)
        else:
            # Green circle when not blocking
            draw.ellipse([4, 4, size-4, size-4], fill='#2ecc71', outline='#27ae60', width=2)
            # Check mark
            draw.line([(20, 32), (28, 42), (44, 22)], fill='white', width=4)

        return image

    def block_sites(self, duration_seconds: int = 0):
        """Add blocked sites to hosts file
        
        Args:
            duration_seconds: Planned session duration for crash recovery
        """
        if not is_admin():
            print("ERROR: Cannot block - not running as admin!")
            return False

        if not self.blacklist:
            print("ERROR: No sites to block!")
            return False

        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Remove existing block if present
            if MARKER_START in content and MARKER_END in content:
                start_idx = content.find(MARKER_START)
                end_idx = content.find(MARKER_END) + len(MARKER_END)
                if start_idx < end_idx:
                    content = content[:start_idx] + content[end_idx:]

            # Build block entries
            block_entries = [f"\n{MARKER_START}"]
            blocked_count = 0
            for site in self.blacklist:
                clean_site = site.strip().lower()
                if clean_site and self._is_valid_hostname(clean_site):
                    block_entries.append(f"{REDIRECT_IP} {clean_site}")
                    blocked_count += 1
            block_entries.append(f"{MARKER_END}\n")

            # Write back
            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n' + '\n'.join(block_entries))

            self.is_blocking = True
            self._flush_dns()
            
            # Start bypass attempt logger
            if self.bypass_logger:
                self.bypass_logger.start_server()
            
            # Save session state for crash recovery
            self.save_session_state(duration_seconds)
            
            print(f"✓ Blocking {blocked_count} sites")
            return True

        except PermissionError:
            print("ERROR: Permission denied writing to hosts file!")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
            return False

    def unblock_sites(self):
        """Remove blocked sites from hosts file"""
        if not is_admin():
            print("ERROR: Cannot unblock - not running as admin!")
            return False

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
            self._flush_dns()
            
            # Stop bypass attempt logger
            if self.bypass_logger:
                self.bypass_logger.stop_server()
            
            # Clear session state (crash recovery no longer needed)
            self.clear_session_state()
            
            print("✓ Sites unblocked")
            return True

        except Exception as e:
            print(f"ERROR: {e}")
            return False

    def format_time(self, seconds):
        """Format seconds to HH:MM:SS"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def start_session(self, minutes):
        """Start a focus session"""
        if self.is_blocking:
            print("Session already active!")
            return

        print(f"Starting {minutes} minute session...")

        def timer_callback():
            import time as time_module
            self.remaining_seconds = minutes * 60
            duration_seconds = minutes * 60
            session_start = time_module.time()

            if not self.block_sites(duration_seconds=duration_seconds):
                print("Failed to start blocking!")
                self.remaining_seconds = 0
                return

            self.update_icon()

            # Show notification
            if self.icon:
                try:
                    self.icon.notify(
                        f"Blocking {len(self.blacklist)} sites for {minutes} minutes",
                        "Focus Session Started"
                    )
                except Exception:
                    pass
            
            # Play start sound
            self._play_notification_sound()

            # Timer loop
            while self.remaining_seconds > 0 and self.is_blocking:
                if self._stop_event.wait(timeout=1):
                    break
                self.remaining_seconds -= 1
                try:
                    self.update_menu()
                except Exception:
                    pass

            # Calculate elapsed time
            elapsed = int(time_module.time() - session_start)
            completed = self.remaining_seconds <= 0 and self.is_blocking

            # Session ended
            if self.is_blocking:
                self.unblock_sites()
                self.update_icon()
                
                # Update stats
                self._update_stats(elapsed, completed=True)
                
                # Play completion sound
                self._play_notification_sound()
                
                if self.icon:
                    try:
                        total_hours = self.stats.get('total_focus_time', 0) / 3600
                        streak = self.stats.get('streak_days', 0)
                        self.icon.notify(
                            f"Session complete! 🔥 Streak: {streak} days | Total: {total_hours:.1f}h",
                            "Focus Complete! 🎉"
                        )
                    except Exception:
                        pass
            else:
                # Session was stopped manually
                if elapsed > 60:  # Only count if > 1 minute
                    self._update_stats(elapsed, completed=False)

            print("Session ended")

        self._stop_event.clear()
        self.timer_thread = threading.Thread(target=timer_callback, daemon=True)
        self.timer_thread.start()

    def stop_session(self, icon=None, item=None):
        """Stop the current session"""
        print("Stopping session...")
        self._stop_event.set()
        self.remaining_seconds = 0
        self.unblock_sites()
        self.update_icon()
    
    def _play_notification_sound(self):
        """Play a notification sound"""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass  # Sound not critical

    def update_icon(self):
        """Update the tray icon"""
        if self.icon:
            try:
                self.icon.icon = self.create_icon_image(self.is_blocking)
            except Exception:
                pass

    def update_menu(self):
        """Update the menu (for timer display)"""
        if self.icon:
            try:
                self.icon.update_menu()
            except Exception:
                pass

    def get_status_text(self, item):
        """Get current status text for menu"""
        if self.is_blocking:
            return f"🔒 Blocking - {self.format_time(self.remaining_seconds)}"
        admin_status = "✅" if is_admin() else "⚠️ No Admin"
        return f"{admin_status} Ready"

    def create_menu(self):
        """Create the system tray menu"""
        return pystray.Menu(
            pystray.MenuItem(self.get_status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⏱ Quick Start", pystray.Menu(
                pystray.MenuItem("25 minutes", lambda icon, item: self.start_session(25)),
                pystray.MenuItem("45 minutes", lambda icon, item: self.start_session(45)),
                pystray.MenuItem("1 hour", lambda icon, item: self.start_session(60)),
                pystray.MenuItem("2 hours", lambda icon, item: self.start_session(120)),
                pystray.MenuItem("4 hours", lambda icon, item: self.start_session(240)),
            )),
            pystray.MenuItem("⬛ Stop Session", self.stop_session,
                           enabled=self.is_blocking),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🖥 Open Full App", self.open_full_app),
            pystray.MenuItem("❌ Exit", self.exit_app),
        )

    def open_full_app(self, icon=None, item=None):
        """Open the full GUI application"""
        # Try exe first
        exe_path = SCRIPT_DIR / "dist" / "PersonalFreedom.exe"
        if not exe_path.exists():
            exe_path = SCRIPT_DIR / "PersonalFreedom.exe"

        if exe_path.exists():
            print(f"Opening: {exe_path}")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", str(exe_path), None, str(SCRIPT_DIR), 1
            )
            return

        # Fall back to Python script
        main_script = SCRIPT_DIR / "focus_blocker.py"
        if main_script.exists():
            print(f"Opening: {main_script}")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{main_script}"', str(SCRIPT_DIR), 1
            )

    def exit_app(self, icon=None, item=None):
        """Exit the application"""
        print("Exiting...")
        if self.is_blocking:
            self.unblock_sites()
        self._stop_event.set()
        if self.icon:
            self.icon.stop()

    def run(self):
        """Run the system tray application"""
        print("=" * 50)
        print("  Personal Freedom - System Tray")
        print("=" * 50)
        print(f"Admin privileges: {'Yes ✓' if is_admin() else 'No ✗'}")
        print(f"Sites loaded: {len(self.blacklist)}")
        print()

        if not is_admin():
            print("WARNING: Running without admin - blocking will NOT work!")
            print()

        print("Right-click the tray icon to access the menu.")
        print("=" * 50)

        self.icon = pystray.Icon(
            "PersonalFreedom",
            self.create_icon_image(False),
            "Personal Freedom - Focus Blocker",
            self.create_menu()
        )

        # Show startup notification
        def after_setup(icon):
            if is_admin():
                icon.notify("Right-click the icon to start a focus session", "Personal Freedom Ready")
            else:
                icon.notify("Running without admin - blocking won't work!\nRight-click > Open Full App", "⚠️ Admin Required")

        self.icon.run(setup=after_setup)


def main():
    # Add a small delay to ensure window is ready
    import time

    print("Personal Freedom Tray starting...")
    print(f"Python: {sys.executable}")
    print(f"Script: {sys.argv[0]}")
    print(f"Working dir: {os.getcwd()}")
    print()

    # Check admin and offer to elevate
    if not is_admin():
        print("Not running as administrator.")
        print()

        # Try to show a dialog
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            result = messagebox.askyesno(
                "Administrator Required",
                "Personal Freedom needs administrator privileges to block websites.\n\n"
                "Without admin rights, blocking will NOT work.\n\n"
                "Restart as administrator?",
                icon='warning'
            )
            root.destroy()

            if result:
                if request_admin_and_restart():
                    print("Elevated process started. Exiting this instance.")
                    sys.exit(0)
                else:
                    print("Failed to elevate. Running without admin...")
        except Exception as e:
            print(f"Could not show dialog: {e}")
            print("Running without admin privileges...")
    else:
        print("Running with administrator privileges ✓")

    # Change to script directory
    os.chdir(SCRIPT_DIR)
    print(f"Changed to: {SCRIPT_DIR}")

    # Run the app
    try:
        app = TrayBlocker()
        app.run()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
