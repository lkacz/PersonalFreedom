"""
Personal Freedom - Website Blocker for Focus Time
A Windows application to block distracting websites during focus sessions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
    "facebook.com",
    "www.facebook.com",
    "youtube.com",
    "www.youtube.com",
    "twitter.com",
    "www.twitter.com",
    "x.com",
    "www.x.com",
    "instagram.com",
    "www.instagram.com",
    "tiktok.com",
    "www.tiktok.com",
    "reddit.com",
    "www.reddit.com",
    "netflix.com",
    "www.netflix.com",
    "twitch.tv",
    "www.twitch.tv",
]


class FocusBlocker:
    def __init__(self):
        self.blacklist = []
        self.is_blocking = False
        self.end_time = None
        self.timer_thread = None
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    loaded_list = config.get('blacklist', [])
                    # Validate loaded list
                    if isinstance(loaded_list, list) and all(isinstance(s, str) for s in loaded_list):
                        self.blacklist = loaded_list if loaded_list else DEFAULT_BLACKLIST.copy()
                    else:
                        self.blacklist = DEFAULT_BLACKLIST.copy()
            except (json.JSONDecodeError, IOError, OSError):
                self.blacklist = DEFAULT_BLACKLIST.copy()
        else:
            self.blacklist = DEFAULT_BLACKLIST.copy()
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {'blacklist': self.blacklist}
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except (IOError, OSError) as e:
            print(f"Warning: Could not save config: {e}")
    
    def is_admin(self):
        """Check if running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except (AttributeError, OSError):
            return False
    
    def block_sites(self):
        """Add blocked sites to hosts file"""
        if not self.is_admin():
            return False, "Administrator privileges required!"
        
        if not self.blacklist:
            return False, "No sites in blacklist!"
        
        try:
            # Read current hosts file with proper encoding
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Remove any existing blocks from our app
            if MARKER_START in content and MARKER_END in content:
                start_idx = content.find(MARKER_START)
                end_idx = content.find(MARKER_END) + len(MARKER_END)
                if start_idx < end_idx:  # Valid markers found
                    content = content[:start_idx] + content[end_idx:]
            
            # Build block entries
            block_entries = [f"\n{MARKER_START}"]
            for site in self.blacklist:
                # Sanitize site name
                clean_site = site.strip().lower()
                if clean_site and self._is_valid_hostname(clean_site):
                    block_entries.append(f"{REDIRECT_IP} {clean_site}")
            block_entries.append(f"{MARKER_END}\n")
            
            # Write updated hosts file
            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n' + '\n'.join(block_entries))
            
            self.is_blocking = True
            # Flush DNS cache using subprocess (safer than os.system)
            self._flush_dns()
            return True, "Sites blocked successfully!"
        
        except PermissionError:
            return False, "Permission denied! Run as Administrator."
        except FileNotFoundError:
            return False, "Hosts file not found!"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _is_valid_hostname(self, hostname):
        """Validate hostname format"""
        if not hostname or len(hostname) > 253:
            return False
        # Remove trailing dot if present
        hostname = hostname.rstrip('.')
        # Check for valid characters and structure
        # Must have at least one dot, no consecutive dots
        if '..' in hostname or '.' not in hostname:
            return False
        # Simple validation - alphanumeric, dots, and hyphens
        # Each label must start/end with alphanumeric
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
            pass  # DNS flush is not critical
    
    def unblock_sites(self):
        """Remove blocked sites from hosts file"""
        if not self.is_admin():
            return False, "Administrator privileges required!"
        
        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Remove our block entries
            if MARKER_START in content and MARKER_END in content:
                start_idx = content.find(MARKER_START)
                end_idx = content.find(MARKER_END) + len(MARKER_END)
                if start_idx < end_idx:  # Valid markers found
                    content = content[:start_idx] + content[end_idx:]
            
            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.write(content.strip() + '\n')
            
            self.is_blocking = False
            self.end_time = None
            # Flush DNS cache
            self._flush_dns()
            return True, "Sites unblocked!"
        
        except PermissionError:
            return False, "Permission denied! Run as Administrator."
        except FileNotFoundError:
            return False, "Hosts file not found!"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def add_site(self, site):
        """Add a site to the blacklist"""
        # Clean up the site input
        site = site.lower().strip()
        
        # Remove common prefixes
        for prefix in ['https://', 'http://', 'www.']:
            if site.startswith(prefix):
                site = site[len(prefix):]
        
        # Remove trailing slashes and paths
        site = site.split('/')[0].strip()
        
        if not site or not self._is_valid_hostname(site):
            return False
        
        if site not in self.blacklist:
            self.blacklist.append(site)
            # Also add www version if not present
            if not site.startswith('www.'):
                www_site = f"www.{site}"
                if www_site not in self.blacklist and self._is_valid_hostname(www_site):
                    self.blacklist.append(www_site)
            self.save_config()
            return True
        return False
    
    def remove_site(self, site):
        """Remove a site from the blacklist"""
        if site in self.blacklist:
            self.blacklist.remove(site)
            self.save_config()
            return True
        return False


class FocusBlockerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Freedom - Focus Blocker")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # Set icon if available
        try:
            self.root.iconbitmap(default='')
        except:
            pass
        
        self.blocker = FocusBlocker()
        self.timer_running = False
        self.remaining_seconds = 0
        self._timer_lock = threading.Lock()
        
        self.setup_ui()
        self.update_site_list()
        self.check_admin_status()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔒 Personal Freedom", 
                                font=('Segoe UI', 18, 'bold'))
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Block distracting sites and focus!", 
                                   font=('Segoe UI', 10))
        subtitle_label.pack(pady=(0, 15))
        
        # Admin status
        self.admin_label = ttk.Label(main_frame, text="", font=('Segoe UI', 9))
        self.admin_label.pack(pady=(0, 10))
        
        # Timer Frame
        timer_frame = ttk.LabelFrame(main_frame, text="Focus Timer", padding="10")
        timer_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Timer display
        self.timer_display = ttk.Label(timer_frame, text="00:00:00", 
                                       font=('Segoe UI', 36, 'bold'))
        self.timer_display.pack(pady=10)
        
        # Time input
        time_input_frame = ttk.Frame(timer_frame)
        time_input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_input_frame, text="Hours:").pack(side=tk.LEFT, padx=5)
        self.hours_var = tk.StringVar(value="0")
        self.hours_spin = ttk.Spinbox(time_input_frame, from_=0, to=12, width=5, 
                                       textvariable=self.hours_var)
        self.hours_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_input_frame, text="Minutes:").pack(side=tk.LEFT, padx=5)
        self.minutes_var = tk.StringVar(value="25")
        self.minutes_spin = ttk.Spinbox(time_input_frame, from_=0, to=59, width=5,
                                         textvariable=self.minutes_var)
        self.minutes_spin.pack(side=tk.LEFT, padx=5)
        
        # Quick timer buttons
        quick_frame = ttk.Frame(timer_frame)
        quick_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(quick_frame, text="25 min", 
                   command=lambda: self.set_quick_time(25)).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(quick_frame, text="45 min", 
                   command=lambda: self.set_quick_time(45)).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(quick_frame, text="1 hour", 
                   command=lambda: self.set_quick_time(60)).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(quick_frame, text="2 hours", 
                   command=lambda: self.set_quick_time(120)).pack(side=tk.LEFT, padx=5, expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(timer_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="▶ Start Focus Session", 
                                    command=self.start_session)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.stop_btn = ttk.Button(control_frame, text="⬛ Stop Session", 
                                   command=self.stop_session, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Status
        self.status_label = ttk.Label(timer_frame, text="Status: Ready", 
                                      font=('Segoe UI', 10, 'bold'))
        self.status_label.pack(pady=5)
        
        # Blacklist Frame
        blacklist_frame = ttk.LabelFrame(main_frame, text="Blocked Sites", padding="10")
        blacklist_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Site list with scrollbar
        list_frame = ttk.Frame(blacklist_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.site_listbox = tk.Listbox(list_frame, height=8, 
                                        yscrollcommand=scrollbar.set,
                                        font=('Consolas', 10))
        self.site_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.site_listbox.yview)
        
        # Add/Remove site
        site_controls = ttk.Frame(blacklist_frame)
        site_controls.pack(fill=tk.X, pady=(10, 0))
        
        self.site_entry = ttk.Entry(site_controls, font=('Segoe UI', 10))
        self.site_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.site_entry.bind('<Return>', lambda e: self.add_site())
        
        ttk.Button(site_controls, text="+ Add", command=self.add_site).pack(side=tk.LEFT, padx=2)
        ttk.Button(site_controls, text="- Remove", command=self.remove_site).pack(side=tk.LEFT, padx=2)
        
        # Footer
        footer_label = ttk.Label(main_frame, text="⚠ Run as Administrator for blocking to work", 
                                 font=('Segoe UI', 8), foreground='gray')
        footer_label.pack(pady=(5, 0))
    
    def check_admin_status(self):
        """Check and display admin status"""
        if self.blocker.is_admin():
            self.admin_label.config(text="✅ Running as Administrator", foreground='green')
        else:
            self.admin_label.config(text="⚠ Not running as Administrator - blocking won't work!", 
                                   foreground='red')
    
    def set_quick_time(self, minutes):
        """Set quick timer values"""
        hours = minutes // 60
        mins = minutes % 60
        self.hours_var.set(str(hours))
        self.minutes_var.set(str(mins))
    
    def update_site_list(self):
        """Update the site listbox"""
        self.site_listbox.delete(0, tk.END)
        for site in sorted(self.blocker.blacklist):
            self.site_listbox.insert(tk.END, site)
    
    def add_site(self):
        """Add a site to the blacklist"""
        site = self.site_entry.get().strip()
        if site:
            if self.blocker.add_site(site):
                self.update_site_list()
                self.site_entry.delete(0, tk.END)
            else:
                messagebox.showinfo("Info", "Site already in list or invalid.")
    
    def remove_site(self):
        """Remove selected site from blacklist"""
        selection = self.site_listbox.curselection()
        if selection:
            site = self.site_listbox.get(selection[0])
            if self.blocker.remove_site(site):
                self.update_site_list()
    
    def start_session(self):
        """Start a focus session"""
        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for time.")
            return
        
        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            messagebox.showerror("Error", "Please set a time greater than 0.")
            return
        
        # Block sites
        success, message = self.blocker.block_sites()
        if not success:
            messagebox.showerror("Error", message)
            return
        
        # Start timer
        self.remaining_seconds = total_minutes * 60
        self.timer_running = True
        
        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.hours_spin.config(state=tk.DISABLED)
        self.minutes_spin.config(state=tk.DISABLED)
        self.status_label.config(text="🔒 Status: BLOCKING", foreground='red')
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
        self.timer_thread.start()
        
        messagebox.showinfo("Focus Session Started", 
                           f"Sites are now blocked for {hours}h {minutes}m.\nStay focused! 💪")
    
    def run_timer(self):
        """Run the countdown timer"""
        while True:
            with self._timer_lock:
                if self.remaining_seconds <= 0 or not self.timer_running:
                    break
                
                hours = self.remaining_seconds // 3600
                minutes = (self.remaining_seconds % 3600) // 60
                seconds = self.remaining_seconds % 60
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.remaining_seconds -= 1
            
            # Update UI from main thread
            try:
                self.root.after(0, lambda t=time_str: self.timer_display.config(text=t))
            except tk.TclError:
                break  # Window was closed
            
            time.sleep(1)
        
        with self._timer_lock:
            if self.remaining_seconds <= 0 and self.timer_running:
                try:
                    self.root.after(0, self.session_complete)
                except tk.TclError:
                    pass  # Window was closed
    
    def session_complete(self):
        """Handle session completion"""
        self.stop_session(show_message=False)
        self.timer_display.config(text="00:00:00")
        messagebox.showinfo("Session Complete", 
                           "🎉 Focus session complete!\nSites are now unblocked.\nGreat job staying focused!")
    
    def stop_session(self, show_message=True):
        """Stop the focus session"""
        with self._timer_lock:
            self.timer_running = False
            self.remaining_seconds = 0
        
        # Unblock sites
        success, message = self.blocker.unblock_sites()
        
        # Update UI
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.hours_spin.config(state=tk.NORMAL)
            self.minutes_spin.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Ready", foreground='black')
            self.timer_display.config(text="00:00:00")
        except tk.TclError:
            pass  # Window may be closing
        
        if show_message:
            if success:
                messagebox.showinfo("Session Stopped", "Focus session stopped. Sites unblocked.")
            else:
                messagebox.showerror("Error", message)
    
    def on_closing(self):
        """Handle window close"""
        if self.timer_running:
            if messagebox.askyesno("Confirm Exit", 
                                   "A focus session is running!\n\nDo you want to stop the session and exit?"):
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
