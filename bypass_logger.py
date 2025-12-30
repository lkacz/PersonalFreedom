"""
Bypass Attempt Logger for Personal Liberty
Runs a local HTTP server to log attempts to access blocked sites.

When sites are blocked via hosts file (redirected to 127.0.0.1),
any browser request to those sites will hit this server instead.
We log these attempts to help users understand their distraction patterns.
"""

import threading
import json
import logging
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket

logger = logging.getLogger(__name__)

# Path for storing bypass attempts
if getattr(__import__('sys'), 'frozen', False):
    APP_DIR = Path(__import__('sys').executable).parent
else:
    APP_DIR = Path(__file__).parent

BYPASS_LOG_PATH = APP_DIR / "bypass_attempts.json"


class BypassAttemptHandler(BaseHTTPRequestHandler):
    """HTTP handler that logs bypass attempts and shows a focus reminder."""
    
    # Class variable to store the logger instance
    bypass_logger = None
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests - log the attempt and show reminder page."""
        self._handle_request()
    
    def do_POST(self):
        """Handle POST requests."""
        self._handle_request()
    
    def do_HEAD(self):
        """Handle HEAD requests."""
        self._handle_request()
    
    def _handle_request(self):
        """Log the bypass attempt and return a focus reminder page."""
        # Extract the host from the request
        host = self.headers.get('Host', 'unknown')
        
        # Log the attempt
        if self.bypass_logger:
            self.bypass_logger.log_attempt(host, self.path)
        
        # Send focus reminder page
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = self._generate_reminder_page(host)
        self.wfile.write(html.encode('utf-8'))
    
    def _generate_reminder_page(self, blocked_site: str) -> str:
        """Generate an HTML page reminding user to stay focused."""
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>🔒 Stay Focused!</title>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-align: center;
            padding: 20px;
        }}
        .container {{
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        .icon {{ font-size: 80px; margin-bottom: 20px; }}
        h1 {{ font-size: 2.5em; margin-bottom: 15px; }}
        .blocked-site {{
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 10px;
            font-family: monospace;
            margin: 20px 0;
            word-break: break-all;
        }}
        p {{ font-size: 1.1em; line-height: 1.6; margin: 15px 0; opacity: 0.9; }}
        .tips {{
            text-align: left;
            background: rgba(0,0,0,0.2);
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        .tips h3 {{ margin-bottom: 10px; }}
        .tips li {{ margin: 8px 0; padding-left: 10px; }}
        .counter {{
            font-size: 0.9em;
            opacity: 0.7;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🔒</div>
        <h1>Stay Focused!</h1>
        <p>You tried to access a blocked site:</p>
        <div class="blocked-site">{blocked_site}</div>
        <p>This site is blocked during your focus session to help you stay productive.</p>
        
        <div class="tips">
            <h3>💡 Quick Tips:</h3>
            <ul>
                <li>Take a deep breath - the urge will pass</li>
                <li>Remember why you started this focus session</li>
                <li>Try a quick stretch or walk instead</li>
                <li>Write down what you wanted to check - review it later</li>
            </ul>
        </div>
        
        <p class="counter">This attempt has been logged for your productivity insights.</p>
    </div>
</body>
</html>'''


class BypassLogger:
    """Logs and tracks bypass attempts during focus sessions."""
    
    def __init__(self):
        self.attempts = self._load_attempts()
        self.server = None
        self.server_thread = None
        self.current_session_attempts = []
        self._running = False
    
    def _load_attempts(self) -> dict:
        """Load existing bypass attempts from file."""
        if BYPASS_LOG_PATH.exists():
            try:
                with open(BYPASS_LOG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "total_attempts": 0,
            "attempts_by_site": {},
            "attempts_by_hour": {str(i): 0 for i in range(24)},
            "daily_attempts": {},
            "session_history": []
        }
    
    def _save_attempts(self):
        """Save bypass attempts to file."""
        try:
            with open(BYPASS_LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.attempts, f, indent=2)
        except (IOError, OSError) as e:
            logger.warning(f"Could not save bypass attempts: {e}")
    
    def log_attempt(self, site: str, path: str = "/"):
        """Log a single bypass attempt."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        hour = str(now.hour)
        
        # Clean up site name
        site = site.split(':')[0].lower()  # Remove port if present
        
        attempt = {
            "timestamp": now.isoformat(),
            "site": site,
            "path": path
        }
        
        # Update statistics
        self.attempts["total_attempts"] += 1
        
        # By site
        if site not in self.attempts["attempts_by_site"]:
            self.attempts["attempts_by_site"][site] = 0
        self.attempts["attempts_by_site"][site] += 1
        
        # By hour
        self.attempts["attempts_by_hour"][hour] += 1
        
        # By day
        if today not in self.attempts["daily_attempts"]:
            self.attempts["daily_attempts"][today] = 0
        self.attempts["daily_attempts"][today] += 1
        
        # Current session
        self.current_session_attempts.append(attempt)
        
        # Save periodically (every 5 attempts)
        if self.attempts["total_attempts"] % 5 == 0:
            self._save_attempts()
        
        logger.info(f"Bypass attempt logged: {site}{path}")
    
    def start_server(self, port: int = 80) -> bool:
        """Start the HTTP server to catch bypass attempts."""
        if self._running:
            return True
        
        # Set the handler's logger reference
        BypassAttemptHandler.bypass_logger = self
        
        try:
            # Try to bind to port 80 first
            self.server = HTTPServer(('127.0.0.1', port), BypassAttemptHandler)
            self._running = True
            
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            logger.info(f"Bypass logger server started on port {port}")
            return True
            
        except socket.error as e:
            if port == 80:
                # Try alternative port
                logger.warning(f"Port 80 unavailable ({e}), trying port 8080")
                return self.start_server(port=8080)
            else:
                logger.error(f"Could not start bypass logger server: {e}")
                return False
    
    def _run_server(self):
        """Run the HTTP server."""
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Bypass logger server error: {e}")
        finally:
            self._running = False
    
    def stop_server(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self._running = False
            
            # Save session summary
            if self.current_session_attempts:
                session_summary = {
                    "date": datetime.now().isoformat(),
                    "attempt_count": len(self.current_session_attempts),
                    "sites": list(set(a["site"] for a in self.current_session_attempts))
                }
                self.attempts["session_history"].append(session_summary)
                
                # Keep only last 100 sessions
                if len(self.attempts["session_history"]) > 100:
                    self.attempts["session_history"] = self.attempts["session_history"][-100:]
            
            self.current_session_attempts = []
            self._save_attempts()
            
            logger.info("Bypass logger server stopped")
    
    def get_statistics(self) -> dict:
        """Get bypass attempt statistics for display."""
        # Top distraction sites
        sorted_sites = sorted(
            self.attempts["attempts_by_site"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Peak distraction hours
        sorted_hours = sorted(
            self.attempts["attempts_by_hour"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Recent trend (last 7 days)
        recent_days = []
        for i in range(7):
            date = (datetime.now() - __import__('datetime').timedelta(days=i)).strftime("%Y-%m-%d")
            count = self.attempts["daily_attempts"].get(date, 0)
            recent_days.append((date, count))
        
        return {
            "total_attempts": self.attempts["total_attempts"],
            "top_sites": sorted_sites,
            "peak_hours": sorted_hours,
            "recent_trend": list(reversed(recent_days)),
            "current_session": len(self.current_session_attempts),
            "session_sites": list(set(a["site"] for a in self.current_session_attempts))
        }
    
    def get_insights(self) -> list:
        """Generate insights about distraction patterns."""
        insights = []
        stats = self.get_statistics()
        
        if stats["total_attempts"] == 0:
            return ["No bypass attempts recorded yet. Great focus! 🎉"]
        
        # Top distraction site
        if stats["top_sites"]:
            top_site, count = stats["top_sites"][0]
            insights.append(f"🎯 Your #1 distraction: {top_site} ({count} attempts)")
        
        # Peak distraction time
        if stats["peak_hours"]:
            peak_hour, count = stats["peak_hours"][0]
            hour_int = int(peak_hour)
            time_str = f"{hour_int}:00-{hour_int+1}:00"
            if hour_int < 12:
                period = "morning"
            elif hour_int < 17:
                period = "afternoon"
            else:
                period = "evening"
            insights.append(f"⏰ Most distracted in the {period} ({time_str})")
        
        # Trend analysis
        recent = stats["recent_trend"]
        if len(recent) >= 7:
            first_half = sum(d[1] for d in recent[:3])
            second_half = sum(d[1] for d in recent[4:])
            if second_half < first_half * 0.7:
                insights.append("📉 Great progress! Distractions down this week!")
            elif second_half > first_half * 1.3:
                insights.append("📈 Distraction attempts increasing - stay vigilant!")
        
        return insights


# Singleton instance
_bypass_logger_instance = None

def get_bypass_logger() -> BypassLogger:
    """Get the singleton bypass logger instance."""
    global _bypass_logger_instance
    if _bypass_logger_instance is None:
        _bypass_logger_instance = BypassLogger()
    return _bypass_logger_instance
