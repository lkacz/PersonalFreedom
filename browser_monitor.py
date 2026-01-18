"""
Browser URL Monitor for Light Mode

Monitors active browser windows and detects when users visit blocked sites.
Shows toast notifications instead of blocking. No admin privileges required.
"""

import ctypes
import re
import threading
import time
from typing import Optional, Callable, List, Set
from datetime import datetime, timedelta


# Windows API for getting active window title
try:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    WINDOWS_API_AVAILABLE = True
except Exception:
    WINDOWS_API_AVAILABLE = False
    user32 = None
    kernel32 = None


def get_active_window_title() -> str:
    """Get the title of the currently active window."""
    if not WINDOWS_API_AVAILABLE:
        return ""
    
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ""
        
        # Get window title length
        length = user32.GetWindowTextLengthW(hwnd) + 1
        if length <= 1:
            return ""
        
        # Get window title
        buffer = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buffer, length)
        return buffer.value
    except Exception:
        return ""


def extract_domain_from_title(title: str) -> Optional[str]:
    """
    Extract domain from browser window title.
    
    Browsers typically show: "Page Title - Site Name - Browser Name"
    or have the URL visible in various formats.
    """
    if not title:
        return None
    
    title_lower = title.lower()
    
    # Common browser suffixes to strip
    browser_suffixes = [
        ' - google chrome',
        ' - chrome',
        ' - mozilla firefox',
        ' - firefox',
        ' - microsoft edge',
        ' - edge',
        ' - opera',
        ' - brave',
        ' - vivaldi',
        ' — mozilla firefox',
        ' — google chrome',
    ]
    
    clean_title = title_lower
    for suffix in browser_suffixes:
        if clean_title.endswith(suffix):
            clean_title = clean_title[:-len(suffix)]
            break
    
    # Try to find domain patterns in the title
    # Pattern 1: "Something - domain.com" or "Something | domain.com"
    parts = re.split(r'\s[-|–—]\s', clean_title)
    
    for part in reversed(parts):  # Check from right to left
        part = part.strip()
        # Check if this looks like a domain
        if _looks_like_domain(part):
            return _clean_domain(part)
    
    # Pattern 2: Direct URL in title (some browsers show this)
    url_match = re.search(r'https?://([a-z0-9.-]+)', title_lower)
    if url_match:
        return _clean_domain(url_match.group(1))
    
    # Pattern 3: Check if any part of the title contains a known domain pattern
    domain_match = re.search(r'([a-z0-9-]+\.[a-z]{2,})', clean_title)
    if domain_match:
        return _clean_domain(domain_match.group(1))
    
    return None


def _looks_like_domain(text: str) -> bool:
    """Check if text looks like a domain name."""
    # Must have at least one dot
    if '.' not in text:
        return False
    
    # Basic domain pattern
    pattern = r'^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$'
    return bool(re.match(pattern, text.strip()))


def _clean_domain(domain: str) -> str:
    """Clean and normalize a domain name."""
    domain = domain.lower().strip()
    
    # Remove common prefixes
    for prefix in ['www.', 'http://', 'https://']:
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    
    # Remove path/query
    domain = domain.split('/')[0]
    domain = domain.split('?')[0]
    domain = domain.split('#')[0]
    
    return domain


class BrowserMonitor:
    """
    Monitors browser windows for blocked site access in Light Mode.
    
    Usage:
        monitor = BrowserMonitor(blocked_sites, on_violation_callback)
        monitor.start()
        # ... later ...
        monitor.stop()
    """
    
    def __init__(
        self,
        blocked_sites: List[str],
        on_violation: Callable[[str], None],
        check_interval: float = 2.0,
        cooldown_seconds: int = 30,
    ):
        """
        Initialize the browser monitor.
        
        Args:
            blocked_sites: List of domains to watch for
            on_violation: Callback when user visits a blocked site (receives domain)
            check_interval: How often to check (seconds)
            cooldown_seconds: Don't re-notify for same site within this period
        """
        self._lock = threading.Lock()  # Must be first - used by update_blocked_sites
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_notifications: dict = {}  # domain -> last notification time
        
        self.blocked_sites: Set[str] = set()
        self.update_blocked_sites(blocked_sites)
        self.on_violation = on_violation
        self.check_interval = check_interval
        self.cooldown_seconds = cooldown_seconds
    
    def update_blocked_sites(self, sites: List[str]) -> None:
        """Update the list of blocked sites."""
        cleaned = set()
        for site in sites:
            if site:
                cleaned.add(_clean_domain(site))
        with self._lock:
            self.blocked_sites = cleaned
    
    def start(self) -> None:
        """Start monitoring browser windows."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        self._last_notifications.clear()
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                self._check_active_window()
            except Exception:
                pass  # Silently ignore errors to keep monitoring
            
            time.sleep(self.check_interval)
    
    def _check_active_window(self) -> None:
        """Check if the active window is visiting a blocked site."""
        title = get_active_window_title()
        if not title:
            return
        
        # Check if it looks like a browser window
        if not self._is_browser_window(title):
            return
        
        # Try to extract domain
        domain = extract_domain_from_title(title)
        if not domain:
            return
        
        # Check if this domain (or parent domain) is blocked
        with self._lock:
            blocked_sites = self.blocked_sites.copy()
        
        matched_site = self._matches_blocked(domain, blocked_sites)
        if not matched_site:
            return
        
        # Check cooldown
        now = datetime.now()
        last_notify = self._last_notifications.get(matched_site)
        if last_notify and (now - last_notify) < timedelta(seconds=self.cooldown_seconds):
            return
        
        # Trigger notification
        self._last_notifications[matched_site] = now
        if self.on_violation:
            try:
                self.on_violation(matched_site)
            except Exception:
                pass
    
    def _is_browser_window(self, title: str) -> bool:
        """Check if window title looks like a browser."""
        title_lower = title.lower()
        browsers = [
            'chrome', 'firefox', 'edge', 'opera', 'brave', 
            'vivaldi', 'safari', 'chromium'
        ]
        return any(browser in title_lower for browser in browsers)
    
    def _matches_blocked(self, domain: str, blocked_sites: Set[str]) -> Optional[str]:
        """
        Check if domain matches any blocked site.
        
        Returns the matched blocked site, or None.
        """
        # Direct match
        if domain in blocked_sites:
            return domain
        
        # Check if domain ends with a blocked site (subdomain)
        for blocked in blocked_sites:
            if domain.endswith('.' + blocked):
                return blocked
            # Also check reverse (in case blocked is subdomain)
            if blocked.endswith('.' + domain):
                return blocked
        
        return None


# Singleton instance for app-wide use
_monitor_instance: Optional[BrowserMonitor] = None


def get_browser_monitor() -> Optional[BrowserMonitor]:
    """Get the global browser monitor instance."""
    return _monitor_instance


def create_browser_monitor(
    blocked_sites: List[str],
    on_violation: Callable[[str], None],
) -> BrowserMonitor:
    """Create and register the global browser monitor."""
    global _monitor_instance
    
    if _monitor_instance:
        _monitor_instance.stop()
    
    _monitor_instance = BrowserMonitor(blocked_sites, on_violation)
    return _monitor_instance
