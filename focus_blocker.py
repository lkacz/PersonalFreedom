"""
Personal Freedom - Website Blocker for Focus Time
A Windows application to block distracting websites during focus sessions.

Enhanced Version with Industry-Standard Features:
- Multiple blocking modes (Strict, Normal, Pomodoro)
- Schedule-based blocking
- Statistics and productivity tracking
- Password protection
- Break reminders
- Import/Export blacklists
- Website categories
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import time
import os
import sys
import json
import ctypes
import subprocess
import re
import hashlib
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Windows hosts file path
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"
MARKER_START = "# === PERSONAL FREEDOM BLOCK START ==="
MARKER_END = "# === PERSONAL FREEDOM BLOCK END ==="

# Config file paths
APP_DIR = Path(__file__).parent
CONFIG_PATH = APP_DIR / "config.json"
STATS_PATH = APP_DIR / "stats.json"

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


class FocusBlocker:
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
        
        # Statistics
        self.stats = self._default_stats()
        
        self.load_config()
        self.load_stats()
    
    def _default_stats(self):
        return {
            "total_focus_time": 0,
            "sessions_completed": 0,
            "sessions_cancelled": 0,
            "daily_stats": {},
            "streak_days": 0,
            "last_session_date": None,
            "best_streak": 0,
        }
    
    def load_config(self):
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
                    self.categories_enabled = config.get('categories_enabled', 
                        {cat: True for cat in SITE_CATEGORIES})
                    self.password_hash = config.get('password_hash')
                    self.pomodoro_work = config.get('pomodoro_work', 25)
                    self.pomodoro_break = config.get('pomodoro_break', 5)
                    self.pomodoro_long_break = config.get('pomodoro_long_break', 15)
                    self.schedules = config.get('schedules', [])
            except (json.JSONDecodeError, IOError, OSError):
                self.blacklist = default_blacklist
                self.categories_enabled = {cat: True for cat in SITE_CATEGORIES}
        else:
            self.blacklist = default_blacklist
            self.categories_enabled = {cat: True for cat in SITE_CATEGORIES}
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
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
            }
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except (IOError, OSError) as e:
            print(f"Warning: Could not save config: {e}")
    
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
        """Save statistics to file"""
        try:
            with open(STATS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2)
        except (IOError, OSError):
            pass
    
    def update_stats(self, focus_seconds, completed=True):
        """Update session statistics"""
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
    
    def set_password(self, password):
        """Set a password for strict mode"""
        if password:
            self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        else:
            self.password_hash = None
        self.save_config()
    
    def verify_password(self, password):
        """Verify the password"""
        if not self.password_hash:
            return True
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
    
    def is_admin(self):
        """Check if running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
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
    
    def _flush_dns(self):
        """Flush DNS cache safely"""
        try:
            subprocess.run(['ipconfig', '/flushdns'], capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass
    
    def get_effective_blacklist(self):
        """Get the effective blacklist considering categories and whitelist"""
        effective = set()
        
        for category, enabled in self.categories_enabled.items():
            if enabled and category in SITE_CATEGORIES:
                effective.update(SITE_CATEGORIES[category])
        
        effective.update(self.blacklist)
        effective -= set(self.whitelist)
        
        return list(effective)
    
    def block_sites(self):
        """Add blocked sites to hosts file"""
        if not self.is_admin():
            return False, "Administrator privileges required!"
        
        sites_to_block = self.get_effective_blacklist()
        if not sites_to_block:
            return False, "No sites to block!"
        
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
            return True, f"Blocking {len(sites_to_block)} sites!"
        
        except PermissionError:
            return False, "Permission denied! Run as Administrator."
        except FileNotFoundError:
            return False, "Hosts file not found!"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def unblock_sites(self, password=None):
        """Remove blocked sites from hosts file"""
        if not self.is_admin():
            return False, "Administrator privileges required!"
        
        if self.mode == BlockMode.STRICT and self.is_blocking:
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
                if start <= current_time <= end:
                    return True
        return False


class FocusBlockerGUI:
    """Enhanced GUI with tabbed interface"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Freedom - Focus Blocker")
        self.root.geometry("600x700")
        self.root.minsize(550, 600)
        
        self.blocker = FocusBlocker()
        self.timer_running = False
        self.remaining_seconds = 0
        self._timer_lock = threading.Lock()
        self.session_start_time = None
        
        # Apply theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_styles()
        
        self.setup_ui()
        self.check_admin_status()
        self.update_stats_display()
        
        # Check for scheduled blocking
        self.check_scheduled_blocking()
    
    def _configure_styles(self):
        """Configure custom styles"""
        self.style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'))
        self.style.configure('Timer.TLabel', font=('Consolas', 42, 'bold'))
        self.style.configure('Status.TLabel', font=('Segoe UI', 11, 'bold'))
        self.style.configure('Stats.TLabel', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))
        
        # Button styles
        self.style.configure('Start.TButton', font=('Segoe UI', 10, 'bold'))
        self.style.configure('Stop.TButton', font=('Segoe UI', 10))
        self.style.configure('Category.TCheckbutton', font=('Segoe UI', 10))
    
    def setup_ui(self):
        """Setup the tabbed user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="🔒 Personal Freedom", 
                  style='Title.TLabel').pack(side=tk.LEFT)
        
        self.admin_label = ttk.Label(header_frame, text="", font=('Segoe UI', 9))
        self.admin_label.pack(side=tk.RIGHT, padx=10)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Timer
        self.timer_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.timer_tab, text="⏱ Timer")
        self.setup_timer_tab()
        
        # Tab 2: Sites
        self.sites_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.sites_tab, text="🌐 Sites")
        self.setup_sites_tab()
        
        # Tab 3: Categories
        self.categories_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.categories_tab, text="📁 Categories")
        self.setup_categories_tab()
        
        # Tab 4: Schedule
        self.schedule_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.schedule_tab, text="📅 Schedule")
        self.setup_schedule_tab()
        
        # Tab 5: Stats
        self.stats_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.stats_tab, text="📊 Stats")
        self.setup_stats_tab()
        
        # Tab 6: Settings
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="⚙ Settings")
        self.setup_settings_tab()
    
    def setup_timer_tab(self):
        """Setup the timer tab"""
        # Timer display
        timer_frame = ttk.LabelFrame(self.timer_tab, text="Focus Timer", padding="15")
        timer_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.timer_display = ttk.Label(timer_frame, text="00:00:00", style='Timer.TLabel')
        self.timer_display.pack(pady=15)
        
        # Mode selection
        mode_frame = ttk.Frame(timer_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="Mode:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value=BlockMode.NORMAL)
        
        modes = [("Normal", BlockMode.NORMAL), ("Strict 🔐", BlockMode.STRICT), 
                 ("Pomodoro 🍅", BlockMode.POMODORO)]
        for text, mode in modes:
            ttk.Radiobutton(mode_frame, text=text, value=mode, 
                           variable=self.mode_var).pack(side=tk.LEFT, padx=10)
        
        # Time input
        time_frame = ttk.Frame(timer_frame)
        time_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(time_frame, text="Duration:").pack(side=tk.LEFT, padx=5)
        
        self.hours_var = tk.StringVar(value="0")
        ttk.Spinbox(time_frame, from_=0, to=12, width=4, 
                    textvariable=self.hours_var).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame, text="h").pack(side=tk.LEFT)
        
        self.minutes_var = tk.StringVar(value="25")
        ttk.Spinbox(time_frame, from_=0, to=59, width=4,
                    textvariable=self.minutes_var).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame, text="m").pack(side=tk.LEFT)
        
        # Quick buttons
        quick_frame = ttk.Frame(timer_frame)
        quick_frame.pack(fill=tk.X, pady=10)
        
        presets = [("25m", 25), ("45m", 45), ("1h", 60), ("2h", 120), ("4h", 240)]
        for text, mins in presets:
            ttk.Button(quick_frame, text=text, width=6,
                      command=lambda m=mins: self.set_quick_time(m)).pack(side=tk.LEFT, padx=3, expand=True)
        
        # Control buttons
        btn_frame = ttk.Frame(timer_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ Start Focus", 
                                    command=self.start_session, style='Start.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.stop_btn = ttk.Button(btn_frame, text="⬛ Stop", 
                                   command=self.stop_session, style='Stop.TButton', 
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Status
        self.status_label = ttk.Label(timer_frame, text="Ready to focus", 
                                      style='Status.TLabel')
        self.status_label.pack(pady=5)
        
        # Quick stats
        stats_frame = ttk.LabelFrame(self.timer_tab, text="Today's Progress", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.quick_stats_label = ttk.Label(stats_frame, text="", style='Stats.TLabel')
        self.quick_stats_label.pack()
    
    def setup_sites_tab(self):
        """Setup the sites management tab"""
        # Blacklist frame
        black_frame = ttk.LabelFrame(self.sites_tab, text="Blocked Sites (Custom)", padding="10")
        black_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(black_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.site_listbox = tk.Listbox(list_frame, height=10, font=('Consolas', 10),
                                       yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
        self.site_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.site_listbox.yview)
        
        # Add/Remove controls
        ctrl_frame = ttk.Frame(black_frame)
        ctrl_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.site_entry = ttk.Entry(ctrl_frame, font=('Segoe UI', 10))
        self.site_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.site_entry.bind('<Return>', lambda e: self.add_site())
        
        ttk.Button(ctrl_frame, text="+ Add", command=self.add_site, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="- Remove", command=self.remove_site, width=8).pack(side=tk.LEFT, padx=2)
        
        # Whitelist frame
        white_frame = ttk.LabelFrame(self.sites_tab, text="Whitelist (Never Block)", padding="10")
        white_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        list_frame2 = ttk.Frame(white_frame)
        list_frame2.pack(fill=tk.BOTH, expand=True)
        
        scrollbar2 = ttk.Scrollbar(list_frame2)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.whitelist_listbox = tk.Listbox(list_frame2, height=6, font=('Consolas', 10),
                                            yscrollcommand=scrollbar2.set)
        self.whitelist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.config(command=self.whitelist_listbox.yview)
        
        ctrl_frame2 = ttk.Frame(white_frame)
        ctrl_frame2.pack(fill=tk.X, pady=(10, 0))
        
        self.whitelist_entry = ttk.Entry(ctrl_frame2, font=('Segoe UI', 10))
        self.whitelist_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(ctrl_frame2, text="+ Add", command=self.add_whitelist, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame2, text="- Remove", command=self.remove_whitelist, width=8).pack(side=tk.LEFT, padx=2)
        
        # Import/Export
        io_frame = ttk.Frame(self.sites_tab)
        io_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(io_frame, text="📥 Import", command=self.import_sites).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="📤 Export", command=self.export_sites).pack(side=tk.LEFT, padx=5)
        
        self.update_site_lists()
    
    def setup_categories_tab(self):
        """Setup the categories tab"""
        ttk.Label(self.categories_tab, text="Enable/disable entire categories of sites:",
                  style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        self.category_vars = {}
        
        for category, sites in SITE_CATEGORIES.items():
            frame = ttk.Frame(self.categories_tab)
            frame.pack(fill=tk.X, pady=3)
            
            var = tk.BooleanVar(value=self.blocker.categories_enabled.get(category, True))
            self.category_vars[category] = var
            
            cb = ttk.Checkbutton(frame, text=f"{category} ({len(sites)} sites)", 
                                variable=var, style='Category.TCheckbutton',
                                command=lambda c=category: self.toggle_category(c))
            cb.pack(side=tk.LEFT)
            
            # Show sites button
            ttk.Button(frame, text="View", width=6,
                      command=lambda c=category: self.show_category_sites(c)).pack(side=tk.RIGHT)
        
        # Total count
        ttk.Separator(self.categories_tab).pack(fill=tk.X, pady=15)
        
        self.total_sites_label = ttk.Label(self.categories_tab, text="", style='Stats.TLabel')
        self.total_sites_label.pack()
        self.update_total_sites_count()
    
    def setup_schedule_tab(self):
        """Setup the schedule tab"""
        ttk.Label(self.schedule_tab, text="Automatic blocking schedules:",
                  style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Schedule list
        list_frame = ttk.Frame(self.schedule_tab)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('days', 'time', 'status')
        self.schedule_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        self.schedule_tree.heading('days', text='Days')
        self.schedule_tree.heading('time', text='Time')
        self.schedule_tree.heading('status', text='Status')
        self.schedule_tree.column('days', width=200)
        self.schedule_tree.column('time', width=150)
        self.schedule_tree.column('status', width=80)
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, command=self.schedule_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.schedule_tree.configure(yscrollcommand=scrollbar.set)
        
        # Add schedule controls
        add_frame = ttk.LabelFrame(self.schedule_tab, text="Add Schedule", padding="10")
        add_frame.pack(fill=tk.X, pady=10)
        
        # Days selection
        days_frame = ttk.Frame(add_frame)
        days_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(days_frame, text="Days:").pack(side=tk.LEFT, padx=5)
        
        self.day_vars = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            var = tk.BooleanVar(value=i < 5)  # Default: weekdays
            self.day_vars.append(var)
            ttk.Checkbutton(days_frame, text=day, variable=var).pack(side=tk.LEFT, padx=3)
        
        # Time selection
        time_frame = ttk.Frame(add_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.start_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.start_hour.set("09")
        self.start_hour.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.start_min = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.start_min.set("00")
        self.start_min.pack(side=tk.LEFT)
        
        ttk.Label(time_frame, text="  To:").pack(side=tk.LEFT, padx=5)
        self.end_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.end_hour.set("17")
        self.end_hour.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.end_min = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.end_min.set("00")
        self.end_min.pack(side=tk.LEFT)
        
        ttk.Button(add_frame, text="+ Add Schedule", command=self.add_schedule).pack(pady=10)
        
        # Schedule actions
        action_frame = ttk.Frame(self.schedule_tab)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="Toggle", command=self.toggle_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete", command=self.delete_schedule).pack(side=tk.LEFT, padx=5)
        
        self.update_schedule_list()
    
    def setup_stats_tab(self):
        """Setup the statistics tab"""
        # Overview
        overview_frame = ttk.LabelFrame(self.stats_tab, text="Overview", padding="15")
        overview_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_grid = ttk.Frame(overview_frame)
        stats_grid.pack()
        
        self.stat_labels = {}
        stats = [
            ("total_hours", "Total Focus Time", "0h"),
            ("sessions", "Sessions Completed", "0"),
            ("streak", "Current Streak", "0 days"),
            ("best_streak", "Best Streak", "0 days"),
        ]
        
        for i, (key, label, default) in enumerate(stats):
            row, col = divmod(i, 2)
            frame = ttk.Frame(stats_grid)
            frame.grid(row=row, column=col, padx=20, pady=10)
            
            ttk.Label(frame, text=label, font=('Segoe UI', 9)).pack()
            self.stat_labels[key] = ttk.Label(frame, text=default, 
                                              font=('Segoe UI', 18, 'bold'))
            self.stat_labels[key].pack()
        
        # Weekly chart (simple text-based)
        week_frame = ttk.LabelFrame(self.stats_tab, text="This Week", padding="15")
        week_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.week_chart = tk.Text(week_frame, height=10, font=('Consolas', 10), 
                                  state=tk.DISABLED, bg='#f5f5f5')
        self.week_chart.pack(fill=tk.BOTH, expand=True)
        
        # Reset button
        ttk.Button(self.stats_tab, text="Reset Statistics", 
                   command=self.reset_stats).pack(pady=10)
    
    def setup_settings_tab(self):
        """Setup the settings tab"""
        # Password protection
        pwd_frame = ttk.LabelFrame(self.settings_tab, text="Password Protection", padding="10")
        pwd_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pwd_frame, text="Set a password to prevent stopping Strict Mode sessions early.",
                  wraplength=400).pack(anchor=tk.W)
        
        pwd_btn_frame = ttk.Frame(pwd_frame)
        pwd_btn_frame.pack(fill=tk.X, pady=10)
        
        self.pwd_status = ttk.Label(pwd_btn_frame, text="No password set")
        self.pwd_status.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(pwd_btn_frame, text="Set Password", 
                   command=self.set_password).pack(side=tk.RIGHT, padx=5)
        ttk.Button(pwd_btn_frame, text="Remove Password", 
                   command=self.remove_password).pack(side=tk.RIGHT, padx=5)
        
        self.update_password_status()
        
        # Pomodoro settings
        pomo_frame = ttk.LabelFrame(self.settings_tab, text="Pomodoro Settings", padding="10")
        pomo_frame.pack(fill=tk.X, pady=10)
        
        settings = [
            ("Work duration (min):", "pomodoro_work", self.blocker.pomodoro_work),
            ("Short break (min):", "pomodoro_break", self.blocker.pomodoro_break),
            ("Long break (min):", "pomodoro_long_break", self.blocker.pomodoro_long_break),
        ]
        
        self.pomo_vars = {}
        for label, key, default in settings:
            frame = ttk.Frame(pomo_frame)
            frame.pack(fill=tk.X, pady=3)
            ttk.Label(frame, text=label, width=20).pack(side=tk.LEFT)
            var = tk.StringVar(value=str(default))
            self.pomo_vars[key] = var
            ttk.Spinbox(frame, from_=1, to=120, width=5, textvariable=var).pack(side=tk.LEFT)
        
        ttk.Button(pomo_frame, text="Save Pomodoro Settings", 
                   command=self.save_pomodoro_settings).pack(pady=10)
        
        # About
        about_frame = ttk.LabelFrame(self.settings_tab, text="About", padding="10")
        about_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(about_frame, text="Personal Freedom v2.0", 
                  font=('Segoe UI', 11, 'bold')).pack()
        ttk.Label(about_frame, text="A focus and productivity tool for Windows",
                  font=('Segoe UI', 9)).pack()
        ttk.Label(about_frame, text="Block distracting websites and track your progress.",
                  font=('Segoe UI', 9)).pack()
    
    # === Timer Tab Methods ===
    
    def check_admin_status(self):
        """Check and display admin status"""
        if self.blocker.is_admin():
            self.admin_label.config(text="✅ Admin", foreground='green')
        else:
            self.admin_label.config(text="⚠ Not Admin", foreground='red')
    
    def set_quick_time(self, minutes):
        """Set quick timer values"""
        self.hours_var.set(str(minutes // 60))
        self.minutes_var.set(str(minutes % 60))
    
    def start_session(self):
        """Start a focus session"""
        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid time values")
            return
        
        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            messagebox.showerror("Error", "Please set a time greater than 0")
            return
        
        # Set mode
        self.blocker.mode = self.mode_var.get()
        
        # Block sites
        success, message = self.blocker.block_sites()
        if not success:
            messagebox.showerror("Error", message)
            return
        
        # Start timer
        with self._timer_lock:
            self.remaining_seconds = total_minutes * 60
            self.timer_running = True
            self.session_start_time = time.time()
        
        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        mode_text = {"normal": "BLOCKING", "strict": "STRICT MODE 🔐", 
                     "pomodoro": "POMODORO 🍅"}.get(self.blocker.mode, "BLOCKING")
        self.status_label.config(text=f"🔒 {mode_text}", foreground='red')
        
        # Start timer thread
        threading.Thread(target=self.run_timer, daemon=True).start()
        
        messagebox.showinfo("Focus Session", f"Blocking {len(self.blocker.get_effective_blacklist())} sites for {hours}h {minutes}m\nStay focused! 💪")
    
    def run_timer(self):
        """Run the countdown timer"""
        while True:
            with self._timer_lock:
                if not self.timer_running or self.remaining_seconds <= 0:
                    break
                
                h = self.remaining_seconds // 3600
                m = (self.remaining_seconds % 3600) // 60
                s = self.remaining_seconds % 60
                time_str = f"{h:02d}:{m:02d}:{s:02d}"
                self.remaining_seconds -= 1
            
            try:
                self.root.after(0, lambda t=time_str: self.timer_display.config(text=t))
            except tk.TclError:
                break
            
            time.sleep(1)
        
        with self._timer_lock:
            if self.remaining_seconds <= 0 and self.timer_running:
                try:
                    self.root.after(0, self.session_complete)
                except tk.TclError:
                    pass
    
    def session_complete(self):
        """Handle session completion"""
        elapsed = int(time.time() - self.session_start_time) if self.session_start_time else 0
        self.blocker.update_stats(elapsed, completed=True)
        
        self.stop_session(show_message=False)
        self.timer_display.config(text="00:00:00")
        self.update_stats_display()
        
        messagebox.showinfo("Complete!", "🎉 Focus session complete!\nGreat job staying focused!")
    
    def stop_session(self, show_message=True):
        """Stop the focus session"""
        # Check strict mode
        if self.blocker.mode == BlockMode.STRICT and self.blocker.is_blocking:
            if self.blocker.password_hash:
                password = simpledialog.askstring("Strict Mode", "Enter password to stop:", show='*')
                if not self.blocker.verify_password(password or ""):
                    messagebox.showerror("Error", "Incorrect password!")
                    return
        
        elapsed = int(time.time() - self.session_start_time) if self.session_start_time else 0
        
        with self._timer_lock:
            was_running = self.timer_running
            self.timer_running = False
            self.remaining_seconds = 0
        
        success, message = self.blocker.unblock_sites()
        
        if was_running and elapsed > 60:  # Only count if > 1 minute
            self.blocker.update_stats(elapsed, completed=False)
        
        # Update UI
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Ready to focus", foreground='black')
            self.timer_display.config(text="00:00:00")
            self.update_stats_display()
        except tk.TclError:
            pass
        
        if show_message:
            messagebox.showinfo("Stopped", "Session stopped. Sites unblocked.")
    
    def update_stats_display(self):
        """Update statistics displays"""
        stats = self.blocker.get_stats_summary()
        
        # Quick stats on timer tab
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.blocker.stats.get("daily_stats", {}).get(today, {})
        today_time = daily.get("focus_time", 0) // 60
        today_sessions = daily.get("sessions", 0)
        
        self.quick_stats_label.config(
            text=f"Today: {today_time} min focused • {today_sessions} sessions • 🔥 {stats['current_streak']} day streak"
        )
        
        # Stats tab
        if hasattr(self, 'stat_labels'):
            self.stat_labels['total_hours'].config(text=f"{stats['total_hours']}h")
            self.stat_labels['sessions'].config(text=str(stats['sessions_completed']))
            self.stat_labels['streak'].config(text=f"{stats['current_streak']} days")
            self.stat_labels['best_streak'].config(text=f"{stats['best_streak']} days")
            
            self.update_week_chart()
    
    def update_week_chart(self):
        """Update the weekly chart"""
        self.week_chart.config(state=tk.NORMAL)
        self.week_chart.delete(1.0, tk.END)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        today = datetime.now()
        
        chart_lines = []
        max_time = 1
        
        # Get data for last 7 days
        week_data = []
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.blocker.stats.get("daily_stats", {}).get(date, {})
            time_min = daily.get("focus_time", 0) // 60
            week_data.append((date, time_min))
            max_time = max(max_time, time_min)
        
        # Create ASCII bar chart
        chart_lines.append("Focus time this week:\n\n")
        
        for date_str, time_min in week_data:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = days[date.weekday()]
            bar_len = int((time_min / max_time) * 30) if max_time > 0 else 0
            bar = "█" * bar_len + "░" * (30 - bar_len)
            chart_lines.append(f"  {day_name}  {bar} {time_min}m\n")
        
        total_week = sum(t for _, t in week_data)
        chart_lines.append(f"\n  Total this week: {total_week} minutes ({total_week // 60}h {total_week % 60}m)")
        
        self.week_chart.insert(tk.END, "".join(chart_lines))
        self.week_chart.config(state=tk.DISABLED)
    
    # === Sites Tab Methods ===
    
    def update_site_lists(self):
        """Update both site listboxes"""
        self.site_listbox.delete(0, tk.END)
        for site in sorted(self.blocker.blacklist):
            self.site_listbox.insert(tk.END, site)
        
        self.whitelist_listbox.delete(0, tk.END)
        for site in sorted(self.blocker.whitelist):
            self.whitelist_listbox.insert(tk.END, site)
    
    def add_site(self):
        """Add a site to blacklist"""
        site = self.site_entry.get().strip()
        if site and self.blocker.add_site(site):
            self.update_site_lists()
            self.site_entry.delete(0, tk.END)
            self.update_total_sites_count()
        elif site:
            messagebox.showinfo("Info", "Site already in list or invalid")
    
    def remove_site(self):
        """Remove selected sites from blacklist"""
        selection = self.site_listbox.curselection()
        for i in reversed(selection):
            site = self.site_listbox.get(i)
            self.blocker.remove_site(site)
        self.update_site_lists()
        self.update_total_sites_count()
    
    def add_whitelist(self):
        """Add a site to whitelist"""
        site = self.whitelist_entry.get().strip()
        if site and self.blocker.add_to_whitelist(site):
            self.update_site_lists()
            self.whitelist_entry.delete(0, tk.END)
            self.update_total_sites_count()
    
    def remove_whitelist(self):
        """Remove selected site from whitelist"""
        selection = self.whitelist_listbox.curselection()
        if selection:
            site = self.whitelist_listbox.get(selection[0])
            self.blocker.remove_from_whitelist(site)
            self.update_site_lists()
            self.update_total_sites_count()
    
    def import_sites(self):
        """Import sites from file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if filepath and self.blocker.import_config(filepath):
            self.update_site_lists()
            self.update_total_sites_count()
            messagebox.showinfo("Success", "Sites imported successfully!")
    
    def export_sites(self):
        """Export sites to file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")])
        if filepath and self.blocker.export_config(filepath):
            messagebox.showinfo("Success", "Sites exported successfully!")
    
    # === Categories Tab Methods ===
    
    def toggle_category(self, category):
        """Toggle a category on/off"""
        self.blocker.categories_enabled[category] = self.category_vars[category].get()
        self.blocker.save_config()
        self.update_total_sites_count()
    
    def show_category_sites(self, category):
        """Show sites in a category"""
        sites = SITE_CATEGORIES.get(category, [])
        site_list = "\n".join(sorted(set(s.replace("www.", "") for s in sites)))
        messagebox.showinfo(f"{category} Sites", site_list)
    
    def update_total_sites_count(self):
        """Update total blocked sites count"""
        total = len(self.blocker.get_effective_blacklist())
        self.total_sites_label.config(text=f"Total sites to block: {total}")
    
    # === Schedule Tab Methods ===
    
    def update_schedule_list(self):
        """Update the schedule treeview"""
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for schedule in self.blocker.schedules:
            day_names = ", ".join(days[d] for d in sorted(schedule.get('days', [])))
            time_range = f"{schedule.get('start_time', '')} - {schedule.get('end_time', '')}"
            status = "✅ Active" if schedule.get('enabled', True) else "⏸ Paused"
            
            self.schedule_tree.insert('', tk.END, iid=schedule['id'],
                                      values=(day_names, time_range, status))
    
    def add_schedule(self):
        """Add a new schedule"""
        days = [i for i, var in enumerate(self.day_vars) if var.get()]
        if not days:
            messagebox.showerror("Error", "Select at least one day")
            return
        
        start_time = f"{int(self.start_hour.get()):02d}:{int(self.start_min.get()):02d}"
        end_time = f"{int(self.end_hour.get()):02d}:{int(self.end_min.get()):02d}"
        
        self.blocker.add_schedule(days, start_time, end_time)
        self.update_schedule_list()
    
    def toggle_schedule(self):
        """Toggle selected schedule"""
        selection = self.schedule_tree.selection()
        if selection:
            self.blocker.toggle_schedule(selection[0])
            self.update_schedule_list()
    
    def delete_schedule(self):
        """Delete selected schedule"""
        selection = self.schedule_tree.selection()
        if selection:
            self.blocker.remove_schedule(selection[0])
            self.update_schedule_list()
    
    def check_scheduled_blocking(self):
        """Check if we should be blocking based on schedule"""
        if self.blocker.is_scheduled_block_time() and not self.blocker.is_blocking:
            if messagebox.askyesno("Scheduled Block", 
                                   "You have a blocking schedule active now.\nStart blocking?"):
                self.blocker.mode = BlockMode.SCHEDULED
                self.blocker.block_sites()
                self.status_label.config(text="🔒 SCHEDULED BLOCK", foreground='red')
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
        
        # Check again in 60 seconds
        self.root.after(60000, self.check_scheduled_blocking)
    
    # === Stats Tab Methods ===
    
    def reset_stats(self):
        """Reset all statistics"""
        if messagebox.askyesno("Reset Stats", "Are you sure you want to reset all statistics?"):
            self.blocker.stats = self.blocker._default_stats()
            self.blocker.save_stats()
            self.update_stats_display()
    
    # === Settings Tab Methods ===
    
    def set_password(self):
        """Set strict mode password"""
        password = simpledialog.askstring("Set Password", "Enter new password:", show='*')
        if password:
            confirm = simpledialog.askstring("Confirm", "Confirm password:", show='*')
            if password == confirm:
                self.blocker.set_password(password)
                self.update_password_status()
                messagebox.showinfo("Success", "Password set!")
            else:
                messagebox.showerror("Error", "Passwords don't match")
    
    def remove_password(self):
        """Remove password"""
        if self.blocker.password_hash:
            password = simpledialog.askstring("Remove Password", "Enter current password:", show='*')
            if self.blocker.verify_password(password or ""):
                self.blocker.set_password(None)
                self.update_password_status()
            else:
                messagebox.showerror("Error", "Incorrect password")
        else:
            messagebox.showinfo("Info", "No password set")
    
    def update_password_status(self):
        """Update password status label"""
        if self.blocker.password_hash:
            self.pwd_status.config(text="🔐 Password is set", foreground='green')
        else:
            self.pwd_status.config(text="No password set", foreground='gray')
    
    def save_pomodoro_settings(self):
        """Save Pomodoro settings"""
        try:
            self.blocker.pomodoro_work = int(self.pomo_vars['pomodoro_work'].get())
            self.blocker.pomodoro_break = int(self.pomo_vars['pomodoro_break'].get())
            self.blocker.pomodoro_long_break = int(self.pomo_vars['pomodoro_long_break'].get())
            self.blocker.save_config()
            messagebox.showinfo("Success", "Pomodoro settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Invalid values")
    
    def on_closing(self):
        """Handle window close"""
        if self.timer_running:
            if messagebox.askyesno("Confirm Exit", "A session is running!\nStop and exit?"):
                self.stop_session(show_message=False)
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = FocusBlockerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
