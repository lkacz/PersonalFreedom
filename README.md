# Personal Freedom - Focus Blocker 🔒

A powerful Windows application to block distracting websites during focus sessions. Take control of your time and boost your productivity with industry-standard features!

## ✨ Features

### Core Blocking
- ⏱️ **Timer-based blocking** - Set focus sessions from 25 minutes to several hours
- 🔒 **Hosts file blocking** - Reliable system-level blocking that works across all browsers
- 📁 **Category management** - Enable/disable entire categories (Social Media, Streaming, Gaming, etc.)
- 🌐 **Custom blacklist** - Add your own distracting sites
- ✅ **Whitelist** - Mark important sites that should never be blocked
- 💾 **Persistent settings** - All configurations saved automatically

### Advanced Modes
- 🟢 **Normal Mode** - Can stop session anytime
- 🔐 **Strict Mode** - Requires password to stop early (perfect for serious focus)
- 🍅 **Pomodoro Mode** - 25 min work / 5 min break cycles
- 📅 **Scheduled Blocking** - Auto-block during specific times (e.g., work hours)

### Productivity Tracking
- 📊 **Statistics** - Track total focus time, sessions completed, and streaks
- 🔥 **Streak tracking** - Build focus habits with daily streak counts
- 📈 **Weekly charts** - Visualize your focus time over the week
- 📅 **Daily breakdown** - See your progress each day

### Other Features
- 🖥️ **System tray mode** - Run minimized in the background
- 📥 **Import/Export** - Share blacklists or backup your configuration
- 🎨 **Tabbed interface** - Clean, organized UI with 6 dedicated tabs
- 🔔 **Break reminders** - Stay healthy during long sessions

## How It Works

The app modifies your Windows `hosts` file to redirect blocked websites to `127.0.0.1` (localhost), making them inaccessible in any browser. When your focus session ends, the blocks are automatically removed.

**NEW:** Enhanced with categories, schedules, statistics, and multiple blocking modes for maximum productivity!

## Installation

### Prerequisites
- Windows 10/11
- Python 3.8 or higher

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **For the system tray version (optional):**
   ```bash
   pip install pystray Pillow
   ```

3. **Or use pre-built executables** - Run `build.bat` to create standalone .exe files

## Usage

### Option 1: GUI Application (Recommended)
**Run:** Double-click `run_as_admin.bat` to start with administrator privileges.

**Tabs:**
- **⏱ Timer** - Start focus sessions with custom durations and modes
- **🌐 Sites** - Manage custom blacklist and whitelist
- **📁 Categories** - Toggle entire website categories on/off
- **📅 Schedule** - Set up automatic blocking schedules
- **📊 Stats** - View your focus time, streaks, and progress
- **⚙ Settings** - Configure passwords and Pomodoro timings

### Option 2: System Tray
**Run:** Double-click `run_tray.bat` for background operation.

Right-click the tray icon for quick actions:
- Quick start timers (25m, 45m, 1h, 2h, 4h)
- Stop current session
- Open full app

### Option 3: Autostart
**Run:** `setup_autostart.bat` and choose:
- **Task Scheduler** (Recommended) - Auto-runs with admin rights on login
- **Startup Folder** - Simple shortcut method

## Adding & Managing Sites

### Quick Add
1. Go to **🌐 Sites** tab
2. Type a website (e.g., `twitter.com` or `https://facebook.com/profile`)
3. Click **+ Add**
4. The app automatically adds www. version too

### Categories
Go to **📁 Categories** tab and toggle entire groups:
- **Social Media** - Facebook, Twitter, Instagram, TikTok, etc.
- **Video Streaming** - YouTube, Netflix, Hulu, Twitch, etc.
- **Gaming** - Steam, Epic Games, Roblox, etc.
- **News & Forums** - Reddit, 9gag, HackerNews, etc.
- **Shopping** - Amazon, eBay, AliExpress, etc.

### Whitelist (Never Block)
Add important sites to the whitelist so they're accessible even during focus sessions:
1. Go to **🌐 Sites** tab → Whitelist section
2. Add site and click **+ Add**

### Import/Export
- **Export** - Save your configuration to share or backup
- **Import** - Load a blacklist from a JSON file

## Blocking Modes

### 🟢 Normal Mode
- Default mode
- Can stop session anytime
- Good for flexible work sessions

### 🔐 Strict Mode
- **Requires password** to stop early
- Perfect for serious focus time
- Set password in **⚙ Settings** tab first

### 🍅 Pomodoro Mode
- Work/break cycles (default: 25 min / 5 min)
- Automatic break reminders
- Customize timings in **⚙ Settings**

### 📅 Scheduled Mode
- Auto-blocks during specific times
- Example: Weekdays 9 AM - 5 PM
- Configure in **📅 Schedule** tab

## Statistics & Tracking

View your productivity in the **📊 Stats** tab:

