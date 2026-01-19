# Story System Flow Analysis & Issues

## ✅ ALL ISSUES FIXED

### 1. **Function Signature Mismatch** ✅ FIXED
**Location**: `gamification.py:10156`
**Problem**: UI called `make_story_decision(adhd_buster, story_id, chapter_num, option_key)` but function signature was `make_story_decision(adhd_buster, chapter_number, choice)`.
**Fix**: Updated UI to call with correct 3 parameters.

### 2. **Return Type Mismatch** ✅ FIXED
**Location**: `gamification.py:10156`
**Problem**: UI expected `result.get("success")`, `result.get("choice_label")`, `result.get("outcome")` but function returned `bool`.
**Fix**: Updated `make_story_decision` to return dict with success, choice_label, outcome, story_id.

### 3. **Chapter Decision Data Access** ✅ FIXED
**Location**: `focus_blocker_qt.py:20797`
**Problem**: UI accessed `chapter.get("decision_prompt")`, `chapter.get("options")` from chapter data, but this wasn't in the right structure.
**Fix**: Now fetches decision data from `story_decisions` dict via `get_story_data()`.

### 4. **Content Not Personalized** ✅ FIXED
**Location**: `focus_blocker_qt.py:20736`
**Problem**: UI read `full_chapter.get("content")` directly instead of using personalized content.
**Fix**: Now uses `get_chapter_content()` which handles:
- Gear personalization (helmet, weapon, etc. names in story)
- Decision-based content variations (chapters 3, 5, 7)
- Chapter 7 multiple endings based on decision path

## Flow Analysis

### Current Story Flow (As Designed)
1. **Story Selection** ✅ WORKS
   - User selects story from dropdown
   - If locked, prompts for coin payment
   - Switches active story, loads hero data
   - GameState signal fires to update UI

2. **Chapter Unlocking** ✅ WORKS
   - Based on power thresholds
   - Max power ever reached (permanent unlock)
   - Progress tracked per story

3. **Reading Chapters** ⚠️ PARTIAL
   - ✅ Loads full chapter content correctly (fixed in last commit)
   - ✅ Shows unlock status correctly
   - ❌ Decision UI won't work (missing data)

4. **Making Decisions** ❌ BROKEN
   - ❌ Function call will crash
   - ❌ No feedback after decision
   - ❌ Decision options won't display

5. **Decision Persistence** ✅ WORKS (if UI fixed)
   - Stored in `adhd_buster["story_decisions"]`
   - Keyed by decision ID (e.g., "warrior_mirror")
   - Synced to hero data per story

### Data Structures

#### Chapter in Story Definition (gamification.py)
```python
{
    "title": "Chapter 1: The Echoing Room",
    "threshold": 0,
    "has_decision": False,
    "content": "...",
    # For chapters with decisions:
    "content_variations": {"A": "...", "B": "..."},
    "decision_id": "warrior_mirror"
}
```

#### Decision Definition (gamification.py)
```python
WARRIOR_DECISIONS = {
    2: {
        "id": "warrior_mirror",
        "prompt": "...",
        "choices": {
            "A": {"label": "🔥 Burn Every Shard", ...},
            "B": {"label": "🔍 Study the Fragments", ...}
        }
    }
}
```

#### Chapter in Progress (from get_story_progress)
```python
{
    "number": 1,
    "title": "Chapter 1: The Echoing Room",
    "unlocked": True,
    "has_decision": False,
    "decision_made": False
}
```

## Required Fixes

### Fix 1: Update make_story_decision to return dict
**File**: `gamification.py`
```python
def make_story_decision(adhd_buster: dict, chapter_number: int, choice: str) -> dict:
    """Record a story decision. Returns result dict."""
    ensure_hero_structure(adhd_buster)
    story_decisions, _ = get_story_data(adhd_buster)
    decision_info = story_decisions.get(chapter_number)
    
    if not decision_info:
        return {"success": False, "error": "No decision at this chapter"}
    if choice not in ("A", "B"):
        return {"success": False, "error": "Invalid choice"}
    
    if "story_decisions" not in adhd_buster:
        adhd_buster["story_decisions"] = {}
    
    adhd_buster["story_decisions"][decision_info["id"]] = choice
    sync_hero_data(adhd_buster)
    
    choice_data = decision_info["choices"][choice]
    return {
        "success": True,
        "choice": choice,
        "choice_label": choice_data["label"],
        "outcome": choice_data.get("description", "Your choice will shape the story...")
    }
```

