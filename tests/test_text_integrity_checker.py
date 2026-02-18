"""Tests for the text integrity checker utility."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "tools" / "check_text_integrity.py"


def _run_checker(root: Path, mode: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--root", str(root), "--mode", mode],
        check=False,
        capture_output=True,
        text=True,
    )


def test_checker_passes_for_clean_repo_subset(tmp_path: Path):
    (tmp_path / "sample.py").write_text('print("ok")\n', encoding="utf-8")
    result = _run_checker(tmp_path, "baseline")
    assert result.returncode == 0, result.stdout + result.stderr


def test_checker_fails_on_bom_in_strict_mode(tmp_path: Path):
    # UTF-8 BOM + ASCII body
    (tmp_path / "sample.py").write_bytes(b"\xef\xbb\xbfprint('ok')\n")
    result = _run_checker(tmp_path, "strict")
    assert result.returncode != 0
    assert "BOM not allowed" in result.stdout


def test_checker_fails_on_mojibake_in_baseline_mode(tmp_path: Path):
    (tmp_path / "sample.py").write_text('text = "\u0111\u017a\u017d\u017b Focus"\n', encoding="utf-8")
    result = _run_checker(tmp_path, "baseline")
    assert result.returncode != 0
    assert "New mojibake file detected" in result.stdout


def test_checker_fails_on_c1_control_mojibake_in_strict_mode(tmp_path: Path):
    (tmp_path / "sample.py").write_text('text = "\u00e2\u0098\u2022"\n', encoding="utf-8")
    result = _run_checker(tmp_path, "strict")
    assert result.returncode != 0
    assert "Mojibake signature" in result.stdout


def test_checker_fails_on_replacement_char_in_strict_mode(tmp_path: Path):
    (tmp_path / "sample.py").write_text('text = "\uFFFD"\n', encoding="utf-8")
    result = _run_checker(tmp_path, "strict")
    assert result.returncode != 0
    assert "Mojibake signature" in result.stdout


def test_checker_fails_on_escaped_byte_mojibake_in_strict_mode(tmp_path: Path):
    (tmp_path / "sample.py").write_text('text = "\\xe2\\xad\\x90"\n', encoding="utf-8")
    result = _run_checker(tmp_path, "strict")
    assert result.returncode != 0
    assert "Mojibake signature" in result.stdout
