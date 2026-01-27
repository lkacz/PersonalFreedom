"""Quick test script to preview the legendary sound."""
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

def main():
    app = QApplication(sys.argv)
    
    print("🎺 Playing LEGENDARY fanfare...")
    
    from lottery_sounds import play_legendary_sound
    success = play_legendary_sound()
    
    if success:
        print("✨ Sound played successfully!")
    else:
        print("❌ Failed to play sound")
    
    # Keep the app running for 8 seconds to let the full sound finish
    QTimer.singleShot(8000, app.quit)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
