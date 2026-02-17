#!/usr/bin/env python3
"""Deep SVG integrity scan for the whole app.

Checks:
- Static patterns:
  - feComponentTransfer + feFuncA
  - empty feMergeNode
  - empty image href
  - filter id used as fill/stroke paint server
  - risky filter regions (%-based and large userSpaceOnUse)
- Runtime Qt parse/load warnings via QSvgRenderer
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from PySide6 import QtCore, QtWidgets
from PySide6.QtSvg import QSvgRenderer


EXCLUDE_PARTS = {"artifacts", ".git", ".pytest_cache", "__pycache__", "node_modules"}
URL_REF_RE = re.compile(r"url\(\s*#([A-Za-z_][A-Za-z0-9_.:-]*)\s*\)")
PERCENT_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)%\s*$")
NUM_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*$")


def _collect_svg_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*.svg"):
        if any(part in EXCLUDE_PARTS for part in p.parts):
            continue
        # Ignore ad-hoc preview composites that are not loaded by app runtime.
        if p.name.lower().startswith("preview_"):
            continue
        files.append(p)
    return sorted(files)


def _runtime_category(message: str) -> str:
    low = message.lower()
    if "types are incorrect" in low:
        return "types_incorrect"
    if "requested buffer size is too big" in low:
        return "buffer_too_big"
    if "invalid path data" in low:
        return "invalid_path_data"
    if "image filename is empty" in low:
        return "image_filename_empty"
    if "could not resolve property" in low:
        return "resolve_property"
    if "starttimer" in low:
        return "timer_warning"
    return "other"


def main() -> int:
    root = Path(".")
    svg_files = _collect_svg_files(root)

    report: dict = {
        "svg_total": len(svg_files),
        "static": {
            "component_transfer_files": [],
            "empty_merge_node_files": [],
            "component_transfer_plus_empty_merge_files": [],
            "empty_image_href_files": [],
            "filter_id_used_as_fill_or_stroke_ref": [],
            "risky_percent_filter_regions": [],
            "risky_userspace_filter_regions": [],
        },
        "runtime": {
            "files_with_messages": {},
            "category_counts": {},
            "files_by_category": {},
        },
    }

    # Static pass
    for path in svg_files:
        rel = str(path).replace("\\", "/")
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        has_comp = "<feComponentTransfer" in text and "<feFuncA" in text
        has_empty_merge = "<feMergeNode/>" in text or "<feMergeNode />" in text
        if has_comp:
            report["static"]["component_transfer_files"].append(rel)
        if has_empty_merge:
            report["static"]["empty_merge_node_files"].append(rel)
        if has_comp and has_empty_merge:
            report["static"]["component_transfer_plus_empty_merge_files"].append(rel)

        if re.search(
            r"<image\b[^>]*(?:href|xlink:href)\s*=\s*([\"'])\s*\1",
            text,
            flags=re.IGNORECASE,
        ):
            report["static"]["empty_image_href_files"].append(rel)

        try:
            xml_root = ET.fromstring(text)
        except Exception:
            continue

        filter_ids: set[str] = set()
        for el in xml_root.iter():
            local = el.tag.rsplit("}", 1)[-1]
            if local != "filter":
                continue
            filter_id = el.attrib.get("id")
            if filter_id:
                filter_ids.add(filter_id)

            x = el.attrib.get("x")
            y = el.attrib.get("y")
            width = el.attrib.get("width")
            height = el.attrib.get("height")
            units = (el.attrib.get("filterUnits") or "").strip()

            flags: list[str] = []
            for key, raw in (("x", x), ("y", y), ("width", width), ("height", height)):
                if not raw:
                    continue
                m = PERCENT_RE.match(raw)
                if not m:
                    continue
                value = float(m.group(1))
                if key in ("width", "height") and value >= 200:
                    flags.append(f"{key}={value}%")
                if key in ("x", "y") and value <= -50:
                    flags.append(f"{key}={value}%")
            if flags:
                report["static"]["risky_percent_filter_regions"].append(
                    {"file": rel, "filter_id": filter_id, "flags": flags}
                )

            if units == "userSpaceOnUse":
                mw = NUM_RE.match(width or "")
                mh = NUM_RE.match(height or "")
                if mw and mh:
                    ww = abs(float(mw.group(1)))
                    hh = abs(float(mh.group(1)))
                    area = ww * hh
                    if ww >= 2048 or hh >= 2048 or area >= 4_000_000:
                        report["static"]["risky_userspace_filter_regions"].append(
                            {
                                "file": rel,
                                "filter_id": filter_id,
                                "width": ww,
                                "height": hh,
                                "area": area,
                            }
                        )

        bad_refs: list[dict] = []
        for el in xml_root.iter():
            for attr in ("fill", "stroke"):
                raw = el.attrib.get(attr)
                if not raw:
                    continue
                m = URL_REF_RE.search(raw)
                if not m:
                    continue
                ref = m.group(1)
                if ref in filter_ids:
                    bad_refs.append({"attr": attr, "ref": ref})
        if bad_refs:
            report["static"]["filter_id_used_as_fill_or_stroke_ref"].append(
                {"file": rel, "refs": bad_refs}
            )

    # Runtime pass
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    category_counts: defaultdict[str, int] = defaultdict(int)
    files_by_category: defaultdict[str, set[str]] = defaultdict(set)

    for path in svg_files:
        rel = str(path).replace("\\", "/")
        messages: list[str] = []
        prev_handler = QtCore.qInstallMessageHandler(
            lambda _t, _c, m, bucket=messages: bucket.append(str(m))
        )
        try:
            QSvgRenderer(str(path))
        finally:
            QtCore.qInstallMessageHandler(prev_handler)
        if not messages:
            continue

        report["runtime"]["files_with_messages"][rel] = messages
        for msg in messages:
            cat = _runtime_category(msg)
            category_counts[cat] += 1
            files_by_category[cat].add(rel)

    # Normalize/sort output
    for key in (
        "component_transfer_files",
        "empty_merge_node_files",
        "component_transfer_plus_empty_merge_files",
        "empty_image_href_files",
    ):
        report["static"][key] = sorted(set(report["static"][key]))
    report["static"]["filter_id_used_as_fill_or_stroke_ref"] = sorted(
        report["static"]["filter_id_used_as_fill_or_stroke_ref"],
        key=lambda x: x["file"],
    )
    report["static"]["risky_percent_filter_regions"] = sorted(
        report["static"]["risky_percent_filter_regions"],
        key=lambda x: (x["file"], str(x.get("filter_id") or "")),
    )
    report["static"]["risky_userspace_filter_regions"] = sorted(
        report["static"]["risky_userspace_filter_regions"],
        key=lambda x: (x["file"], str(x.get("filter_id") or "")),
    )
    report["runtime"]["category_counts"] = dict(sorted(category_counts.items()))
    report["runtime"]["files_by_category"] = {
        key: sorted(vals) for key, vals in sorted(files_by_category.items())
    }

    out_json = Path("artifacts/svg_deep_scan_report.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"SVG_TOTAL={report['svg_total']}")
    print("STATIC_COUNTS:")
    print(
        f"  component_transfer_files={len(report['static']['component_transfer_files'])}"
    )
    print(f"  empty_merge_node_files={len(report['static']['empty_merge_node_files'])}")
    print(
        "  component_transfer_plus_empty_merge_files="
        f"{len(report['static']['component_transfer_plus_empty_merge_files'])}"
    )
    print(f"  empty_image_href_files={len(report['static']['empty_image_href_files'])}")
    print(
        "  filter_id_used_as_fill_or_stroke_ref="
        f"{len(report['static']['filter_id_used_as_fill_or_stroke_ref'])}"
    )
    print(
        "  risky_percent_filter_regions="
        f"{len(report['static']['risky_percent_filter_regions'])}"
    )
    print(
        "  risky_userspace_filter_regions="
        f"{len(report['static']['risky_userspace_filter_regions'])}"
    )

    print("RUNTIME_CATEGORY_COUNTS:")
    for key, value in report["runtime"]["category_counts"].items():
        files_count = len(report["runtime"]["files_by_category"].get(key, []))
        print(f"  {key}={value} msgs across {files_count} files")

    for cat in (
        "types_incorrect",
        "resolve_property",
        "image_filename_empty",
        "buffer_too_big",
        "invalid_path_data",
    ):
        files = report["runtime"]["files_by_category"].get(cat, [])
        if not files:
            continue
        print(f"TOP_{cat}_FILES:")
        for p in files[:40]:
            print(f"  {p}")

    print(f"REPORT_JSON={out_json.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