- **Total Focus Time** - All-time accumulated focus hours
- **Sessions Completed** - Number of successful sessions
- **Current Streak** - Consecutive days with focus sessions
- **Best Streak** - Your longest streak record
- **Weekly Chart** - Visual breakdown of this week's focus time

Build the habit by maintaining your daily streak! 🔥

## Troubleshooting

### Sites not being blocked?
1. ✅ Make sure you're running as Administrator (check status in app header)
2. 🧹 Clear browser cache and restart browser
3. 💻 Run `ipconfig /flushdns` in admin command prompt
4. 🔍 Check if site is in blacklist or whitelist

### Can't unblock sites after crash?
1. Open Notepad as Administrator
2. Open `C:\Windows\System32\drivers\etc\hosts`
3. Delete everything between:
   ```
   # === PERSONAL FREEDOM BLOCK START ===
   ...
   # === PERSONAL FREEDOM BLOCK END ===
   ```
4. Save the file
5. Run `ipconfig /flushdns`

### Strict mode won't let me stop?
- This is by design! Enter your password to stop
- Forgot password? Edit `config.json` and remove the `password_hash` field
- Or manually edit the hosts file (see above)

### Statistics not showing?
- Stats are saved in `stats.json`
- If corrupted, delete the file to reset
- Sessions must be > 1 minute to be counted

### Schedule not working?
- Check that schedule is enabled (green ✅)
- Verify day and time settings
- App checks every 60 seconds

## Configuration Files

| File | Purpose |
|------|---------|
| `config.json` | Blacklist, whitelist, categories, password, settings |
| `stats.json` | All statistics and progress tracking |
| `*.spec` | PyInstaller build specifications (auto-generated) |

### Manual Configuration

Edit `config.json` to:
- Bulk add sites to blacklist/whitelist
- Change Pomodoro timings
- Add schedules programmatically
- Reset password (remove `password_hash`)

**Example config.json:**
```json
{
  "blacklist": ["customsite.com", "www.customsite.com"],
  "whitelist": ["github.com", "stackoverflow.com"],
  "categories_enabled": {
    "Social Media": true,
    "Video Streaming": false,
    "Gaming": true,
    "News & Forums": true,
    "Shopping": false
  },
  "password_hash": null,
  "pomodoro_work": 25,
  "pomodoro_break": 5,
  "pomodoro_long_break": 15,
  "schedules": [
    {
      "id": "abc123",
      "days": [0, 1, 2, 3, 4],
      "start_time": "09:00",
      "end_time": "17:00",
      "enabled": true
    }
  ]
}
```

## Tips for Maximum Productivity

1. 🎯 **Start with Pomodoro Mode** - Great for building the focus habit
2. 🔐 **Use Strict Mode for important work** - No escape route keeps you accountable
3. 📅 **Set up schedules** - Automatic blocking during work hours
4. 🔥 **Build streaks** - Aim for daily focus sessions to maintain motivation
5. ✅ **Use whitelist wisely** - Only add truly essential sites
6. 📊 **Review stats weekly** - Track progress and adjust as needed
7. 🎨 **Customize categories** - Disable shopping blocks on weekends, etc.

## Keyboard Shortcuts

- `Enter` in site input fields = Add site
- `Tab` to navigate between tabs
- Close app = `Alt+F4` (will prompt if session running)

## Building from Source

```bash
# Install PyInstaller
pip install pyinstaller

# Run build script
build.bat

# Executables will be in dist/ folder
```

## What's New in v2.0

### Major Features
- ✨ **Tabbed interface** with 6 dedicated sections
- 📁 **Category system** with 80+ pre-defined distracting sites
- 🔐 **Strict Mode** with password protection
- 🍅 **Pomodoro Mode** with configurable timings
- 📅 **Scheduling system** for automatic blocking
- 📊 **Comprehensive statistics** and streak tracking
- ✅ **Whitelist** for never-block sites
- 📥 **Import/Export** configurations

### Improvements
- 🎨 Better UI with modern styling
- 🔒 Thread-safe timer operations
- ✅ Improved hostname validation
- 🌐 Better URL parsing (handles https://, paths, etc.)
- 💾 Separate stats file for tracking
- 🔧 More robust error handling

## Important Notes

⚠️ **Administrator Privileges Required**
The app needs admin rights to modify the Windows hosts file. Always run using the provided `.bat` files.

⚠️ **Backup Your Work**
Don't close the app during a session without stopping it first, or sites will remain blocked.

⚠️ **Browser Caching**
Some browsers cache DNS. If a site is still accessible:
- Clear browser cache
- Restart browser
- The app auto-runs `ipconfig /flushdns` but browsers may need restart

⚠️ **VPN/Proxy Warning**
If using VPN or proxy, some sites might bypass hosts file blocking. Consider blocking at router level for complete control.

## License

MIT License - Feel free to modify and share!

## Contributing

Found a bug? Want a feature? 
- Open an issue on GitHub
- Submit a pull request
- Star the repo if you find it useful!

---

**Stay focused and take back your time! 💪**

Made with ❤️ for productivity enthusiasts
