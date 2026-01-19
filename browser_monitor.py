"""
Browser URL Monitor for Light Mode

Monitors active browser windows and detects when users visit blocked sites.
Shows toast notifications instead of blocking. No admin privileges required.

Detection Methods:
1. UI Automation - Reads the actual URL from browser address bar (most reliable)
2. Title-to-domain mapping - Maps known site names to domains (e.g., "YouTube" → youtube.com)
3. Domain extraction from title - Tries to find domains in window titles
"""

import ctypes
import ctypes.wintypes
import re
import threading
import time
from typing import Optional, Callable, List, Set, Tuple
from datetime import datetime, timedelta


# Windows API for getting active window title and process info
try:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    oleacc = ctypes.windll.oleacc
    WINDOWS_API_AVAILABLE = True
except Exception:
    WINDOWS_API_AVAILABLE = False
    user32 = None
    kernel32 = None
    oleacc = None


# Known site name to domain mappings
# These map page title patterns to their domains
KNOWN_SITE_MAPPINGS = {
    # Social Media
    'youtube': 'youtube.com',
    'reddit': 'reddit.com',
    'twitter': 'twitter.com',
    'x.com': 'x.com',
    'facebook': 'facebook.com',
    'instagram': 'instagram.com',
    'tiktok': 'tiktok.com',
    'linkedin': 'linkedin.com',
    'pinterest': 'pinterest.com',
    'snapchat': 'snapchat.com',
    'tumblr': 'tumblr.com',
    'discord': 'discord.com',
    'twitch': 'twitch.tv',
    'threads': 'threads.net',
    'bluesky': 'bsky.app',
    'mastodon': 'mastodon.social',
    
    # Entertainment / Streaming
    'netflix': 'netflix.com',
    'hulu': 'hulu.com',
    'amazon prime': 'primevideo.com',
    'prime video': 'primevideo.com',
    'disney+': 'disneyplus.com',
    'disney plus': 'disneyplus.com',
    'hbo max': 'max.com',
    'paramount+': 'paramountplus.com',
    'crunchyroll': 'crunchyroll.com',
    'spotify': 'spotify.com',
    'soundcloud': 'soundcloud.com',
    'vimeo': 'vimeo.com',
    'dailymotion': 'dailymotion.com',
    
    # Gaming
    'steam': 'steampowered.com',
    'epic games': 'epicgames.com',
    'itch.io': 'itch.io',
    'roblox': 'roblox.com',
    'miniclip': 'miniclip.com',
    'kongregate': 'kongregate.com',
    'armor games': 'armorgames.com',
    'poki': 'poki.com',
    'crazygames': 'crazygames.com',
    
    # News / Media
    'cnn': 'cnn.com',
    'bbc': 'bbc.com',
    'nytimes': 'nytimes.com',
    'new york times': 'nytimes.com',
    'washington post': 'washingtonpost.com',
    'the guardian': 'theguardian.com',
    'huffpost': 'huffpost.com',
    'buzzfeed': 'buzzfeed.com',
    'vice': 'vice.com',
    
    # Shopping
    'amazon': 'amazon.com',
    'ebay': 'ebay.com',
    'etsy': 'etsy.com',
    'alibaba': 'alibaba.com',
    'aliexpress': 'aliexpress.com',
    'wish': 'wish.com',
    'shopify': 'shopify.com',
    'walmart': 'walmart.com',
    'target': 'target.com',
    
    # Messaging
    'whatsapp': 'web.whatsapp.com',
    'telegram': 'web.telegram.org',
    'messenger': 'messenger.com',
    'slack': 'slack.com',
    'signal': 'signal.org',
    
    # Dating
    'tinder': 'tinder.com',
    'bumble': 'bumble.com',
    'hinge': 'hinge.co',
    'okcupid': 'okcupid.com',
    'match.com': 'match.com',
    
    # Other distractions
    'imgur': 'imgur.com',
    'giphy': 'giphy.com',
    '9gag': '9gag.com',
    'quora': 'quora.com',
    'medium': 'medium.com',
}


def get_active_window_info() -> Tuple[int, str]:
    """
    Get the window handle and title of the currently active window.
    
    Returns:
        Tuple of (hwnd, title)
    """
    if not WINDOWS_API_AVAILABLE:
        return 0, ""
    
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return 0, ""
        
        # Get window title length
        length = user32.GetWindowTextLengthW(hwnd) + 1
        if length <= 1:
            return hwnd, ""
        
        # Get window title
        buffer = ctypes.create_unicode_buffer(length)
        user32.GetWindowTextW(hwnd, buffer, length)
        return hwnd, buffer.value
    except Exception:
        return 0, ""


def get_active_window_title() -> str:
    """Get the title of the currently active window."""
    _, title = get_active_window_info()
    return title


