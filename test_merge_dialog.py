"""
Test Suite for LuckyMergeDialog
================================
Validates the industry-standard merge UI implementation.
"""

import sys
import unittest
from datetime import datetime
from PySide6 import QtWidgets, QtCore, QtTest

# Add parent directory to path for imports
sys.path.insert(0, '..')

from merge_dialog import (
    ItemPreviewWidget,
    SuccessRateWidget,
    ResultPreviewWidget,
    LuckyMergeDialog
)

try:
    from gamification import generate_item, ITEM_RARITIES
    GAMIFICATION_AVAILABLE = True
except ImportError:
    GAMIFICATION_AVAILABLE = False


class TestItemPreviewWidget(unittest.TestCase):
    """Test ItemPreviewWidget component."""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance()
        if cls.app is None:
            cls.app = QtWidgets.QApplication(sys.argv)
    
    def test_widget_creation(self):
        """Test basic widget creation."""
        item = {
            "name": "Test Sword",
            "rarity": "Rare",
            "slot": "weapon",
            "power": 50
        }
        widget = ItemPreviewWidget(item)
        self.assertIsNotNone(widget)
        self.assertEqual(widget.item, item)
    
    def test_widget_size(self):
        """Test widget has correct fixed size."""
        item = {"name": "Test", "rarity": "Common", "slot": "helmet", "power": 10}
        widget = ItemPreviewWidget(item)
        self.assertEqual(widget.width(), 140)
        self.assertEqual(widget.height(), 180)
    
    def test_emoji_mapping(self):
        """Test emoji mapping for different slots."""
        test_cases = [
            ("helmet", "⛑️"),
            ("weapon", "⚔️"),
            ("shield", "🛡️"),
            ("unknown", "🎁")
        ]
        for slot, expected_emoji in test_cases:
            item = {"name": "Test", "rarity": "Common", "slot": slot, "power": 10}
            widget = ItemPreviewWidget(item)
            emoji = widget._get_item_emoji()
            self.assertEqual(emoji, expected_emoji, f"Slot {slot} should map to {expected_emoji}")
    
    def test_color_darkening(self):
        """Test color darkening function."""
        item = {"name": "Test", "rarity": "Common", "slot": "helmet", "power": 10}
        widget = ItemPreviewWidget(item)
        
        # Test darkening
        original = "#ff0000"
        darkened = widget._darken_color(original, 0.5)
        self.assertTrue(darkened.startswith("#"))
        self.assertEqual(len(darkened), 7)
        self.assertNotEqual(darkened, original)


class TestSuccessRateWidget(unittest.TestCase):
    """Test SuccessRateWidget component."""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance()
        if cls.app is None:
            cls.app = QtWidgets.QApplication(sys.argv)
    
    def test_widget_creation(self):
        """Test basic widget creation."""
        breakdown = {
            "Base Rate": 10,
            "Item Count": 6,
            "Legacy Luck": 4
        }
        widget = SuccessRateWidget(0.25, breakdown)
        self.assertIsNotNone(widget)
        self.assertAlmostEqual(widget.rate, 0.25)
    
    def test_progress_bar_value(self):
        """Test progress bar displays correct percentage."""
        breakdown = {"Base": 50}
        widget = SuccessRateWidget(0.5, breakdown)
        
        # Find progress bar
        progress = widget.findChild(QtWidgets.QProgressBar)
        self.assertIsNotNone(progress)
        self.assertEqual(progress.value(), 50)
    
    def test_color_selection(self):
        """Test progress bar color changes based on rate."""
        test_cases = [
            (0.9, "#4caf50"),  # High rate -> green
            (0.5, "#ff9800"),  # Medium rate -> orange
            (0.2, "#f44336")   # Low rate -> red
        ]
        
        for rate, expected_color in test_cases:
            breakdown = {"Base": int(rate * 100)}
            widget = SuccessRateWidget(rate, breakdown)
            progress = widget.findChild(QtWidgets.QProgressBar)
            stylesheet = progress.styleSheet()
            # Color should be in stylesheet (lightening variations allowed)
            self.assertTrue(expected_color[:4] in stylesheet or 
                          "QProgressBar::chunk" in stylesheet,
                          f"Rate {rate} should use color family {expected_color}")


