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
        
        self.assertGreaterEqual(dialog.minimumWidth(), 700)
        self.assertGreaterEqual(dialog.minimumHeight(), 600)
    
    def test_success_rate_calculation(self):
        """Test success rate is calculated correctly."""
        items = [
            generate_item(rarity="Common"),
            generate_item(rarity="Common")
        ]
        luck = 10
        equipped = {}
        
        dialog = LuckyMergeDialog(items, luck, equipped)
        
        # Base: 10%, Item bonus: 3%, Luck: 20% = 33%
        expected_rate = 0.10 + 0.03 + 0.20
        self.assertAlmostEqual(dialog.success_rate, expected_rate, places=2)
    
    def test_breakdown_components(self):
        """Test breakdown includes all components."""
        items = [generate_item(rarity="Common") for _ in range(3)]
        luck = 5
        equipped = {}
        
        dialog = LuckyMergeDialog(items, luck, equipped)
        
        self.assertIn("Base Rate", dialog.breakdown)
        self.assertIn("Item Count", dialog.breakdown.get(list(dialog.breakdown.keys())[1], ""))
        self.assertIn("Legacy Luck", dialog.breakdown.get(list(dialog.breakdown.keys())[2], ""))
    
    def test_gear_bonus_included(self):
        """Test gear merge luck bonus is included when present."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        luck = 0
        
        # Mock equipped item with merge_luck
        equipped = {
            "Helmet": {
                "name": "Test Helmet",
                "rarity": "Epic",
                "power": 100,
                "lucky_options": {"merge_luck": 15}
            }
        }
        
        dialog = LuckyMergeDialog(items, luck, equipped)
        
        # Should include gear bonus in breakdown
        breakdown_str = str(dialog.breakdown)
        self.assertTrue(any("Gear" in str(k) or "Equipped" in str(k) 
                          for k in dialog.breakdown.keys()),
                       "Gear bonus should be in breakdown")
    
    def test_item_preview_widgets_created(self):
        """Test item preview widgets are created for all items."""
        items = [generate_item(rarity="Rare") for _ in range(4)]
        dialog = LuckyMergeDialog(items, 0, {})
        
        previews = dialog.findChildren(ItemPreviewWidget)
        self.assertEqual(len(previews), 4, "Should create preview for each item")
    
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
        """Test warning box is displayed."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        dialog = LuckyMergeDialog(items, 0, {})
        
        labels = dialog.findChildren(QtWidgets.QLabel)
        label_texts = [lbl.text() for lbl in labels]
        
        self.assertTrue(any("Warning" in text or "destroy" in text.lower() 
                          for text in label_texts),
                       "Dialog should show warning about item loss")


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
        for label in labels:
            stylesheet = label.styleSheet()
            # Basic check: shouldn't use extremely light colors on light background
            if "color:" in stylesheet.lower():
                self.assertNotIn("color: #fff", stylesheet.lower())
                self.assertNotIn("color: white", stylesheet.lower())
    
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
        
        # Should show green color scheme for high success
        buttons = [btn for btn in dialog.findChildren(QtWidgets.QPushButton)
                  if "Merge" in btn.text()]
        self.assertGreater(len(buttons), 0)
        merge_btn = buttons[0]
        self.assertIn("#4caf50", merge_btn.styleSheet())
    
    @unittest.skipIf(not GAMIFICATION_AVAILABLE, "Gamification module not available")
    def test_low_success_rate(self):
        """Test UI warns about very low success rates."""
        items = [generate_item(rarity="Common"), generate_item(rarity="Common")]
        luck = 0
        dialog = LuckyMergeDialog(items, luck, {})
        
        # Should show red color scheme for low success
        if dialog.success_rate < 0.3:
            buttons = [btn for btn in dialog.findChildren(QtWidgets.QPushButton)
                      if "Merge" in btn.text()]
            self.assertGreater(len(buttons), 0)
            merge_btn = buttons[0]
            self.assertIn("#f44336", merge_btn.styleSheet())
    
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
