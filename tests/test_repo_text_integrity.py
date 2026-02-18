"""Repository-level text integrity contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_repository_text_integrity_strict():
    root = Path(__file__).resolve().parents[1]
    checker = root / "tools" / "check_text_integrity.py"
    result = subprocess.run(
        [sys.executable, str(checker), "--mode", "strict"],
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
