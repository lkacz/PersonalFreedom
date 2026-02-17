#!/usr/bin/env python3
"""Lint hero SVG animation assets for integrity and compatibility risks.

This checker focuses on SMIL correctness and known fragile patterns:
- `keyTimes` / `values` cardinality mismatches.
- `calcMode="spline"` / `keySplines` cardinality mismatches.
- `<animate attributeName="transform">` (prefer `animateTransform`).
- Very fast loops (`dur < 0.2s`) as performance warnings.
"""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


SMIL_TAG_PATTERN = re.compile(
    r"<(animate|animateTransform|animateMotion|set)\b[^>]*>",
    re.IGNORECASE | re.DOTALL,
)
ATTR_PATTERN = re.compile(r'([:\w-]+)\s*=\s*"([^"]*)"')
DUR_SECONDS_PATTERN = re.compile(r"^\s*([0-9]*\.?[0-9]+)s\s*$", re.IGNORECASE)

ERROR_CODES = {
    "XML_PARSE_ERROR",
    "KEYTIMES_VALUES_MISMATCH",
    "KEYSPLINES_MISMATCH",
    "ANIMATE_TRANSFORM_VIA_ANIMATE",
}
WARNING_CODES = {
    "VERY_FAST_ANIMATION",
}


@dataclass(frozen=True)
class SvgLintIssue:
    file: str
    code: str
    severity: str  # error | warning
    message: str
    line: int | None = None


def _split_semicolon_values(raw: str) -> list[str]:
    return [part.strip() for part in str(raw).split(";") if part.strip()]


def _line_number_for_offset(content: str, offset: int) -> int:
    # 1-based line number
    return content.count("\n", 0, max(0, offset)) + 1


def lint_svg_text(content: str, file_label: str) -> list[SvgLintIssue]:
    issues: list[SvgLintIssue] = []
    try:
        ET.fromstring(content)
    except ET.ParseError as exc:
        issues.append(
            SvgLintIssue(
                file=file_label,
                code="XML_PARSE_ERROR",
                severity="error",
                message=str(exc),
                line=None,
            )
        )
        return issues

    for match in SMIL_TAG_PATTERN.finditer(content):
        tag_name = match.group(1)
        raw_tag = match.group(0)
        attrs = {k: v for k, v in ATTR_PATTERN.findall(raw_tag)}
        line = _line_number_for_offset(content, match.start())

        values = _split_semicolon_values(attrs.get("values", ""))
        key_times = _split_semicolon_values(attrs.get("keyTimes", ""))
        key_splines = _split_semicolon_values(attrs.get("keySplines", ""))
        calc_mode = attrs.get("calcMode", "").strip().lower()
        attribute_name = attrs.get("attributeName", "").strip()

        if values and key_times and len(values) != len(key_times):
            issues.append(
                SvgLintIssue(
                    file=file_label,
                    code="KEYTIMES_VALUES_MISMATCH",
                    severity="error",
                    message=(
                        f"{tag_name}: values has {len(values)} entries but keyTimes has {len(key_times)}"
                    ),
                    line=line,
                )
            )

        if calc_mode == "spline" and key_times and key_splines:
            expected = max(len(key_times) - 1, 0)
            if len(key_splines) != expected:
                issues.append(
                    SvgLintIssue(
                        file=file_label,
                        code="KEYSPLINES_MISMATCH",
                        severity="error",
                        message=(
                            f"{tag_name}: keySplines has {len(key_splines)} entries, expected {expected} "
                            f"for keyTimes={len(key_times)}"
                        ),
                        line=line,
                    )
                )

        if tag_name.lower() == "animate" and attribute_name == "transform":
            issues.append(
                SvgLintIssue(
                    file=file_label,
                    code="ANIMATE_TRANSFORM_VIA_ANIMATE",
                    severity="error",
                    message="Use animateTransform instead of animate for attributeName='transform'",
                    line=line,
                )
            )

        dur_raw = attrs.get("dur", "")
        dur_match = DUR_SECONDS_PATTERN.match(dur_raw)
        if dur_match:
            duration_s = float(dur_match.group(1))
            if duration_s < 0.2:
                issues.append(
                    SvgLintIssue(
                        file=file_label,
                        code="VERY_FAST_ANIMATION",
                        severity="warning",
                        message=f"{tag_name} has dur={duration_s:.3f}s (<0.2s)",
                        line=line,
                    )
                )

    return issues


def lint_svg_file(path: Path) -> list[SvgLintIssue]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return lint_svg_text(text, str(path).replace("\\", "/"))


def lint_svg_tree(root: Path) -> dict[str, object]:
    svg_files = sorted(root.rglob("*.svg"))
    issues: list[SvgLintIssue] = []
    for svg_path in svg_files:
        issues.extend(lint_svg_file(svg_path))

    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    return {
        "root": str(root).replace("\\", "/"),
        "scanned_files": len(svg_files),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def _serialize_issues(issues: Iterable[SvgLintIssue]) -> list[dict]:
    return [asdict(issue) for issue in issues]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lint hero SVG animation assets.")
    parser.add_argument(
        "--root",
        default="icons/heroes",
        help="Root directory to scan (default: icons/heroes).",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit JSON output.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Return non-zero exit code when warnings are present.",
    )
    parser.add_argument(
        "--show-warnings",
        action="store_true",
        help="Print warning rows in text output.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    root = Path(args.root)
    if not root.exists():
        print(f"Root not found: {root}")
        return 2

    report = lint_svg_tree(root)
    errors = report["errors"]
    warnings = report["warnings"]

    if args.as_json:
        payload = {
            "root": report["root"],
            "scanned_files": report["scanned_files"],
            "error_count": report["error_count"],
            "warning_count": report["warning_count"],
            "errors": _serialize_issues(errors),
            "warnings": _serialize_issues(warnings),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"Scanned {report['scanned_files']} SVG files in {report['root']} | "
            f"errors={report['error_count']} warnings={report['warning_count']}"
        )
        for issue in errors:
            line_hint = f":{issue.line}" if issue.line else ""
            print(f"[ERROR] {issue.file}{line_hint} [{issue.code}] {issue.message}")
        if args.show_warnings:
            for issue in warnings:
                line_hint = f":{issue.line}" if issue.line else ""
                print(f"[WARN] {issue.file}{line_hint} [{issue.code}] {issue.message}")

    if errors:
        return 1
    if args.fail_on_warning and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
