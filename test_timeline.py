"""Quick test script for Timeline widgets."""
import sys
from datetime import datetime
from PySide6 import QtWidgets, QtCore

# Mock blocker for testing
class MockBlocker:
    def __init__(self):
        self.stats = {
            "daily_stats": {
                datetime.now().strftime("%Y-%m-%d"): {
                    "focus_time": 7200  # 2 hours
                }
            }
        }
        self.water_entries = [
            {"date": datetime.now().strftime("%Y-%m-%d"), "time": "08:00"},
            {"date": datetime.now().strftime("%Y-%m-%d"), "time": "10:30"},
            {"date": datetime.now().strftime("%Y-%m-%d"), "time": "14:00"},
        ]
        self.sleep_entries = [
            {
                "date": (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "bedtime": "23:00",
                "wake_time": "07:30"
            }
        ]
        self.adhd_buster = {
            "hero": {
                "xp": 1500,
                "level": 5,
                "class": "Warrior"
            }
        }

if __name__ == "__main__":
    from datetime import timedelta
    
    # Import the widgets from main file
    sys.path.insert(0, ".")
    from focus_blocker_qt import load_heavy_modules, FocusRingWidget, ChronoStreamWidget, DailyTimelineWidget
    
    app = QtWidgets.QApplication(sys.argv)
    
    # Load modules
    load_heavy_modules()
    
    # Create test window
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Timeline Widget Test")
    window.resize(1000, 300)
    
    central = QtWidgets.QWidget()
    window.setCentralWidget(central)
    layout = QtWidgets.QVBoxLayout(central)
    
    # Create timeline with mock blocker
    blocker = MockBlocker()
    timeline = DailyTimelineWidget(blocker, window)
    layout.addWidget(timeline)
    
    # Add some debug info
    info_label = QtWidgets.QLabel("Timeline Widget Test - Check for visual errors")
    info_label.setStyleSheet("padding: 10px; background: #1a1a2e; color: white;")
    layout.addWidget(info_label)
    
    window.show()
    
    print("Timeline widget created successfully")
    print(f"Focus Ring visible: {timeline.focus_ring.isVisible()}")
    print(f"Timeline visible: {timeline.timeline.isVisible()}")
    
    sys.exit(app.exec())
