"""
System Tray version of Personal Freedom - Focus Blocker
Runs minimized in the system tray for unobtrusive operation.
"""

import pystray
from PIL import Image, ImageDraw
import threading
import time
import os
import sys
import json
import ctypes
import subprocess
import re
from pathlib import Path

# Windows hosts file path
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"
MARKER_START = "# === PERSONAL FREEDOM BLOCK START ==="
MARKER_END = "# === PERSONAL FREEDOM BLOCK END ==="

# Config file path
CONFIG_PATH = Path(__file__).parent / "config.json"

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


class TrayBlocker:
    def __init__(self):
        self.blacklist = []
        self.is_blocking = False
        self.remaining_seconds = 0
        self.timer_thread = None
        self.icon = None
        self.load_config()
    
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
    
    def block_sites(self):
        """Add blocked sites to hosts file"""
        if not self.is_admin():
            return False
        
        if not self.blacklist:
            return False
        
        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if MARKER_START in content and MARKER_END in content:
                start_idx = content.find(MARKER_START)
                end_idx = content.find(MARKER_END) + len(MARKER_END)
                if start_idx < end_idx:
                    content = content[:start_idx] + content[end_idx:]
            
            block_entries = [f"\n{MARKER_START}"]
            for site in self.blacklist:
                clean_site = site.strip().lower()
                if clean_site and self._is_valid_hostname(clean_site):
                    block_entries.append(f"{REDIRECT_IP} {clean_site}")
            block_entries.append(f"{MARKER_END}\n")
            
            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n' + '\n'.join(block_entries))
            
            self.is_blocking = True
            self._flush_dns()
            return True
        except Exception:
            return False
    
    def unblock_sites(self):
        """Remove blocked sites from hosts file"""
        if not self.is_admin():
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
            return True
        except Exception:
            return False
    
    def format_time(self, seconds):
        """Format seconds to HH:MM:SS"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def start_session(self, minutes):
        """Start a focus session"""
        def timer_callback():
            self.remaining_seconds = minutes * 60
            self.block_sites()
            self.update_icon()
            
            while self.remaining_seconds > 0 and self.is_blocking:
                time.sleep(1)
                self.remaining_seconds -= 1
                self.update_menu()
            
            if self.is_blocking:
                self.unblock_sites()
                self.update_icon()
                self.show_notification("Focus Complete!", "Your focus session has ended.")
        
        self.timer_thread = threading.Thread(target=timer_callback, daemon=True)
        self.timer_thread.start()
    
    def stop_session(self, icon=None, item=None):
        """Stop the current session"""
        self.remaining_seconds = 0
        self.unblock_sites()
        self.update_icon()
    
    def update_icon(self):
        """Update the tray icon"""
        if self.icon:
            self.icon.icon = self.create_icon_image(self.is_blocking)
    
    def update_menu(self):
        """Update the menu (for timer display)"""
        if self.icon:
            self.icon.update_menu()
    
    def show_notification(self, title, message):
        """Show a system notification"""
        if self.icon:
            self.icon.notify(message, title)
    
    def create_menu(self):
        """Create the system tray menu"""
        def get_status():
            if self.is_blocking:
                return f"🔒 Blocking - {self.format_time(self.remaining_seconds)}"
            return "✅ Not Blocking"
        
        return pystray.Menu(
            pystray.MenuItem(get_status, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⏱ Quick Start", pystray.Menu(
                pystray.MenuItem("25 minutes", lambda: self.start_session(25)),
                pystray.MenuItem("45 minutes", lambda: self.start_session(45)),
                pystray.MenuItem("1 hour", lambda: self.start_session(60)),
                pystray.MenuItem("2 hours", lambda: self.start_session(120)),
                pystray.MenuItem("4 hours", lambda: self.start_session(240)),
            )),
            pystray.MenuItem("⬛ Stop Session", self.stop_session, 
                           enabled=lambda item: self.is_blocking),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🖥 Open Full App", self.open_full_app),
            pystray.MenuItem("❌ Exit", self.exit_app),
        )
    
    def open_full_app(self, icon=None, item=None):
        """Open the full GUI application"""
        script_dir = Path(__file__).parent
        main_script = script_dir / "focus_blocker.py"
        if main_script.exists():
            os.system(f'start pythonw "{main_script}"')
    
    def exit_app(self, icon=None, item=None):
        """Exit the application"""
        if self.is_blocking:
            self.unblock_sites()
        if self.icon:
            self.icon.stop()
    
    def run(self):
        """Run the system tray application"""
        if not self.is_admin():
            print("Warning: Not running as administrator. Blocking will not work.")
        
        self.icon = pystray.Icon(
            "PersonalFreedom",
            self.create_icon_image(False),
            "Personal Freedom",
            self.create_menu()
        )
        self.icon.run()


def main():
    app = TrayBlocker()
    app.run()


if __name__ == "__main__":
    main()