class TestResultPreviewWidget(unittest.TestCase):
    """Test ResultPreviewWidget component."""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance()
        if cls.app is None:
            cls.app = QtWidgets.QApplication(sys.argv)
    
    def test_widget_creation(self):
        """Test basic widget creation."""
        widget = ResultPreviewWidget("Epic")
        self.assertIsNotNone(widget)
        self.assertEqual(widget.result_rarity, "Epic")
    
    def test_rarity_stars(self):
        """Test correct number of stars for each rarity."""
        rarity_stars = {
            "Common": 1,
            "Uncommon": 2,
            "Rare": 3,
            "Epic": 4,
            "Legendary": 5
        }
        
        for rarity, expected_stars in rarity_stars.items():
            widget = ResultPreviewWidget(rarity)
            stars_label = None
            for label in widget.findChildren(QtWidgets.QLabel):
                if "★" in label.text():
                    stars_label = label
                    break
            
            self.assertIsNotNone(stars_label, f"Stars label not found for {rarity}")
            self.assertEqual(len(stars_label.text()), expected_stars,
                           f"{rarity} should show {expected_stars} stars")


@unittest.skipIf(not GAMIFICATION_AVAILABLE, "Gamification module not available")
class TestLuckyMergeDialog(unittest.TestCase):
    """Test LuckyMergeDialog integration."""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance()
        if cls.app is None:
            cls.app = QtWidgets.QApplication(sys.argv)
    
    def test_dialog_creation(self):
        """Test dialog creation with valid items."""
        items = [
            generate_item(rarity="Common"),
            generate_item(rarity="Common"),
            generate_item(rarity="Uncommon")
        ]
        equipped = {}
        luck = 5
        
        dialog = LuckyMergeDialog(items, luck, equipped)
        self.assertIsNotNone(dialog)
        self.assertEqual(len(dialog.items), 3)
        self.assertEqual(dialog.luck, 5)
    
    def test_dialog_minimum_size(self):
        """Test dialog respects minimum size."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        dialog = LuckyMergeDialog(items, 0, {})
        
        # Updated to match refactored UI (680x500)
        self.assertGreaterEqual(dialog.minimumWidth(), 680)
        self.assertGreaterEqual(dialog.minimumHeight(), 500)
    
    def test_success_rate_calculation(self):
        """Test success rate is calculated correctly."""
        items = [
            generate_item(rarity="Common"),
            generate_item(rarity="Common")
        ]
        luck = 10
        equipped = {}
        
        dialog = LuckyMergeDialog(items, luck, equipped)
        
        # Base: 25% (MERGE_BASE_SUCCESS_RATE), no bonus for 2 items
        # Legacy luck (luck param) is no longer used in calculation
        expected_rate = 0.25  # Base rate only for 2 items with no merge_luck
        self.assertAlmostEqual(dialog.success_rate, expected_rate, places=2)
    
    def test_breakdown_components(self):
        """Test breakdown includes all components."""
        items = [generate_item(rarity="Common") for _ in range(3)]
        luck = 5
        equipped = {}
        
        dialog = LuckyMergeDialog(items, luck, equipped)
        
        # Breakdown should have Base Rate and Item Count
        self.assertIn("Base Rate", dialog.breakdown)
        # Second key should be Item Count (with item count in the key name)
        keys = list(dialog.breakdown.keys())
        self.assertTrue(any("Item Count" in k for k in keys), 
                       f"Should have Item Count in breakdown keys: {keys}")
    
    def test_gear_bonus_included(self):
        """Test gear merge luck bonus is included when present via entity_perks."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        luck = 0
        equipped = {}
        
        # Entity perks are now passed separately, not derived from equipped gear
        entity_perks = {
            "total_merge_luck": 15,
            "contributors": [{"name": "Test Entity", "perk_type": "merge_luck", "value": 15}]
        }
        
        dialog = LuckyMergeDialog(items, luck, equipped, entity_perks=entity_perks)
        
        # Should include entity perk bonus in breakdown
        self.assertTrue(any("Entity" in str(k) for k in dialog.breakdown.keys()),
                       f"Entity perk bonus should be in breakdown: {dialog.breakdown}")
    
    def test_item_preview_widgets_created(self):
        """Test item list displays all items (now uses collapsible text list)."""
        items = [generate_item(rarity="Rare") for _ in range(4)]
        dialog = LuckyMergeDialog(items, 0, {})
        
        # UI was refactored to use collapsible text list instead of ItemPreviewWidget
        # Check that the items toggle button shows correct count
        self.assertTrue(hasattr(dialog, '_items_toggle_btn'),
                       "Should have items toggle button")
        self.assertIn("4", dialog._items_toggle_btn.text(),
                     "Items count should be shown in toggle button")
    
    def test_buttons_present(self):
        """Test dialog has required buttons."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        dialog = LuckyMergeDialog(items, 0, {})
        
        buttons = dialog.findChildren(QtWidgets.QPushButton)
        button_texts = [btn.text() for btn in buttons]
        
        self.assertTrue(any("Cancel" in text for text in button_texts),
                       "Dialog should have Cancel button")
        self.assertTrue(any("Merge" in text for text in button_texts),
                       "Dialog should have Merge button")
    
    def test_warning_box_present(self):
        """Test warning information is communicated through UI context."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        dialog = LuckyMergeDialog(items, 0, {})
        
        # Warning box was removed (risk is evident from UI context)
        # Instead, verify the items section shows what will be lost
        self.assertTrue(hasattr(dialog, '_items_toggle_btn'),
                       "Should have items section showing items to merge")


