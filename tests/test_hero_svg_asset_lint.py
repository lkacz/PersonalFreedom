from pathlib import Path

from tools.lint_hero_svg_animations import lint_svg_text, lint_svg_tree


def test_lint_detects_keytimes_values_mismatch() -> None:
    svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <path d="M0 0 L1 1">
    <animate attributeName="d" values="A;B;C" keyTimes="0;0.2;0.4;1" dur="1s" repeatCount="indefinite" />
  </path>
</svg>
""".strip()
    issues = lint_svg_text(svg, "memory.svg")
    codes = {issue.code for issue in issues}
    assert "KEYTIMES_VALUES_MISMATCH" in codes


def test_lint_detects_animate_transform_via_animate() -> None:
    svg = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <circle cx="5" cy="5" r="2">
    <animate attributeName="transform" type="translate" from="0 0" to="0 2" dur="1s" repeatCount="indefinite" />
  </circle>
</svg>
""".strip()
    issues = lint_svg_text(svg, "memory.svg")
    codes = {issue.code for issue in issues}
    assert "ANIMATE_TRANSFORM_VIA_ANIMATE" in codes


def test_hero_svg_assets_have_no_lint_errors() -> None:
    report = lint_svg_tree(Path("icons/heroes"))
    assert report["error_count"] == 0, report["errors"]
