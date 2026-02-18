#!/usr/bin/env python3
"""Validate repository text integrity for emoji/encoding regressions.

Modes:
- baseline: allow known pre-existing issues, fail on any new/worse issues
- strict: fail on any BOM/mojibake signature
- report: report findings only (never fails)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from typing import Iterable


UTF8_BOM = b"\xef\xbb\xbf"

# Baseline debt map. Keep empty after remediation so baseline mode behaves like
# "no known debt" while still supporting future phased rollouts if needed.
BASELINE_MOJIBAKE_MAX: dict[str, int] = {}
BASELINE_BOM_ALLOWED: set[str] = set()

# Common mojibake signatures observed in this codebase.
MOJIBAKE_PATTERNS = [
    re.compile(r"\u0111\u017a"),  # text-integrity: ignore
    re.compile(
        r"\u00e2[\u0161\u015b\u0179\u20ac\u2122\u02dc\u017e\u2030\u2020"
        r"\u201e\u2039\u203a\u2013\u2014]"
    ),  # text-integrity: ignore
    re.compile(r"\u00e2\u0165"),  # text-integrity: ignore
    re.compile(r"\u00e2\u201e"),  # text-integrity: ignore
    re.compile(r"\u00e2\u0179"),  # text-integrity: ignore
    re.compile(r"\u00e2\u00ac"),  # text-integrity: ignore
    re.compile(r"\u0102\u2014"),  # text-integrity: ignore
    re.compile(r"\u010f\u00b8"),  # text-integrity: ignore
]


# Escaped-byte mojibake signatures (escaped UTF-8 bytes in string literals).
# These indicate UTF-8 bytes were embedded as Latin-1 style escapes instead of
# proper Unicode escapes (\u.../\U...).
ESCAPED_MOJIBAKE_PATTERNS = [
    re.compile(r"\\xe2\\x[89abAB][0-9a-fA-F]\\x[89abAB][0-9a-fA-F]"),
    re.compile(
        r"\\xf0\\x[89abAB][0-9a-fA-F]\\x[89abAB][0-9a-fA-F]\\x[89abAB][0-9a-fA-F]"
    ),
]

# Scope intentionally limited to Python source where runtime user-facing strings
# and logic live. Reports/docs may legitimately include mojibake examples.
TEXT_SUFFIXES = {
    ".py",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "artifacts",
    "installer_output",
}
IGNORE_MARKER = "text-integrity: ignore"


@dataclass
class FileScanResult:
    path: Path
    has_bom: bool = False
    mojibake_lines: list[int] = field(default_factory=list)
    decode_error: str | None = None

    @property
    def relpath(self) -> str:
        return self.path.as_posix()


@dataclass
class ScanSummary:
    root: Path
    files_scanned: int = 0
    results: list[FileScanResult] = field(default_factory=list)

    def bom_results(self) -> list[FileScanResult]:
        return [r for r in self.results if r.has_bom]

    def mojibake_results(self) -> list[FileScanResult]:
        return [r for r in self.results if r.mojibake_lines]

    def decode_errors(self) -> list[FileScanResult]:
        return [r for r in self.results if r.decode_error]


def _is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def _iter_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if _is_text_candidate(path):
            yield path


def _line_has_mojibake(line: str) -> bool:
    if any(pattern.search(line) for pattern in MOJIBAKE_PATTERNS):
        return True

    if any(pattern.search(line) for pattern in ESCAPED_MOJIBAKE_PATTERNS):
        return True

    # Mojibake often introduces C1 control bytes into source text.
    if any(0x80 <= ord(ch) <= 0x9F for ch in line):
        return True

    # Replacement char indicates lossy decoding has already happened somewhere.
    if "\uFFFD" in line:
        return True

    return False


def _scan_file(path: Path, root: Path) -> FileScanResult:
    rel = path.relative_to(root)
    result = FileScanResult(path=rel)

    raw = path.read_bytes()
    result.has_bom = raw.startswith(UTF8_BOM)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        result.decode_error = str(exc)
        return result

    for idx, line in enumerate(text.splitlines(), start=1):
        if IGNORE_MARKER in line:
            continue
        if _line_has_mojibake(line):
            result.mojibake_lines.append(idx)

    return result


def scan_repository(root: Path) -> ScanSummary:
    summary = ScanSummary(root=root)
    for path in _iter_text_files(root):
        summary.files_scanned += 1
        summary.results.append(_scan_file(path, root))
    return summary


def evaluate_violations(summary: ScanSummary, mode: str) -> list[str]:
    violations: list[str] = []

    for result in summary.decode_errors():
        violations.append(f"Decode error in {result.relpath}: {result.decode_error}")

    if mode == "report":
        return violations

    if mode == "strict":
        for result in summary.bom_results():
            violations.append(f"BOM not allowed in {result.relpath}")
        for result in summary.mojibake_results():
            violations.append(
                f"Mojibake signature(s) in {result.relpath} "
                f"(lines: {', '.join(str(n) for n in result.mojibake_lines[:8])})"
            )
        return violations

    # baseline mode
    for result in summary.bom_results():
        if result.relpath not in BASELINE_BOM_ALLOWED:
            violations.append(f"New BOM file detected: {result.relpath}")

    for result in summary.mojibake_results():
        baseline_limit = BASELINE_MOJIBAKE_MAX.get(result.relpath)
        found = len(result.mojibake_lines)
        if baseline_limit is None:
            violations.append(f"New mojibake file detected: {result.relpath} ({found} lines)")
        elif found > baseline_limit:
            violations.append(
                f"Mojibake worsened in {result.relpath}: {found} > baseline {baseline_limit}"
            )

    return violations


def print_summary(summary: ScanSummary, mode: str, verbose: bool) -> None:
    bom_results = summary.bom_results()
    mojibake_results = summary.mojibake_results()
    decode_errors = summary.decode_errors()

    print(f"Scanned files: {summary.files_scanned}")
    print(f"Mode: {mode}")
    print(f"BOM files: {len(bom_results)}")
    print(f"Mojibake files: {len(mojibake_results)}")
    print(f"Decode errors: {len(decode_errors)}")

    if verbose:
        if bom_results:
            print("BOM details:")
            for result in sorted(bom_results, key=lambda r: r.relpath):
                print(f"  - {result.relpath}")
        if mojibake_results:
            print("Mojibake details:")
            for result in sorted(mojibake_results, key=lambda r: r.relpath):
                print(f"  - {result.relpath}: {len(result.mojibake_lines)} line(s)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check repository text encoding integrity.")
    parser.add_argument(
        "--mode",
        choices=("baseline", "strict", "report"),
        default="baseline",
        help="Validation strictness.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to scan.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-file details.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()

    summary = scan_repository(root)
    print_summary(summary, args.mode, args.verbose)
    violations = evaluate_violations(summary, args.mode)

    if violations:
        print("Violations:")
        for violation in violations:
            print(f"  - {violation}")
        if args.mode == "report":
            return 0
        return 1

    print("Text integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
