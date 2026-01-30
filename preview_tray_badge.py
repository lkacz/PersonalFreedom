from PySide6 import QtGui, QtCore, QtWidgets
import sys
from pathlib import Path

# Initialize application for font rendering if not already running
if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance()

def create_badge_preview(minutes: int, size: int = 128):
    """Generate a preview of the tray icon with minutes badge in top-right."""
    # Create base blocking icon (simulated)
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    
    # Base Icon (Blue Circle + Sword)
    painter.setBrush(QtGui.QColor("#0EA5E9"))
    painter.setPen(QtGui.QPen(QtGui.QColor("#0369A1"), size // 32))
    margin = size // 16
    painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)
    
    # (Simulating base icon content)
    painter.setBrush(QtGui.QColor("white"))
    painter.setPen(QtCore.Qt.NoPen)
    painter.drawRect(size//2 - 5, size//2, 10, size//4)
    
    # ---------------------------------------------------------
    # Badge Logic (same as app)
    # ---------------------------------------------------------
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

    text = str(minutes)
    if len(text) > 2:
        badge_size = int(size * 0.55)
    elif len(text) > 1:
        badge_size = int(size * 0.45)
    else:
        badge_size = int(size * 0.4)
        
    badge_x = size - badge_size
    badge_y = 0
    
    # Draw badge background (Red circle)
    painter.setBrush(QtGui.QColor("#EF4444"))  # Red-500
    painter.setPen(QtGui.QPen(QtGui.QColor("white"), size // 32))
    painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)
    
    # Draw minutes text
    painter.setPen(QtGui.QColor("white"))
    
    font_size = int(badge_size * 0.65)
    font = QtGui.QFont("Arial", font_size, QtGui.QFont.Bold)
    painter.setFont(font)
    
    rect = QtCore.QRect(badge_x, badge_y, badge_size, badge_size)
    painter.drawText(rect, QtCore.Qt.AlignCenter, text)

    painter.end()
    return pixmap

def main():
    output_dir = Path("preview_icons")
    output_dir.mkdir(exist_ok=True)
    
    examples = [120, 99, 45, 10, 5, 1]
    
    print(f"Generating badge preview icons in {output_dir.absolute()}...")
    
    for mins in examples:
        pixmap = create_badge_preview(mins)
        filename = output_dir / f"badge_preview_{mins}min.png"
        pixmap.save(str(filename))
        print(f"  ✓ {filename.name}")

if __name__ == "__main__":
    main()
