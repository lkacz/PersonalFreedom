"""
Merge Dialog Demo - Visual Showcase
====================================
Demonstrates the new industry-standard merge UI.
Run this after installing PyQt5 in your environment.
"""

import sys
from datetime import datetime

try:
    from PySide6 import QtWidgets, QtCore
    PYSIDE_AVAILABLE = True
except ImportError:
    print("PySide6 not installed. Install with: pip install PySide6")
    PYSIDE_AVAILABLE = False
    sys.exit(1)

try:
    from merge_dialog import LuckyMergeDialog
    from gamification import generate_item
    GAMIFICATION_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    GAMIFICATION_AVAILABLE = False
    sys.exit(1)


def create_demo_items(count=3):
    """Create demo items for testing."""
    rarities = ["Common", "Uncommon", "Rare", "Epic"]
    items = []
    for i in range(count):
        rarity = rarities[min(i, len(rarities) - 1)]
        item = generate_item(rarity=rarity)
        items.append(item)
    return items


def main():
    """Run the merge dialog demo."""
    app = QtWidgets.QApplication(sys.argv)
    
    print("=" * 60)
    print("LUCKY MERGE DIALOG - INDUSTRY STANDARD UI DEMO")
    print("=" * 60)
    print()
    print("Features demonstrated:")
    print("  ✓ Visual item preview cards with emoji and rarity colors")
    print("  ✓ Success rate progress bar with color coding")
    print("  ✓ Detailed calculation breakdown")
    print("  ✓ Result preview with expected rarity")
    print("  ✓ Risk warning with clear messaging")
    print("  ✓ Animated merge execution with feedback")
    print("  ✓ Professional color scheme and layout")
    print("  ✓ WCAG 2.1 Level AA accessibility compliance")
    print()
    print("Demo scenarios:")
    print()
    
    # Demo 1: Basic merge
    print("1. Basic Merge (3 items, low luck)")
    items = create_demo_items(3)
    luck = 5
    equipped = {}
    
    dialog = LuckyMergeDialog(items, luck, equipped)
    print(f"   - Items: {len(items)}")
    print(f"   - Success Rate: {dialog.success_rate * 100:.1f}%")
    print(f"   - Expected Result: {dialog.result_rarity}")
    print(f"   - Breakdown: {dialog.breakdown}")
    print()
    
    result = dialog.exec_()
    if result == QtWidgets.QDialog.Accepted:
        if dialog.merge_result and dialog.merge_result.get("success"):
            print("   ✓ MERGE SUCCESS!")
            result_item = dialog.merge_result.get("result_item", {})
            print(f"   - Created: {result_item.get('name', 'Unknown')}")
            print(f"   - Rarity: {result_item.get('rarity', 'Unknown')}")
            print(f"   - Power: {result_item.get('power', 0)}")
        elif dialog.merge_result:
            print("   ✗ Merge Failed - Items lost")
        else:
            print("   - Merge cancelled")
    else:
        print("   - Dialog cancelled by user")
    print()
    
    # Demo 2: High-stakes merge
    print("2. High-Stakes Merge (5 Epic items)")
    items = [generate_item(rarity="Epic") for _ in range(5)]
    luck = 20
    
    # Add gear bonus
    equipped = {
        "Helmet": {
            "name": "Lucky Helmet of Merging",
            "rarity": "Legendary",
            "power": 250,
            "lucky_options": {"merge_luck": 25}
        }
    }
    
    dialog = LuckyMergeDialog(items, luck, equipped)
    print(f"   - Items: {len(items)}")
    print(f"   - Success Rate: {dialog.success_rate * 100:.1f}%")
    print(f"   - Gear Bonus: +{dialog.merge_luck_bonus}%")
    print(f"   - Expected Result: {dialog.result_rarity}")
    print()
    
    result = dialog.exec_()
    if result == QtWidgets.QDialog.Accepted:
        if dialog.merge_result and dialog.merge_result.get("success"):
            print("   ✓ LEGENDARY SUCCESS!")
            result_item = dialog.merge_result.get("result_item", {})
            print(f"   - Created: {result_item.get('name', 'Unknown')}")
            print(f"   - Rarity: {result_item.get('rarity', 'Unknown')}")
            print(f"   - Power: {result_item.get('power', 0)}")
        elif dialog.merge_result:
            print("   ✗ Merge Failed - Epic items lost")
        else:
            print("   - Merge cancelled")
    else:
        print("   - Dialog cancelled by user")
    print()
    
    print("=" * 60)
    print("Demo complete!")
    print()
    print("Key UX Improvements:")
    print("  • Visual feedback at every step")
    print("  • Clear risk/reward presentation")
    print("  • Professional animations and transitions")
    print("  • Comprehensive information display")
    print("  • Accessible color contrast (WCAG AA)")
    print("  • Responsive layout with scroll support")
    print("=" * 60)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