def get_browser_url_from_address_bar(hwnd: int, browser_name: str) -> Optional[str]:
    """
    Try to get the URL from browser address bar using UI Automation.
    
    This is the most reliable method but requires optional dependencies.
    Falls back gracefully if not available.
    
    Args:
        hwnd: Window handle of the browser
        browser_name: Name of the browser (chrome, edge, firefox, etc.)
        
    Returns:
        URL string if found, None otherwise
    """
    if not WINDOWS_API_AVAILABLE or not hwnd:
        return None
    
    # Method 1: Try uiautomation package (most reliable, lightweight)
    try:
        import uiautomation as auto
        
        # Get control from hwnd
        control = auto.ControlFromHandle(hwnd)
        if not control:
            return None
        
        # For Chrome/Edge, the address bar is an Edit control with name containing "Address"
        # or with AutomationId like "addressEditBox"
        if browser_name in ('chrome', 'edge', 'chromium', 'brave'):
            # Try to find the address bar edit control
            edit = control.EditControl(searchDepth=10, AutomationId='addressEditBox')
            if not edit.Exists(0, 0):
                # Try by name
                edit = control.EditControl(searchDepth=10, Name='Address and search bar')
            if edit.Exists(0, 0):
                value = edit.GetValuePattern().Value
                if value and ('.' in value or '://' in value):
                    return value
        
        elif browser_name == 'firefox':
            # Firefox uses a different structure
            edit = control.EditControl(searchDepth=10, AutomationId='urlbar-input')
            if edit.Exists(0, 0):
                value = edit.GetValuePattern().Value
                if value and ('.' in value or '://' in value):
                    return value
        
        return None
        
    except ImportError:
        pass
    except Exception:
        pass
    
    # Method 2: Try comtypes (heavier dependency)
    try:
        import comtypes.client
        
        # Initialize UI Automation
        uia = comtypes.client.CreateObject(
            "{ff48dba4-60ef-4201-aa87-54103eef594e}",  # CUIAutomation CLSID
            interface=comtypes.gen.UIAutomationClient.IUIAutomation
        )
        
        # Get the element from window handle
        element = uia.ElementFromHandle(hwnd)
        if not element:
            return None
        
        # Create condition to find edit controls (address bar)
        edit_condition = uia.CreatePropertyCondition(30003, 50004)  # UIA_ControlTypePropertyId
        edit_elements = element.FindAll(4, edit_condition)  # TreeScope_Descendants
        
        if edit_elements:
            for i in range(edit_elements.Length):
                edit = edit_elements.GetElement(i)
                try:
                    value_pattern = edit.GetCurrentPattern(10002)  # UIA_ValuePatternId
                    if value_pattern:
                        value = value_pattern.CurrentValue
                        if value and ('://' in value or '.' in value):
                            return value
                except Exception:
                    continue
        
        return None
        
    except ImportError:
        pass
    except Exception:
        pass
    
    return None


def match_title_to_known_site(title: str) -> Optional[str]:
    """
    Check if the window title matches any known site names.
    
    Many sites use their name in the title, like "YouTube", "Reddit - ...", etc.
    
    Args:
        title: Browser window title
        
    Returns:
        Domain if matched, None otherwise
    """
    if not title:
        return None
    
    title_lower = title.lower()
    
    # Check each known site mapping
    for site_name, domain in KNOWN_SITE_MAPPINGS.items():
        # Check if site name appears in title
        # Use word boundary-like matching to avoid false positives
        if site_name in title_lower:
            # Verify it's likely a match (not part of another word)
            # For short names, be more strict
            if len(site_name) <= 4:
                # For short names like "x.com", need exact word match
                pattern = r'\b' + re.escape(site_name) + r'\b'
                if re.search(pattern, title_lower):
                    return domain
            else:
                # Longer names are less likely to be false positives
                return domain
    
    return None


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
        """
        Check if the active window is visiting a blocked site.
        
        Uses multiple detection methods:
        1. UI Automation to read actual URL from address bar (most reliable)
        2. Known site name matching (e.g., "YouTube" → youtube.com)
        3. Domain extraction from window title (fallback)
        """
        hwnd, title = get_active_window_info()
        if not title:
            return
        
        # Check if it looks like a browser window
        browser_name = self._get_browser_name(title)
        if not browser_name:
            return
        
        domain = None
        
        # Method 1: Try UI Automation to get actual URL (most reliable)
        url = get_browser_url_from_address_bar(hwnd, browser_name)
        if url:
            domain = _clean_domain(url)
        
        # Method 2: Try matching known site names from title
        if not domain:
            domain = match_title_to_known_site(title)
        
        # Method 3: Try extracting domain from title patterns
        if not domain:
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
    
    def _get_browser_name(self, title: str) -> Optional[str]:
        """
        Get browser name from window title if it's a browser window.
        
        Returns:
            Browser name (lowercase) if detected, None otherwise
        """
        title_lower = title.lower()
        
        # Check for each browser
        browsers = ['chrome', 'firefox', 'edge', 'opera', 'brave', 'vivaldi', 'chromium']
        for browser in browsers:
            if browser in title_lower:
                return browser
        
        return None
    
    def _is_browser_window(self, title: str) -> bool:
        """Check if window title looks like a browser."""
        return self._get_browser_name(title) is not None
    
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