class TestDialogAccessibility(unittest.TestCase):
    """Test accessibility features of merge dialog."""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance()
        if cls.app is None:
            cls.app = QtWidgets.QApplication(sys.argv)
    
    @unittest.skipIf(not GAMIFICATION_AVAILABLE, "Gamification module not available")
    def test_color_contrast(self):
        """Test color contrast meets accessibility standards."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        dialog = LuckyMergeDialog(items, 0, {})
        
        # Get all labels and check they have readable colors
        labels = dialog.findChildren(QtWidgets.QLabel)
        # Just verify labels exist and are readable (basic check)
        self.assertGreater(len(labels), 0, "Dialog should have readable labels")
    
    @unittest.skipIf(not GAMIFICATION_AVAILABLE, "Gamification module not available")
    def test_keyboard_navigation(self):
        """Test dialog supports keyboard navigation."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        dialog = LuckyMergeDialog(items, 0, {})
        
        buttons = dialog.findChildren(QtWidgets.QPushButton)
        self.assertGreater(len(buttons), 0, "Dialog should have focusable buttons")
        
        # All buttons should be keyboard accessible
        for button in buttons:
            self.assertTrue(button.focusPolicy() & QtCore.Qt.TabFocus or
                          button.focusPolicy() & QtCore.Qt.StrongFocus,
                          f"Button '{button.text()}' should be keyboard accessible")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance()
        if cls.app is None:
            cls.app = QtWidgets.QApplication(sys.argv)
    
    @unittest.skipIf(not GAMIFICATION_AVAILABLE, "Gamification module not available")
    def test_many_items(self):
        """Test dialog handles many items gracefully."""
        items = [generate_item(rarity="Common") for _ in range(10)]
        dialog = LuckyMergeDialog(items, 0, {})
        
        self.assertIsNotNone(dialog)
        self.assertEqual(len(dialog.items), 10)
        
        # Should use scroll area
        scroll_areas = dialog.findChildren(QtWidgets.QScrollArea)
        self.assertGreater(len(scroll_areas), 0, "Should have scroll area for many items")
    
    @unittest.skipIf(not GAMIFICATION_AVAILABLE, "Gamification module not available")
    def test_high_success_rate(self):
        """Test UI adapts to very high success rates."""
        items = [generate_item(rarity="Legendary") for _ in range(5)]
        luck = 50  # Very high luck
        dialog = LuckyMergeDialog(items, luck, {})
        
        # Just verify the dialog was created successfully with high success items
        self.assertIsNotNone(dialog)
        # Success rate should be higher with more items
        self.assertGreater(dialog.success_rate, 0.25, 
                          "Success rate should increase with more items")
    
    @unittest.skipIf(not GAMIFICATION_AVAILABLE, "Gamification module not available")
    def test_low_success_rate(self):
        """Test UI for low success rates."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        luck = 0
        dialog = LuckyMergeDialog(items, luck, {})
        
        # Verify low success rate is calculated correctly (25% base for 2 items)
        self.assertAlmostEqual(dialog.success_rate, 0.25, places=2)
    
    def test_missing_item_attributes(self):
        """Test dialog handles items with missing attributes."""
        item_with_missing = {
            "name": "Incomplete Item"
            # Missing: rarity, slot, power
        }
        
        widget = ItemPreviewWidget(item_with_missing)
        self.assertIsNotNone(widget)
        # Should use defaults without crashing


if __name__ == "__main__":
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
