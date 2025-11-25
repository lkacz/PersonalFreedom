# Personal Freedom - Focus Blocker 🔒

A Windows application to block distracting websites during focus sessions. Take control of your time and boost your productivity!

## Features

- ⏱️ **Timer-based blocking** - Set focus sessions from 25 minutes to several hours
- 🚫 **Website blacklist** - Block Facebook, YouTube, Reddit, Twitter, and more
- 📝 **Customizable list** - Add or remove sites from the blacklist
- 💾 **Persistent settings** - Your blacklist is saved between sessions
- 🖥️ **System tray mode** - Run minimized in the background
- 🔒 **Hosts file blocking** - Reliable blocking at the system level

## How It Works

The app modifies your Windows `hosts` file to redirect blocked websites to `127.0.0.1` (localhost), making them inaccessible in any browser. When your focus session ends, the blocks are automatically removed.

## Installation

### Prerequisites
- Windows 10/11
- Python 3.8 or higher

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **For the system tray version, install additional packages:**
   ```bash
   pip install pystray Pillow
   ```

## Usage

### GUI Version (Recommended)
Double-click `run_as_admin.bat` to start the full application with administrator privileges.

**Features:**
- Visual timer display
- Quick-start buttons (25 min, 45 min, 1 hour, 2 hours)
- Custom time input
- Site list management

### System Tray Version
Double-click `run_tray.bat` to start the minimized system tray version.

**Features:**
- Runs quietly in the background
- Right-click menu for quick actions
- Less intrusive for long focus sessions

## Default Blocked Sites

- facebook.com
- youtube.com
- twitter.com / x.com
- instagram.com
- tiktok.com
- reddit.com
- netflix.com
- twitch.tv

## Adding/Removing Sites

### In the GUI:
1. Type the website URL in the input field (e.g., `pinterest.com`)
2. Click "Add" or press Enter
3. The www version is automatically added

To remove: Select a site and click "Remove"

### Manually:
Edit `config.json` in the application folder:
```json
{
  "blacklist": [
    "facebook.com",
    "www.facebook.com",
    "yoursite.com",
    "www.yoursite.com"
  ]
}
```

## Important Notes

⚠️ **Administrator Privileges Required**
The app needs administrator rights to modify the Windows hosts file. Always run using the provided `.bat` files.

⚠️ **Don't Close During Session**
If you close the app during a focus session, sites will remain blocked. You can:
- Re-run the app and click "Stop Session"
- Manually edit `C:\Windows\System32\drivers\etc\hosts` and remove lines between the `PERSONAL FREEDOM` markers

⚠️ **Browser Caching**
Some browsers cache DNS. If a site is still accessible after blocking:
- Clear your browser cache
- The app automatically runs `ipconfig /flushdns` but a browser restart may help

## Troubleshooting

### Sites not being blocked?
1. Make sure you're running as Administrator (check the status in the app)
2. Clear browser cache and restart browser
3. Try running `ipconfig /flushdns` in an admin command prompt

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
5. Run `ipconfig /flushdns` in command prompt

## License

MIT License - Feel free to modify and share!

---

**Stay focused and take back your time! 💪**
