import argparse
import re
import os
import sys
from pathlib import Path

VERSION_FILE_PY = "__version__.py"
VERSION_FILE_TXT = "version_info.txt"
INSTALLER_FILE = "installer.iss"
PYPROJECT_FILE = "pyproject.toml"

def get_current_version():
    if not os.path.exists(VERSION_FILE_PY):
        raise FileNotFoundError(f"{VERSION_FILE_PY} not found.")
    
    with open(VERSION_FILE_PY, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
        
    raise ValueError(f"Could not find version string in {VERSION_FILE_PY}")

def bump_version_string(current_version, part):
    try:
        major, minor, patch = map(int, current_version.split('.'))
    except ValueError:
        print(f"Error: Version format '{current_version}' not supported. Expected 'major.minor.patch'.")
        sys.exit(1)

    if part == 'major':
        major += 1
        minor = 0
        patch = 0
    elif part == 'minor':
        minor += 1
        patch = 0
    elif part == 'patch':
        patch += 1
    else:
        # Assuming explicit version string
        if re.match(r'^\d+\.\d+\.\d+$', part):
            return part
        else:
             print(f"Error: Invalid version argument '{part}'. Use 'major', 'minor', 'patch', or 'X.Y.Z'.")
             sys.exit(1)

    return f"{major}.{minor}.{patch}"

def update_version_py(new_version):
    with open(VERSION_FILE_PY, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    with open(VERSION_FILE_PY, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {VERSION_FILE_PY}")

def update_version_info_txt(new_version):
    if not os.path.exists(VERSION_FILE_TXT):
        print(f"Warning: {VERSION_FILE_TXT} not found. Skipping.")
        return

    # Windows version requires 4 parts usually. We append .0
    win_version = f"{new_version}.0"
    # Or just replace the comma separated tuple for 'filevers' and 'prodvers' if they existed in standard pyinstaller format,
    # but based on reading it is formatted as:
    # StringStruct('FileVersion', '5.0.7.0'),
    # StringStruct(u'ProductVersion', u'5.0.0.0')])
    
    # We will only update the StringStruct string values for now.
    
    with open(VERSION_FILE_TXT, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update FileVersion string
    content = re.sub(
        r"StringStruct\((u?)'FileVersion',\s*(u?)'[\d\.]+'\)",
        f"StringStruct(\\1'FileVersion', \\2'{win_version}')",
        content
    )
    
    # Update ProductVersion string
    content = re.sub(
        r"StringStruct\((u?)'ProductVersion',\s*(u?)'[\d\.]+'\)",
        f"StringStruct(\\1'ProductVersion', \\2'{win_version}')",
        content
    )
    
    # Also update the tuple version if present (e.g., filevers=(5, 6, 8, 0))
    # It usually looks like filevers=(5, 0, 7, 0)
    # Let's try to find those tuples in standard pyinstaller version files
    major, minor, patch = map(int, new_version.split('.'))
    tuple_ver = f"({major}, {minor}, {patch}, 0)"
    
    content = re.sub(
        r"filevers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)",
        f"filevers={tuple_ver}",
        content
    )
    content = re.sub(
        r"prodvers=\(\d+,\s*\d+,\s*\d+,\s*\d+\)",
        f"prodvers={tuple_ver}",
        content
    )
    
    with open(VERSION_FILE_TXT, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {VERSION_FILE_TXT}")

def update_installer_iss(new_version):
    if not os.path.exists(INSTALLER_FILE):
        print(f"Warning: {INSTALLER_FILE} not found. Skipping.")
        return

    with open(INSTALLER_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # #define MyAppVersion "5.6.8"
    new_content = re.sub(
        r'#define MyAppVersion "[^"]+"',
        f'#define MyAppVersion "{new_version}"',
        content
    )

    with open(INSTALLER_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {INSTALLER_FILE}")

def update_pyproject_toml(new_version):
    if not os.path.exists(PYPROJECT_FILE):
        print(f"Warning: {PYPROJECT_FILE} not found. Skipping.")
        return

    with open(PYPROJECT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # version = "5.0.0"
    new_content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )

    with open(PYPROJECT_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {PYPROJECT_FILE}")

def main():
    parser = argparse.ArgumentParser(description="Manage project versioning.")
    parser.add_argument("action", help="Action to perform: 'show', 'bump', 'set'")
    parser.add_argument("value", nargs="?", help="For 'bump': major, minor, patch. For 'set': X.Y.Z")
    
    args = parser.parse_args()
    
    current_version = get_current_version()
    
    if args.action == 'show':
        print(f"Current version: {current_version}")
        return
    
    new_version = None
    if args.action == 'bump':
        if not args.value:
            print("Error: Please specify 'major', 'minor', or 'patch' for bump.")
            return
        new_version = bump_version_string(current_version, args.value)
        
    elif args.action == 'set':
        if not args.value:
            print("Error: Please specify version string (X.Y.Z) for set.")
            return
        if not re.match(r'^\d+\.\d+\.\d+$', args.value):
            print("Error: Invalid version format. Use X.Y.Z")
            return
        new_version = args.value
        
    else:
        print("Unknown action. Use 'show', 'bump', or 'set'.")
        return
        
    print(f"Updating version from {current_version} to {new_version}...")
    
    update_version_py(new_version)
    update_version_info_txt(new_version)
    update_installer_iss(new_version)
    update_pyproject_toml(new_version)
    
    print("\nVersion update complete!")
    print(f"New version: {new_version}")

if __name__ == "__main__":
    main()
