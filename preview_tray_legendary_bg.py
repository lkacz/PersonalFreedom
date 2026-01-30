from PySide6 import QtGui, QtCore, QtWidgets
import sys
from pathlib import Path

# Initialize application for font rendering if not already running
if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance()

def create_legendary_with_bg(minutes: int, size: int = 128):
    """Generate a preview of the legendary style tray icon with rare blue gradient."""
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.TextAntialiasing)

    # Scale margin from base 64px
    margin = int(size * (4/64))
    
    # Draw Rare Blue Gradient Background Circle
    center_x = size // 2
    center_y = size // 2
    radius = (size - 2 * margin) // 2
    
    gradient = QtGui.QRadialGradient(center_x, center_y, radius)
    gradient.setColorAt(0, QtGui.QColor("#2196f3"))  # Rare blue (center)
    gradient.setColorAt(1, QtGui.QColor("#1565c0"))  # Darker blue (edge)
    
    painter.setBrush(gradient)
    painter.setPen(QtCore.Qt.NoPen)
    painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)

    # Draw Legendary Orange Circle Outline
    stroke_width = int(size * (4/64))
    legendary_color = QtGui.QColor("#FF9800")
    
    painter.setPen(QtGui.QPen(legendary_color, stroke_width))
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawEllipse(margin, margin, size - 2*margin, size - 2*margin)

    # Draw Number
    painter.setPen(QtGui.QColor("white"))
    
    # Scaling logic for font size (matching app logic scaled to size)
    text = str(minutes)
    
    # Base sizes for 64px
    if len(text) >= 3:
        base_font_size = 20
    elif len(text) == 2:
        base_font_size = 26
    else:
        base_font_size = 32
        
    font_size = int(base_font_size * (size / 64))
    
    font = QtGui.QFont("Arial", font_size, QtGui.QFont.Bold)
    painter.setFont(font)
    
    rect = QtCore.QRect(0, 0, size, size)
    painter.drawText(rect, QtCore.Qt.AlignCenter, text)

    painter.end()
    return pixmap

def main():
    output_dir = Path("preview_icons")
    output_dir.mkdir(exist_ok=True)
    
    examples = [120, 99, 45, 10, 5, 1]
    
    print(f"Generating legendary preview icons with blue gradient in {output_dir.absolute()}...")
    
    for mins in examples:
        pixmap = create_legendary_with_bg(mins)
        filename = output_dir / f"legendary_blue_preview_{mins}min.png"
        pixmap.save(str(filename))
        print(f"  ✓ {filename.name}")

if __name__ == "__main__":
    main()
