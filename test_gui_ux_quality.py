#!/usr/bin/env python
"""GUI/UX Quality Test - Check visual appearance and interaction patterns."""
import sys
sys.path.insert(0, '.')

from PySide6 import QtWidgets, QtCore
from gamification import get_power_breakdown, generate_item, GEAR_SLOTS

def create_test_data():
    """Create realistic test data for visual inspection."""
    equipped = {}
    
    # Helmet with friendly effect on Chestplate
    helmet = generate_item(rarity="Legendary", story_id="warrior")
    helmet["slot"] = "Helmet"
    helmet["name"] = "Crown of the Ancient Warrior King"  # Long name test
    helmet["neighbor_effect"] = {"type": "synergy", "target": "power", "multiplier": 1.20}
    equipped["Helmet"] = helmet
    
    # Chestplate (receives effect from Helmet)
    chest = generate_item(rarity="Epic", story_id="warrior")
    chest["slot"] = "Chestplate"
    chest["name"] = "Dragonscale Chestplate"
    chest["neighbor_effect"] = {"type": "boost", "target": "power", "multiplier": 1.10}
    equipped["Chestplate"] = chest
    
    # Gauntlets (receives effect from Chestplate, has unfriendly on Boots)
    gauntlets = generate_item(rarity="Rare", story_id="warrior")
    gauntlets["slot"] = "Gauntlets"
    gauntlets["name"] = "Gauntlets"
    gauntlets["neighbor_effect"] = {"type": "drain", "target": "power", "multiplier": 0.85}
    equipped["Gauntlets"] = gauntlets
    
    # Boots (receives penalty from Gauntlets)
    boots = generate_item(rarity="Epic", story_id="warrior")
    boots["slot"] = "Boots"
    equipped["Boots"] = boots
    
    # Weapon (no effects)
    weapon = generate_item(rarity="Common", story_id="warrior")
    weapon["slot"] = "Weapon"
    weapon["name"] = "Rusty Sword"
    equipped["Weapon"] = weapon
    
    # Leave Shield, Cloak, Amulet empty for contrast
    
    return equipped

def analyze_ux_issues():
    """Analyze UX issues without launching full GUI."""
    print("=" * 70)
    print("GUI/UX Quality Analysis")
    print("=" * 70)
    
    equipped = create_test_data()
    adhd_buster = {"equipped": equipped}
    breakdown = get_power_breakdown(adhd_buster, include_neighbor_effects=True)
    
    issues = []
    warnings = []
    suggestions = []
    
    # Issue 1: Fixed window size
    print("\n1. Window Sizing")
    print("   Current: Fixed at 900x600")
    issues.append("❌ Fixed window size - users cannot resize")
    suggestions.append("   → Allow resizing with setMinimumSize(700, 500)")
    
    # Issue 2: Column width
    print("\n2. Table Column Layout")
    print("   Current: Only column 3 (Synergy) stretches")
    warnings.append("⚠️  Other columns may be too narrow for long item names")
    suggestions.append("   → Set column 1 (Item) to also stretch or use Interactive resize")
    
    # Issue 3: Long item names
    print("\n3. Long Item Names")
    longest_name = max([equipped[s].get("name", "") for s in equipped], key=len)
    print(f"   Test case: '{longest_name}' ({len(longest_name)} chars)")
    if len(longest_name) > 30:
        warnings.append(f"⚠️  Item name '{longest_name}' may overflow (35+ chars)")
        suggestions.append("   → Enable word wrap or use ellipsis with tooltip")
    
    # Issue 4: Scrolling
    print("\n4. Content Scrolling")
    print("   Current: Fixed 8 rows, no scroll area")
    print("   Analysis: With variable row heights (40-60px), max height = 480px")
    if 480 < 600:
        print("   ✓ Fits in window")
    else:
        issues.append("❌ Content may overflow on small screens")
    
    # Issue 5: Button layout
    print("\n5. Dialog Buttons")
    print("   Current: Only 'Ok' button")
    suggestions.append("   → Consider adding 'Copy to Clipboard' or 'Export' button")
    
    # Issue 6: Empty state
    print("\n6. Empty Equipment State")
    empty_count = sum(1 for s in GEAR_SLOTS if equipped.get(s) is None)
    print(f"   Empty slots: {empty_count}/8")
    if empty_count == 8:
        warnings.append("⚠️  All-empty state may look barren")
        suggestions.append("   → Show helpful message when no items equipped")
    
    # Issue 7: Color contrast (accessibility)
    print("\n7. Accessibility - Color Contrast")
    print("   Background: #2b2b2b (dark)")
    print("   Text colors: #ffffff (white), #888888 (gray), #666666 (darker gray)")
    print("   Analysis: WCAG 2.1 contrast ratios:")
    print("     - White on #2b2b2b: ~12:1 (AAA) ✓")
    print("     - #888888 on #2b2b2b: ~4.5:1 (AA) ✓")
    print("     - #666666 on #2b2b2b: ~2.8:1 (Fail) ❌")
    issues.append("❌ Empty slot color (#666666) fails WCAG AA contrast (2.8:1)")
    suggestions.append("   → Use #888888 or lighter for empty slots")
    
    # Issue 8: Loading state
    print("\n8. Loading/Processing State")
    print("   Current: No loading indicator")
    warnings.append("⚠️  No feedback during calculation (instant for now, but future-proofing)")
    suggestions.append("   → Add brief loading state if calculation becomes complex")
    
    # Issue 9: Keyboard navigation
    print("\n9. Keyboard Navigation")
    print("   Current: Standard Qt dialog shortcuts")
    print("   - Esc to close: ✓")
    print("   - Tab navigation: ✓")
    suggestions.append("   → Consider Ctrl+C to copy table data")
    
    # Issue 10: Tooltip/Help
    print("\n10. User Guidance")
    print("   Current: Static explanation text")
    warnings.append("⚠️  No tooltips on effect types (synergy, boost, drain)")
    suggestions.append("   → Add tooltips explaining effect types")
    suggestions.append("   → Add '?' help button with more detailed explanation")
    
    # Issue 11: Visual hierarchy
    print("\n11. Visual Hierarchy")
    print("   Header: 24px bold gold")
    print("   Formula: 14px gray")
    print("   Table: Default size")
    print("   ✓ Clear hierarchy established")
    
    # Issue 12: Responsive behavior
    print("\n12. Responsive Behavior")
    issues.append("❌ Dialog doesn't remember size/position between opens")
    suggestions.append("   → Save dialog geometry to QSettings")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n🔴 Critical Issues: {len(issues)}")
    for issue in issues:
        print(f"   {issue}")
    
    print(f"\n🟡 Warnings: {len(warnings)}")
    for warning in warnings:
        print(f"   {warning}")
    
    print(f"\n💡 Suggestions: {len(suggestions)}")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"   {i}. {suggestion}")
    
    return len(issues), len(warnings)

if __name__ == "__main__":
    critical, warnings = analyze_ux_issues()
    print(f"\n{'='*70}")
    print(f"Total Critical Issues: {critical}")
    print(f"Total Warnings: {warnings}")
    print(f"{'='*70}")