### Fix 2: Update UI to call with correct parameters
**File**: `focus_blocker_qt.py`
```python
def _make_story_decision(self, chapter_num: int, option_key: str, dialog: QtWidgets.QDialog) -> None:
    """Make a story decision for a chapter."""
    if not GAMIFICATION_AVAILABLE:
        return
    
    from gamification import make_story_decision, AVAILABLE_STORIES
    
    result = make_story_decision(self.blocker.adhd_buster, chapter_num, option_key)
    
    if result.get("success"):
        self.blocker.save_config()
        dialog.accept()
        
        show_info(
            self, "Decision Made!",
            f"You chose: {result.get('choice_label', option_key)}\n\n"
            f"{result.get('outcome', 'Your choice will shape the story...')}"
        )
        
        self._refresh_story_chapter_list()
        
        if self._game_state:
            story_id = result.get("story_id")  # Get from adhd_buster
            self._game_state.set_story(story_id)
    else:
        show_error(self, "Error", result.get("error", "Failed to make decision."))
```

### Fix 3: Update decision UI to fetch correct data
**File**: `focus_blocker_qt.py:20790-20840`
```python
if chapter_progress.get("has_decision") and not chapter_progress.get("decision_made"):
    # Fetch decision info from story decisions
    from gamification import get_story_data
    story_decisions, _ = get_story_data(self.blocker.adhd_buster)
    decision_info = story_decisions.get(chapter_num)
    
    if decision_info:
        decision_frame = QtWidgets.QFrame()
        # ... styling ...
        
        decision_title = QtWidgets.QLabel("<h3>⚡ A Pivotal Decision</h3>")
        decision_layout.addWidget(decision_title)
        
        decision_prompt = QtWidgets.QLabel(decision_info.get("prompt", "What will you do?"))
        decision_prompt.setWordWrap(True)
        decision_layout.addWidget(decision_prompt)
        
        btn_layout = QtWidgets.QHBoxLayout()
        for choice_key, choice_data in decision_info.get("choices", {}).items():
            btn = QtWidgets.QPushButton(choice_data.get("label", choice_key))
            btn.setStyleSheet("padding: 10px 20px; font-size: 12px;")
            btn.clicked.connect(lambda checked, ck=choice_key: self._make_story_decision(chapter_num, ck, dialog))
            btn_layout.addWidget(btn)
        decision_layout.addLayout(btn_layout)
        
        layout.addWidget(decision_frame)
```

## Edge Cases to Test

1. ✅ **Switching Stories Mid-Progress**
   - Each story has separate hero data
   - Decisions are story-specific
   - Progress is story-specific

2. ⚠️ **Reading Chapter Before Power Threshold**
   - Should show locked message
   - Need to verify power requirement display is correct

3. ❌ **Making Decision Twice** 
   - UI checks `decision_made` flag
   - But what if user restarts story? Need to verify decisions clear on restart.

4. ⚠️ **Content Variations After Decisions**
   - Chapters 3, 5, 7 have content_variations based on previous decisions
   - Need to verify `get_chapter_content()` is used (currently UI just uses base content)

5. ⚠️ **Restart Story**
   - Should clear decisions
   - Should keep unlocked chapters (based on max power)
   - Need to verify this logic

## Recommendations

1. **Immediate**: Fix the function signature mismatch (critical crashes)
2. **High Priority**: Fix decision UI data access
3. **Medium Priority**: Verify content variations work for chapters 3, 5, 7
4. **Low Priority**: Add more user feedback (animations, sounds)
5. **Testing**: Create comprehensive test suite for story flow
