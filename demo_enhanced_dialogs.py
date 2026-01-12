"""
Demo script for testing all enhanced dialogs.
"""
import sys
from PySide6 import QtWidgets, QtCore

# Import all enhanced dialogs
from item_drop_dialog import EnhancedItemDropDialog
from level_up_dialog import EnhancedLevelUpDialog
from emergency_cleanup_dialog import EmergencyCleanupDialog, show_emergency_cleanup_dialog


class DemoWindow(QtWidgets.QWidget):
    """Demo window with buttons to test each dialog."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Dialogs Demo")
        self.resize(400, 300)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Title
        title = QtWidgets.QLabel("Enhanced Dialogs Demo")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Item Drop Dialog button
        item_btn = QtWidgets.QPushButton("🎁 Test Item Drop Dialog")
        item_btn.clicked.connect(self.test_item_drop)
        item_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        layout.addWidget(item_btn)
        
        # Level Up Dialog button
        level_btn = QtWidgets.QPushButton("🎊 Test Level Up Dialog")
        level_btn.clicked.connect(self.test_level_up)
        level_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        layout.addWidget(level_btn)
        
        # Emergency Cleanup Dialog button
        cleanup_btn = QtWidgets.QPushButton("⚠️ Test Emergency Cleanup Dialog")
        cleanup_btn.clicked.connect(self.test_cleanup)
        cleanup_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c62828;
            }
        """)
        layout.addWidget(cleanup_btn)
        
        # Test all button
        all_btn = QtWidgets.QPushButton("✨ Test All Dialogs")
        all_btn.clicked.connect(self.test_all)
        all_btn.setStyleSheet("""
            QPushButton {
                background-color: #9c27b0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
        """)
        layout.addWidget(all_btn)
        
        layout.addStretch()
        
        # Info label
        info = QtWidgets.QLabel("Click any button to test the corresponding dialog.")
        info.setStyleSheet("color: #666; font-size: 11px; padding: 10px;")
        info.setAlignment(QtCore.Qt.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)
    
    def test_item_drop(self):
        """Test the enhanced item drop dialog."""
        # Create test item (Legendary)
        new_item = {
            "name": "Legendary Focus Blade",
            "rarity": "Legendary",
            "slot": "Weapon",
            "power": 150,
            "lucky_options": {
                "coin_bonus": 50,
                "xp_bonus": 25
            },
            "lucky_upgrade": True
        }
        
        # Create equipped item for comparison
        equipped_item = {
            "name": "Epic Focus Sword",
            "rarity": "Epic",
            "slot": "Weapon",
            "power": 100
        }
        
        dialog = EnhancedItemDropDialog(
            new_item,
            equipped_item,
            session_minutes=45,
            streak_days=7,
            coins_earned=250,
            parent=self
        )
        
        dialog.quick_equip_requested.connect(
            lambda: self.show_result("Quick Equip Requested!")
        )
        dialog.view_inventory.connect(
            lambda: self.show_result("View Inventory Requested!")
        )
        
        result = dialog.exec()
        self.show_result(f"Item Drop Dialog: {'Accepted' if result else 'Rejected'}")
    
    def test_level_up(self):
        """Test the enhanced level up dialog."""
        old_level = 10
        new_level = 12  # Multi-level gain for fullscreen
        
        stats = {
            "total_power": 567,
            "total_xp": 5420,
            "total_coins": 1890,
            "productivity_score": 8500,
            "total_focus_minutes": 1250,
            "items_collected": 34,
            "unlocks": [
                "Epic Item Drops",
                "Legendary Merge Chance",
                "Advanced Story Quests"
            ],
            "rewards": ["Epic Item Box", "500 Coins"]
        }
        
        dialog = EnhancedLevelUpDialog(old_level, new_level, stats, fullscreen=False, parent=self)
        
        dialog.view_stats.connect(
            lambda: self.show_result("View Stats Requested!")
        )
        dialog.claim_rewards.connect(
            lambda: self.show_result("Claim Rewards Requested!")
        )
        
        result = dialog.exec()
        self.show_result(f"Level Up Dialog: {'Accepted' if result else 'Rejected'}")
    
    def test_cleanup(self):
        """Test the emergency cleanup dialog."""
        impact_data = {
            "items_count": 34,
            "power_lost": 567,
            "progress_percent": 45,
            "coins_refund": 0,
            "items_affected": [
                {"name": "Epic Focus Sword", "rarity": "Epic"},
                {"name": "Legendary Shield", "rarity": "Legendary"},
                {"name": "Rare Helmet", "rarity": "Rare"},
                {"name": "Common Boots", "rarity": "Common"},
                {"name": "Uncommon Gloves", "rarity": "Uncommon"},
            ]
        }
        
        confirmed = show_emergency_cleanup_dialog("reset_progress", impact_data, self)
        self.show_result(f"Emergency Cleanup: {'CONFIRMED' if confirmed else 'Cancelled'}")
    
    def test_all(self):
        """Test all dialogs in sequence."""
        self.show_result("Testing all dialogs in sequence...")
        
        # Item drop first
        QtCore.QTimer.singleShot(500, self.test_item_drop)
        QtCore.QTimer.singleShot(2000, self.test_level_up)
        QtCore.QTimer.singleShot(4000, self.test_cleanup)
    
    def show_result(self, message: str):
        """Show test result."""
        QtWidgets.QMessageBox.information(self, "Demo Result", message)


def main():
    """Run demo application."""
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = DemoWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
