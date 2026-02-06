"""Backward-compatible entrypoint shim.

Historically, packaging referenced ``focus_blocker:main``.
The canonical implementation now lives in ``focus_blocker_qt.py``.
"""

from focus_blocker_qt import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
