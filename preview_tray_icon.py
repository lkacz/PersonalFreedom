from PySide6 import QtGui, QtCore, QtWidgets
import sys
from pathlib import Path

# Initialize application for font rendering
if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance()

def create_preview_icon(minutes: int, size: int = 128):
    """Generate a preview of the tray icon with minutes."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

    # Base colors (Blocking Blue)
    painter.setBrush(QtGui.QColor("#0EA5E9"))
    painter.setPen(QtGui.QPen(QtGui.QColor("#0369A1"), size // 32))
    
    # Draw circle
    margin = size // 32
    painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)

    # Draw Text
    painter.setPen(QtGui.QColor("white"))
    
    # Font scaling logic matching app (base 64 -> 128 scaling x2)
    scale_factor = size / 64
    if minutes >= 100:
        font_size = int(18 * scale_factor)
    elif minutes >= 10:
        font_size = int(24 * scale_factor)
    else:
        font_size = int(28 * scale_factor)
    
    font = QtGui.QFont("Arial", font_size, QtGui.QFont.Bold)
    painter.setFont(font)
    
    rect = QtCore.QRect(0, 0, size, size)
    painter.drawText(rect, QtCore.Qt.AlignCenter, str(minutes))

    painter.end()
    return pixmap

def main():
    output_dir = Path("preview_icons")
    output_dir.mkdir(exist_ok=True)
    
    # Generate previews for common times
    examples = [120, 60, 45, 15, 5, 2]
    
    print(f"Generating preview icons in {output_dir.absolute()}...")
    
    for mins in examples:
        pixmap = create_preview_icon(mins)
        filename = output_dir / f"preview_{mins}min.png"
        pixmap.save(str(filename))
        print(f"  ✓ {filename.name}")

if __name__ == "__main__":
    main()
