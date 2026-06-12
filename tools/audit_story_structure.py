"""Deep structural audit of all 9 story chapter sets."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gamification as g

VALID_PLACEHOLDERS = {
    "helmet", "weapon", "chestplate", "shield", "gauntlets",
    "boots", "cloak", "amulet", "current_power",
}
STORIES = {
    "warrior": ("WARRIOR_CHAPTERS", "WARRIOR_DECISIONS"),
    "scholar": ("SCHOLAR_CHAPTERS", "SCHOLAR_DECISIONS"),
    "wanderer": ("WANDERER_CHAPTERS", "WANDERER_DECISIONS"),
    "underdog": ("UNDERDOG_CHAPTERS", "UNDERDOG_DECISIONS"),
    "scientist": ("SCIENTIST_CHAPTERS", "SCIENTIST_DECISIONS"),
    "robot": ("ROBOT_CHAPTERS", "ROBOT_DECISIONS"),
    "space_pirate": ("SPACE_PIRATE_CHAPTERS", "SPACE_PIRATE_DECISIONS"),
    "thief": ("THIEF_CHAPTERS", "THIEF_DECISIONS"),
    "zoo_worker": ("ZOO_WORKER_CHAPTERS", "ZOO_WORKER_DECISIONS"),
}
ENDING_PATHS = ["AAA", "AAB", "ABA", "ABB", "BAA", "BAB", "BBA", "BBB"]
PH_RE = re.compile(r"\{([a-z_]+)\}")

problems = []
warnings = []


def prob(story, msg):
    problems.append(f"[{story}] {msg}")


def warn(story, msg):
    warnings.append(f"[{story}] {msg}")


def all_text_blocks(ch):
    """Yield (label, text) for every prose block in a chapter."""
    if "content" in ch:
        yield ("content", ch["content"])
    for k, v in ch.get("content_after_decision", {}).items():
        yield (f"after[{k}]", v)
    for k, v in ch.get("content_variations", {}).items():
        yield (f"var[{k}]", v)
    for k, e in ch.get("endings", {}).items():
        yield (f"ending[{k}].content", e.get("content", ""))


seen_hashes = {}

for story, (ch_name, dec_name) in STORIES.items():
    chapters = getattr(g, ch_name)
    decisions = getattr(g, dec_name)

    # --- registry wiring ---
    if story not in g.STORY_DATA:
        prob(story, "missing from STORY_DATA")
    else:
        if g.STORY_DATA[story]["chapters"] is not chapters:
            prob(story, "STORY_DATA chapters is not the same object")
        if g.STORY_DATA[story]["decisions"] is not decisions:
            prob(story, "STORY_DATA decisions is not the same object")
    if story not in g.STORY_GEAR_THEMES:
        prob(story, "missing from STORY_GEAR_THEMES")

    # --- chapter count / thresholds ---
    if len(chapters) != 7:
        prob(story, f"expected 7 chapters, found {len(chapters)}")
    for i, ch in enumerate(chapters):
        num = i + 1
        thr = ch.get("threshold")
        if thr != g.STORY_THRESHOLDS[i]:
            prob(story, f"ch{num} threshold {thr} != STORY_THRESHOLDS[{i}]={g.STORY_THRESHOLDS[i]}")
        title = ch.get("title", "")
        if not title.startswith(f"Chapter {num}"):
            prob(story, f"ch{num} title doesn't match number: {title!r}")

        # --- structure by chapter role ---
        if num in (2, 4, 6):
            if not ch.get("has_decision"):
                prob(story, f"ch{num} should have has_decision=True")
            did = ch.get("decision_id")
            if not did:
                prob(story, f"ch{num} missing decision_id")
            dec = decisions.get(num)
            if not dec:
                prob(story, f"no decisions[{num}] entry")
            else:
                if dec.get("id") != did:
                    prob(story, f"ch{num} decision_id {did!r} != decisions[{num}].id {dec.get('id')!r}")
                for c in ("A", "B"):
                    cinfo = dec.get("choices", {}).get(c)
                    if not cinfo:
                        prob(story, f"decisions[{num}] missing choice {c}")
                        continue
                    for field in ("label", "short", "description"):
                        if not cinfo.get(field):
                            prob(story, f"decisions[{num}].choices[{c}] missing {field}")
            cad = ch.get("content_after_decision", {})
            if set(cad.keys()) != {"A", "B"}:
                prob(story, f"ch{num} content_after_decision keys {sorted(cad.keys())} != [A, B]")
            for c, txt in cad.items():
                if len(txt.strip()) < 100:
                    prob(story, f"ch{num} after[{c}] suspiciously short ({len(txt.strip())} chars)")
                if "[YOUR CHOICE" not in txt:
                    warn(story, f"ch{num} after[{c}] missing [YOUR CHOICE:] marker")
                else:
                    # label consistency: words of the decision label should appear in the marker
                    marker = txt.split("]")[0].upper()
                    label = decisions.get(num, {}).get("choices", {}).get(c, {}).get("label", "")
                    label_words = [w for w in re.findall(r"[A-Za-z']+", label.upper()) if len(w) > 2]
                    missing = [w for w in label_words if w not in marker]
                    if len(missing) > max(1, len(label_words) // 2):
                        warn(story, f"ch{num} after[{c}] marker may not match label {label!r} (missing {missing})")
            if "CHOICE AWAITS" not in ch.get("content", ""):
                warn(story, f"ch{num} main content missing 'A CHOICE AWAITS' cue")
            if ch.get("content_variations"):
                prob(story, f"ch{num} unexpectedly has content_variations")
        elif num == 3:
            if ch.get("has_decision"):
                prob(story, "ch3 should not have a decision")
            keys = set(ch.get("content_variations", {}).keys())
            if keys != {"A", "B"}:
                prob(story, f"ch3 variation keys {sorted(keys)} != [A, B]")
        elif num == 5:
            keys = set(ch.get("content_variations", {}).keys())
            if keys != {"AA", "AB", "BA", "BB"}:
                prob(story, f"ch5 variation keys {sorted(keys)} != [AA, AB, BA, BB]")
        elif num == 7:
            ends = ch.get("endings", {})
            if set(ends.keys()) != set(ENDING_PATHS):
                prob(story, f"ch7 ending keys {sorted(ends.keys())} != 8 canonical paths")
            for k, e in ends.items():
                if not e.get("title"):
                    prob(story, f"ending[{k}] missing title")
                if len(e.get("content", "").strip()) < 120:
                    prob(story, f"ending[{k}] suspiciously short")
                if "Lesson" not in e.get("content", ""):
                    warn(story, f"ending[{k}] has no Lesson line")
            if not ch.get("content", "").strip():
                warn(story, "ch7 has no framing content before endings")
        elif num == 1:
            if ch.get("has_decision"):
                prob(story, "ch1 should not have a decision")
            if len(ch.get("content", "").strip()) < 200:
                prob(story, "ch1 content suspiciously short")

        # --- text-level checks for every block ---
        for label, txt in all_text_blocks(ch):
            for ph in PH_RE.findall(txt):
                if ph not in VALID_PLACEHOLDERS:
                    prob(story, f"ch{num} {label}: unknown placeholder {{{ph}}}")
            if "  \n" in txt or "\t" in txt:
                warn(story, f"ch{num} {label}: stray tab/trailing spaces")
            h = hash(txt.strip())
            if txt.strip() and h in seen_hashes and seen_hashes[h] != (story, num, label):
                prob(story, f"ch{num} {label}: identical to {seen_hashes[h]} (copy/paste?)")
            seen_hashes.setdefault(h, (story, num, label))
            # mojibake canary
            canaries = ("\ufffd", "\u0111\u017a", "\u00e2\u20ac", "\u010f\u00b8")
            if any(c in txt for c in canaries):
                prob(story, f"ch{num} {label}: mojibake characters present")

        # --- hook coverage (style-aware: report only) ---
        if num < 7:
            hookable = []
            if num in (1,):
                hookable = [("content", ch.get("content", ""))]
            elif num in (3, 5):
                hookable = list(ch.get("content_variations", {}).items())
            else:
                hookable = list(ch.get("content_after_decision", {}).items())
            for label, txt in hookable:
                if not any(m in txt for m in ("NEXT TIME", "FINALE AWAIT")):
                    warn(story, f"ch{num} {label}: no cliffhanger hook")

    # --- decisions dict sanity ---
    extra = set(decisions.keys()) - {2, 4, 6}
    if extra:
        prob(story, f"decisions has unexpected keys {sorted(extra)}")

print("=== PROBLEMS ===" if problems else "=== NO PROBLEMS ===")
for p in problems:
    print(" !", p)
print(f"\n=== WARNINGS ({len(warnings)}) ===")
for w in warnings:
    print(" -", w)
print(f"\nsummary: {len(problems)} problems, {len(warnings)} warnings")
sys.exit(1 if problems else 0)
