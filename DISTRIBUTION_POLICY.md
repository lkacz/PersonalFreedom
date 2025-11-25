# DISTRIBUTION GUIDE - DO NOT COMMIT BINARIES TO GIT

## ⚠️ CRITICAL: Large Files Policy

**NEVER commit the following to Git:**
- `*.exe` files (500MB-2GB with bundled AI)
- `dist/` folder (contains executables)
- `installer_output/` folder (contains 2-3GB installers)
- Any compressed archives of builds

## Why Not Commit Binaries?

1. **Repository bloat**: Each commit with large files adds permanently to repo size
2. **Slow clones**: Users downloading the repo will download ALL historical versions
3. **Git limitations**: GitHub has file size limits (100MB warning, 2GB hard limit)
4. **Wasted bandwidth**: Binary files change completely with each rebuild

## ✅ Correct Distribution Method

### Step 1: Build Locally
```bash
.\build_all.bat
```

This creates:
- `dist\PersonalFreedom_Package\` - Portable version
- `installer_output\PersonalFreedom_Setup_v2.1.exe` - Installer

### Step 2: Create GitHub Release

1. Go to: https://github.com/lkacz/PersonalFreedom/releases
2. Click "Draft a new release"
3. Create a new tag (e.g., `v2.1.0`)
4. Upload files:
   - `PersonalFreedom_Setup_v2.1.exe` (from `installer_output/`)
   - `PersonalFreedom_Package.zip` (zip the folder from `dist/`)
5. Write release notes describing features
6. Publish release

### Step 3: Users Download

Users download from:
- https://github.com/lkacz/PersonalFreedom/releases/latest

NOT from cloning the repository.

## 🛡️ Safeguards in Place

1. **`.gitignore`**: Blocks all `*.exe`, `dist/`, `installer_output/`
2. **`.gitattributes`**: Marks binary types (backup prevention)
3. **Pre-commit hook**: Rejects files > 100MB
4. **Explicit warnings**: This file and comments in `.gitignore`

## If You Accidentally Stage Large Files

```bash
# Check what's staged
git status

# Unstage a specific file
git reset HEAD path/to/large/file.exe

# Unstage entire directory
git reset HEAD dist/
git reset HEAD installer_output/

# Check commit size before pushing
git log --oneline -1 --stat
```

## Summary

- ✅ **DO**: Commit source code (`.py`, `.bat`, `.iss`, `.md`)
- ✅ **DO**: Use GitHub Releases for binaries
- ❌ **DON'T**: Ever `git add` an `.exe` file
- ❌ **DON'T**: Commit the `dist/` or `installer_output/` folders
- ❌ **DON'T**: Commit any file over 100MB

---

**Remember**: Git is for source code versioning, not binary distribution!
