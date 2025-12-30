"""
Personal Liberty Launcher
Automatically requests administrator privileges if needed.
"""

import ctypes
import sys
import os
from pathlib import Path


def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, OSError):
        return False


def run_as_admin():
    """Restart the script with administrator privileges"""
    script = sys.argv[0]
    params = ' '.join(f'"{arg}"' for arg in sys.argv[1:])

    # Use ShellExecuteW to request elevation
    ctypes.windll.shell32.ShellExecuteW(
        None,           # hwnd
        "runas",        # operation (request admin)
        sys.executable, # executable
        f'"{script}" {params}',  # parameters
        None,           # directory
        1               # show command (SW_SHOWNORMAL)
    )


def main():
    if not is_admin():
        print("Requesting administrator privileges...")
        run_as_admin()
        sys.exit(0)

    # We have admin rights - launch the main app
    script_dir = Path(__file__).parent
    main_script = script_dir / "focus_blocker_qt.py"

    if main_script.exists():
        # Import and run the main app
        import importlib.util
        spec = importlib.util.spec_from_file_location("focus_blocker_qt", main_script)
        if spec is None or spec.loader is None:
            print(f"Error: Could not load {main_script}")
            input("Press Enter to exit...")
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()
    else:
        print(f"Error: {main_script} not found!")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
