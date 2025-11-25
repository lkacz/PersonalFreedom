# Personal Freedom - Quick Start Guide

## First Time Setup (2 minutes)

1. **Run as Admin**: Double-click `run_as_admin.bat`
2. **Check Admin Status**: Look for green ✅ Admin in top right
3. **Choose Categories**: Go to **📁 Categories** tab
   - Toggle categories you want to block
   - Default: All enabled (Social Media, Streaming, Gaming, News, Shopping)

## Basic Usage

### Quick Focus Session
1. **⏱ Timer** tab
2. Click a quick button: `25m`, `45m`, `1h`, `2h`
3. Click **▶ Start Focus**
4. Sites are blocked until timer ends

### Add Custom Site
1. **🌐 Sites** tab
2. Type site name (e.g., `pinterest.com`)
3. Click **+ Add**
4. Done! It will be blocked in next session

## Power Features

### Strict Mode (Can't Stop Early)
1. **⚙ Settings** → Set Password
2. **⏱ Timer** → Select "Strict 🔐"
3. Now you can't stop without password!

### Auto-Block During Work Hours
1. **📅 Schedule** tab
2. Select days (Mon-Fri)
3. Set time (9:00 AM - 5:00 PM)
4. Click **+ Add Schedule**
5. App will auto-block during these times

### Pomodoro (25 min work / 5 min break)
1. **⏱ Timer** → Select "Pomodoro 🍅"
2. **▶ Start Focus**
3. Automatic breaks every 25 minutes

### Never Block a Site
1. **🌐 Sites** → Whitelist section
2. Add important sites (e.g., `github.com`)
3. These will NEVER be blocked

## Track Your Progress

**📊 Stats** tab shows:
- Total focus time (hours)
- Sessions completed
- Current streak (consecutive days)
- Weekly chart

**Build the habit:** Focus every day to increase your streak! 🔥

## Common Tasks

### Block YouTube but not Netflix
1. **📁 Categories** → Uncheck "Video Streaming"
2. **🌐 Sites** → Add `youtube.com`, `www.youtube.com`

### Work Mode (Social + News only)
1. **📁 Categories** → Enable Social Media, News & Forums
2. **📁 Categories** → Disable others

### Import Friend's Blacklist
1. Get their exported JSON file
2. **🌐 Sites** → Click **📥 Import**
3. Select file

## Modes Explained

| Mode | Can Stop? | Best For |
|------|-----------|----------|
| 🟢 Normal | Anytime | Flexible work |
| 🔐 Strict | Need password | Serious focus |
| 🍅 Pomodoro | At breaks | Building habit |
| 📅 Scheduled | Manually | Auto work hours |

## Pro Tips

1. **Morning Routine**: Set schedule for 9 AM - 12 PM weekdays
2. **Password Protect**: Use strict mode for important deadlines
3. **Build Streaks**: Focus daily for motivation
4. **Whitelist Wisely**: Only add truly needed sites
5. **Review Stats**: Check weekly progress to stay motivated

## Need Help?

- **Can't stop strict mode?** Enter your password
- **Sites still accessible?** Clear browser cache, restart browser
- **Forgot password?** Edit `config.json`, remove `password_hash`
- **App crashed?** Manually edit hosts file (see README)

## Running Without Admin?

⚠️ **Won't work!** The app needs admin rights to edit the hosts file.
Always use `run_as_admin.bat`

---

**Happy focusing! 🎯**
